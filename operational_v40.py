"""v0.40 operational boundary for a strictly synthetic single-instance pilot.

No clinical production mode is implemented. SQLite synthetic staging is single-node.
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

@dataclass(frozen=True)
class Runtime:
    mode: str
    origin: str | None
    host: str | None
    database: Path

    @property
    def remote(self) -> bool:
        return self.mode == 'synthetic_staging'


def load_runtime(database: Path) -> Runtime:
    mode = os.getenv('RADAR_MODE', 'local_demo').strip()
    if mode not in {'local_demo', 'synthetic_staging'}:
        raise RuntimeError('RADAR_MODE solo admite local_demo o synthetic_staging; no existe un modo clínico de producción')
    if mode == 'local_demo':
        return Runtime(mode, None, None, Path(database))
    raw = os.getenv('RADAR_PUBLIC_ORIGIN', '').strip()
    p = urlsplit(raw)
    if not raw or p.scheme != 'https' or not p.hostname or p.path not in ('', '/') or p.query or p.fragment or p.username or p.password:
        raise RuntimeError('synthetic_staging requiere RADAR_PUBLIC_ORIGIN=https://dominio-sintetico, sin ruta ni credenciales')
    if os.getenv('RADAR_SEED_DEMO') == '1':
        raise RuntimeError('Está prohibido RADAR_SEED_DEMO en synthetic_staging')
    if os.getenv('RADAR_STORAGE', 'sqlite').lower() == 'postgres':
        if not os.getenv('RADAR_DATABASE_URL', '').startswith(('postgres://', 'postgresql://')):
            raise RuntimeError('Se requiere RADAR_DATABASE_URL PostgreSQL para staging')
        return Runtime(mode, raw.rstrip('/'), p.hostname.lower(), Path(database))
    if not os.getenv('RADAR_DB'):
        raise RuntimeError('synthetic_staging requiere RADAR_DB explícita sobre almacenamiento persistente')
    db = Path(database)
    volume = os.getenv('RADAR_PERSISTENT_DATA_DIR', '').strip()
    if not db.is_absolute() or not volume or not Path(volume).is_absolute():
        raise RuntimeError('Se requieren rutas absolutas RADAR_DB y RADAR_PERSISTENT_DATA_DIR')
    if not db.resolve().is_relative_to(Path(volume).resolve()) or db.resolve() == Path(volume).resolve():
        raise RuntimeError('RADAR_DB debe estar dentro del volumen persistente configurado')
    if os.getenv('RADAR_WORKERS', '1').strip() != '1':
        raise RuntimeError('SQLite de simulación requiere exactamente un worker y una instancia')
    return Runtime(mode, raw.rstrip('/'),p.hostname.lower(),db)


def validate_bootstrap_password(password: str) -> None:
    if len(password) < 16 or len(password) > 128 or password.startswith('radar-demo-'):
        raise RuntimeError('Configure RADAR_BOOTSTRAP_ADMIN_PASSWORD única de 16–128 caracteres; no se aceptan contraseñas demo')
    if not (any(c.isupper() for c in password) and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)):
        raise RuntimeError('La contraseña inicial debe contener mayúsculas, minúsculas y números')


@contextmanager
def staging_instance_lock(runtime: Runtime):
    """Same-host POSIX file lock. This is NOT a distributed multi-host lock."""
    if not runtime.remote or os.getenv("RADAR_STORAGE", "sqlite").lower() == "postgres":
        yield
        return
    try:
        import fcntl
    except ImportError as exc:
        raise RuntimeError('synthetic_staging requiere Linux y bloqueo POSIX') from exc
    lock_file = runtime.database.with_suffix(runtime.database.suffix+'.instance.lock')
    lock_file.parent.mkdir(parents=True,exist_ok=True)
    with lock_file.open('a+b') as file:
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Ya hay una instancia de RADAR usando esta base SQLite') from exc
        try:
            yield
        finally:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
