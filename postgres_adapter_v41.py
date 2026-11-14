"""Experimental server-side PostgreSQL compatibility adapter for RADAR v0.41.

Private radar schema only; never use this with real patient data or production.
The backend continues to enforce existing centre authorization. This adapter is
not a substitute for migration parity, row-level policies or a verified deployment.
"""
from __future__ import annotations
import datetime
import json
import os
import re
from contextlib import contextmanager
from urllib.parse import urlsplit, unquote, parse_qs

JSON_FIELDS = frozenset({'payload', 'value_json'})
AUTO_ID_TABLES = frozenset({'users', 'invitations', 'audit', 'audit_field_changes'})

class CompatRow(dict):
    """Match sqlite3.Row name/index lookup and preserve JSON string decoding."""
    def __init__(self, mapping):
        out = {}
        for k, v in mapping.items():
            if k in JSON_FIELDS and not isinstance(v, (str, type(None))):
                v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
            if isinstance(v, (datetime.datetime, datetime.date)):
                v = v.isoformat()
            if isinstance(v, bool):
                v = int(v)
            out[k] = v
        super().__init__(out)
        self._pos = tuple(out.values())
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._pos[key]
        return super().__getitem__(key)


def translate_sql(statement: str) -> tuple[str, bool]:
    """Translate this application's controlled SQLite SQL, not arbitrary user SQL."""
    query = statement.strip()
    if query.upper() == 'BEGIN':
        return 'SELECT 1', False
    if re.search(r'\bPRAGMA\b|\bATTACH\b|\bDETACH\b|\bEXECUTESCRIPT\b', query, re.I):
        raise ValueError('No se admite SQL específico de SQLite en PostgreSQL')
    if re.search(r'\bORDER\s+BY\s+rowid\b', query, re.I):
        query = re.sub(r'\bORDER\s+BY\s+rowid\b', 'ORDER BY id', query, flags=re.I)
    # The only json_extract expression in the v0.40 backend is the status metric.
    query = re.sub(r"json_extract\(payload,\s*'\$\.status'\)", "(payload->>'status')", query, flags=re.I)
    # Bind markers are authored SQL in the server; do not translate quoted literal '?'.
    in_string = False
    result = []
    idx = 0
    while idx < len(query):
        c = query[idx]
        if c == "'":
            if in_string and idx + 1 < len(query) and query[idx + 1] == "'":
                result.extend(["'", "'"])
                idx += 2
                continue
            in_string = not in_string
            result.append(c)
        elif c == '?' and not in_string:
            result.append('%s')
        else:
            result.append(c)
        idx += 1
    query = ''.join(result)
    # sqlite stores INTEGER active flags; the migration maps this to a boolean.
    query = re.sub(r'\bWHERE\s+0\b', 'WHERE FALSE', query, flags=re.I)
    query = re.sub(r'\bactive\s*=\s*1\b', 'active = TRUE', query, flags=re.I)
    query = re.sub(r'\bactive\s*=\s*0\b', 'active = FALSE', query, flags=re.I)
    query = re.sub(r'\bactive\s*=\s*%s', 'active = %s', query, flags=re.I)
    query = re.sub(r'(VALUES\s*\(\s*%s\s*,\s*%s\s*,\s*%s\s*,\s*%s\s*,\s*)1(\s*\))', r'\g<1>TRUE\2', query, flags=re.I)
    m = re.match(r'^INSERT\s+INTO\s+(users|invitations|audit|audit_field_changes)\b', query, re.I)
    needs_id = bool(m and not re.search(r'\bRETURNING\b', query, re.I))
    if needs_id:
        query += ' RETURNING id'
    return query, needs_id


class PgCursor:
    def __init__(self, cursor, lastrowid=None):
        self._cursor=cursor
        self.lastrowid=lastrowid
    def fetchone(self):
        row=self._cursor.fetchone()
        return CompatRow(row) if row is not None else None
    def fetchall(self):
        return [CompatRow(r) for r in self._cursor.fetchall()]
    def __iter__(self):
        for r in self._cursor:
            yield CompatRow(r)
    @property
    def rowcount(self):
        return self._cursor.rowcount


class PgConn:
    def __init__(self, connection):
        self._conn=connection
    def execute(self, sql, params=()):
        statement, return_id = translate_sql(sql)
        if re.match(r'^UPDATE\s+users\s+SET\s+active\s*=\s*%s', statement, re.I):
            params = (bool(params[0]), *params[1:])
        cur=self._conn.execute(statement, params)
        last_id=cur.fetchone()['id'] if return_id else None
        return PgCursor(cur, last_id)
    def executemany(self, sql, batch):
        statement, returning = translate_sql(sql)
        if returning:
            # Audit-field inserts have identity IDs but the caller does not use
            # them. Keep each insert in the caller's enclosing transaction.
            for params in batch:
                self.execute(sql, params)
        else:
            with self._conn.cursor() as cur:
                cur.executemany(statement, batch)
        return self


