"""Verified, offline backup tools for the synthetic RADAR-CORUÑA SQLite pilot.

A backup includes all tables (including authentication and audit), so treat it as
sensitive; these tools must never be used to imply institutional approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def count_rows(path: Path):
    with sqlite3.connect(f'file:{path.resolve().as_posix()}?mode=ro',uri=True) as connection:
        result=connection.execute('PRAGMA integrity_check').fetchone()[0]
        if result!='ok':raise ValueError(f'Fallo de integridad SQLite: {result}')
        names={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {name:connection.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in ('patients','visits','episodes','contacts','audit','audit_field_changes') if name in names}


def backup(source: Path, directory: Path):
    source=source.resolve();directory=directory.resolve()
    if not source.is_file():raise FileNotFoundError(f'No existe la base: {source}')
    if directory==source.parent:raise ValueError('Usar una carpeta de copias distinta a la carpeta de datos')
    directory.mkdir(parents=True,exist_ok=True)
    if source.stat().st_size==0:raise ValueError('La base está vacía')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=directory/f'RADAR_CORUNA_backup_{stamp}.sqlite3'
    temp=directory/f'.{dest.name}.tmp'
    try:
        with sqlite3.connect(f'file:{source.as_posix()}?mode=ro',uri=True,timeout=15) as src:
            with sqlite3.connect(str(temp),timeout=15) as dst:
                src.backup(dst)
        rows=count_rows(temp)
        temp.replace(dest)
        try:os.chmod(dest,0o600)
        except OSError:pass
        manifest={
           'format':'radar-coruna-synthetic-sqlite-backup-v1',
           'created_at_utc':datetime.now(timezone.utc).isoformat(),
           'filename':dest.name,'sha256':digest(dest),'size_bytes':dest.stat().st_size,
           'tables':rows,'scope':'Synthetic local pilot; NOT authorised for real patient data',
        }
        manifest_path=dest.with_suffix('.json')
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        try:os.chmod(manifest_path,0o600)
        except OSError:pass
        verify(manifest_path)
        return dest,manifest_path
    finally:
        temp.unlink(missing_ok=True)


def verify(manifest_file: Path):
    path=manifest_file.resolve()
    m=json.loads(path.read_text(encoding='utf-8'))
    if m.get('format')!='radar-coruna-synthetic-sqlite-backup-v1':raise ValueError('Manifiesto no reconocido')
    name=m.get('filename','')
    if not name or Path(name).name!=name:raise ValueError('Nombre de copia inválido')
    db=path.parent/name
    if not db.is_file():raise FileNotFoundError(f'Copia inexistente: {db}')
    if digest(db)!=m['sha256'] or db.stat().st_size!=m['size_bytes']:
        raise ValueError('La copia no coincide con el hash SHA-256 del manifiesto')
    rows=count_rows(db)
    if rows!=m['tables']:raise ValueError('La base no coincide con las cantidades del manifiesto')
    return {'verified':True,'path':str(db),'sha256':m['sha256'],'rows':rows}


def restore_new(manifest_file: Path, target: Path):
    """Restore to a NEW database path; never replace an active database."""
    mpath=manifest_file.resolve(); target=target.resolve()
    checked=verify(mpath)
    source=Path(checked['path'])
    if target.exists() or target.with_name(target.name+'-wal').exists() or target.with_name(target.name+'-shm').exists():
        raise FileExistsError('La restauración no puede sobrescribir una base existente o activa')
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_name('.'+target.name+'.restoring')
    try:
        with sqlite3.connect(f'file:{source.as_posix()}?mode=ro',uri=True) as src:
            with sqlite3.connect(str(tmp)) as dst:src.backup(dst)
        if count_rows(tmp)!=checked['rows']:raise ValueError('La restauración no reproduce el contenido esperado')
        if target.exists():raise FileExistsError('Destino creado por otro proceso')
        tmp.rename(target)
        return {'restored_to':str(target),'rows':checked['rows'],'integrity':'ok'}
    finally:
        tmp.unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description='Copias verificables de RADAR-CORUÑA: sólo datos sintéticos')
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('backup');b.add_argument('--db',default=os.environ.get('RADAR_DB',str(Path(__file__).resolve().parent/'radar_synthetic.sqlite3')));b.add_argument('--out',required=True)
    v=sub.add_parser('verify');v.add_argument('manifest')
    r=sub.add_parser('restore-new');r.add_argument('manifest');r.add_argument('--target',required=True)
    args=p.parse_args()
    if args.command=='backup':result={'backup':str(backup(Path(args.db),Path(args.out))[0])}
    elif args.command=='verify':result=verify(Path(args.manifest))
    else:result=restore_new(Path(args.manifest),Path(args.target))
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
