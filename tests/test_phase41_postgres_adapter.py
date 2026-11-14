"""Offline v0.41 PostgreSQL-compatibility checks; do not imply hosted DB parity."""
import datetime
import unittest
from postgres_adapter_v41 import CompatRow, PgConn, translate_sql, validate_database_target

class FakeCursor:
    def __init__(self, rows=None, rowcount=1):
        self.rows = list(rows or [])
        self.rowcount = rowcount
    def fetchone(self): return self.rows.pop(0) if self.rows else None
    def fetchall(self):
        out=self.rows; self.rows=[]; return out
    def __iter__(self): return iter(self.rows)

class FakeNative:
    def __init__(self): self.calls=[]
    def execute(self, statement, params):
        self.calls.append((statement,params))
        return FakeCursor([{'id':41}] if ' RETURNING id' in statement else [{'payload':{'status':'incluido'},'rev':1}])

class PgAdapterTest(unittest.TestCase):
    def test_placeholders(self):
        self.assertEqual(translate_sql('SELECT * FROM patients WHERE id=? AND centre=?')[0], 'SELECT * FROM patients WHERE id=%s AND centre=%s')
    def test_quoted_question_marks_preserved(self):
        sql="SELECT 'a?b' as literal, id FROM users WHERE username=?"
        self.assertIn("'a?b'", translate_sql(sql)[0])
    def test_status_json(self):
        self.assertIn("payload->>'status'",translate_sql("SELECT json_extract(payload,'$.status') FROM patients")[0])
    def test_rowid(self):
        self.assertIn('ORDER BY id',translate_sql('SELECT * FROM episodes ORDER BY rowid')[0])
    def test_where_zero(self):
        self.assertIn('WHERE FALSE',translate_sql('SELECT * FROM visits WHERE 0')[0])
    def test_no_sqlite_pragmas(self):
        with self.assertRaises(ValueError): translate_sql('PRAGMA quick_check')
    def test_users_identity(self):
        q,yes=translate_sql('INSERT INTO users(username,pw_hash,role,centre,active) VALUES (?,?,?,?,1)')
        self.assertTrue(yes);self.assertIn('TRUE',q);self.assertTrue(q.endswith('RETURNING id'))
    def test_audit_identity(self):
        self.assertTrue(translate_sql('INSERT INTO audit(username,role) VALUES (?,?)')[1])
    def test_no_identity_on_regular_table(self):
        self.assertFalse(translate_sql('INSERT INTO patients VALUES (?,?,?,?,?,?)')[1])
    def test_begin(self):
        self.assertEqual(translate_sql('BEGIN')[0], 'SELECT 1')
    def test_row_access(self):
        row=CompatRow({'id':'SIM-001','payload':{'status':'incluido'},'time':datetime.datetime(2026,11,14,tzinfo=datetime.timezone.utc),'active':True})
        self.assertEqual(row[0],'SIM-001')
        self.assertEqual(row['payload'],'{"status":"incluido"}')
        self.assertEqual(row['active'],1)
        self.assertTrue(row['time'].endswith('+00:00'))
    def test_insert_identity_cursor(self):
        native=FakeNative(); c=PgConn(native)
        result=c.execute('INSERT INTO audit(username,role) VALUES (?,?)',('one','admin'))
        self.assertEqual(result.lastrowid,41)
    def test_cast_boolean_activation(self):
        native=FakeNative(); c=PgConn(native)
        c.execute('UPDATE users SET active=? WHERE id=?',(0,2))
        self.assertEqual(native.calls[0][1],(False,2))
    def test_generic_query(self):
        native=FakeNative(); c=PgConn(native)
        row=c.execute('SELECT payload,rev FROM patients WHERE id=?',('SIM-001',)).fetchone()
        self.assertEqual(row['rev'],1)
    def test_legacy_semantics_where_false(self):
        self.assertEqual(translate_sql('SELECT * FROM study_observations WHERE 0')[0], 'SELECT * FROM study_observations WHERE FALSE')

if __name__ == '__main__': unittest.main()

class AuditBatchTest(unittest.TestCase):
    def test_audit_field_batch_can_return_identity(self):
        native=FakeNative(); c=PgConn(native)
        c.executemany('INSERT INTO audit_field_changes(audit_id,field_name,prior_value,new_value) VALUES (?,?,?,?)',[(1,'x',None,'1'),(1,'y',None,'2')])
        self.assertEqual(len(native.calls),2)
        self.assertTrue(all('RETURNING id' in q for q,_ in native.calls))


class RemoteTargetValidationTest(unittest.TestCase):
    REF='vqdpkzlrzwchjumpbqta'
    def test_correct_direct_and_pooler(self):
        self.assertEqual(validate_database_target(f'postgresql://postgres:fake@db.{self.REF}.supabase.co:5432/postgres?sslmode=verify-full',self.REF),'direct')
        self.assertEqual(validate_database_target(f'postgresql://postgres.{self.REF}:fake@aws-0-eu-west-3.pooler.supabase.com:5432/postgres?sslmode=verify-full',self.REF),'pooler')
    def test_refuses_wrong_project_or_user(self):
        with self.assertRaises(RuntimeError):validate_database_target('postgresql://postgres:fake@db.oxlkisjwfarseyqgeyuw.supabase.co:5432/postgres?sslmode=verify-full',self.REF)
        with self.assertRaises(RuntimeError):validate_database_target('postgresql://postgres.otherproject:fake@aws-0-eu-west-3.pooler.supabase.com:5432/postgres?sslmode=verify-full',self.REF)
    def test_requires_verified_tls(self):
        with self.assertRaisesRegex(RuntimeError,'verify-full'):validate_database_target(f'postgresql://postgres:fake@db.{self.REF}.supabase.co:5432/postgres?sslmode=require',self.REF)
        with self.assertRaises(RuntimeError):validate_database_target(f'postgresql://postgres:fake@db.{self.REF}.supabase.co:5432/postgres',self.REF)
    def test_no_secret_leak(self):
        u=f'postgresql://postgres:S3cr3tNeverDisplay@db.{self.REF}.supabase.co:5432/postgres?sslmode=disable'
        try:validate_database_target(u,self.REF)
        except RuntimeError as exc:self.assertNotIn('S3cr3tNeverDisplay',str(exc))
        else:self.fail('Insecure transport accepted')