def validate_database_target(url: str, expected_ref: str) -> str:
    """Reject wrong Supabase project, plaintext DB links, or URL credentials in logs.

    Validation is deliberately limited to the Supabase connection patterns used
    by RADAR staging. The secret URL is never included in raised exceptions.
    """
    if not re.fullmatch(r'[a-z]{20}', expected_ref):
        raise RuntimeError('Configure RADAR_EXPECTED_PROJECT_REF explícitamente')
    try:
        u = urlsplit(url)
        host = (u.hostname or '').lower()
        username = unquote(u.username or '')
        query = parse_qs(u.query, strict_parsing=False)
        port = u.port
    except (ValueError, TypeError) as exc:
        raise RuntimeError('URL de PostgreSQL inválida') from exc
    if (u.scheme not in ('postgresql', 'postgres') or not u.password
        or u.path != '/postgres' or u.fragment or not port):
        raise RuntimeError('Conexión PostgreSQL incompleta o inválida')
    direct = (host == f'db.{expected_ref}.supabase.co' and username == 'postgres')
    pooled = (host.endswith('.pooler.supabase.com')
              and username == f'postgres.{expected_ref}')
    if not (direct or pooled) or port not in (5432, 6543):
        raise RuntimeError('La conexión no corresponde al proyecto RADAR esperado')
    if query.get('sslmode') != ['verify-full']:
        raise RuntimeError('RADAR requiere sslmode=verify-full y CA de confianza para PostgreSQL')
    return 'direct' if direct else 'pooler'


@contextmanager
def connect_postgres():
    """One transaction per request, connection kept exclusively on the backend."""
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as e:
        raise RuntimeError('Instale psycopg[binary] en el backend para activar PostgreSQL') from e
    url=os.environ.get('RADAR_DATABASE_URL','').strip()
    if os.getenv('RADAR_MODE') != 'synthetic_staging':
        raise RuntimeError('PostgreSQL sólo se habilita en modo synthetic_staging')
    validate_database_target(url, os.environ.get('RADAR_EXPECTED_PROJECT_REF', '').strip())
    if os.getenv('RADAR_SEED_DEMO') == '1':
        raise RuntimeError('No se permite RADAR_SEED_DEMO con PostgreSQL remoto')
    # Pin the downloaded Supabase root CA explicitly for strict TLS verification.
    # This is public verification material installed at Docker build time.
    trusted_ca='/usr/local/share/ca-certificates/supabase-root-2021.crt'
    if not os.path.isfile(trusted_ca):
        raise RuntimeError('Falta el certificado raíz público de Supabase')
    with psycopg.connect(url, sslrootcert=trusted_ca, row_factory=dict_row, connect_timeout=10) as native:
        # Search_path is fixed, never supplied by a browser or other request.
        with native.transaction():
            native.execute('SET LOCAL search_path TO radar, pg_catalog')
            # Shared storage makes serial read/check/update sequences safe to
            # execute concurrently across distinct backend replicas. Serialize
            # writers for this first staging migration; remove after atomic
            # revision/episode-number tests have been completed.
            native.execute('SELECT pg_advisory_xact_lock(40041, 1)')
            yield PgConn(native)


def postgres_initialise(existing_conn_factory):
    """Bootstrap only; all schema DDL is applied through versioned migrations."""
    from argon2 import PasswordHasher
    from operational_v40 import validate_bootstrap_password
    username=os.environ.get('RADAR_BOOTSTRAP_ADMIN_USER','radar.admin').strip()
    password=os.environ.get('RADAR_BOOTSTRAP_ADMIN_PASSWORD','')
    # Do not require plaintext bootstrap password when the account exists.
    with existing_conn_factory() as c:
        row=c.execute('SELECT count(*) AS n FROM users').fetchone()
        if row['n']:
            return
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,64}', username):
            raise RuntimeError('Cuenta administradora inicial inválida')
        validate_bootstrap_password(password)
        c.execute('INSERT INTO users(username,pw_hash,role,centre,active) VALUES (?,?,?,?,1)',
                  (username,PasswordHasher().hash(password),'admin',None))


def postgres_ready(connection_factory):
    with connection_factory() as c:
        c.execute('SELECT 1').fetchone()
        count=c.execute('SELECT count(*) n FROM users').fetchone()['n']
    return count > 0
