"""Scientific Phase 5 demonstrator: read-only audit of an explicitly selected synthetic SQLite file.

Usage (from project root):
  python scripts/phase5_readonly_audit.py --db path/to/uat_synthetic.sqlite3 --out local_uat_result.json
Only SIM- identifiers are accepted. The SQLite source is opened with mode=ro.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scientific_preflight import aggregate


def inspect_db(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f'No existe la base sintética: {path}')
    # Use SQLite URI mode=ro; never initialize or migrate the source.
    uri='file:'+quote(str(path.resolve()),safe='/:')+'?mode=ro'
    with sqlite3.connect(uri,uri=True) as conn:
        conn.row_factory=sqlite3.Row
        persons=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM patients ORDER BY id')]
        visits=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM visits ORDER BY patient,vtype')]
    if any(not str(p.get('id','')).startswith('SIM-') for p in persons):
        raise ValueError('Se detecta un código no sintético. Preflight cancelado.')
    if any(not str(v.get('patient','')).startswith('SIM-') for v in visits):
        raise ValueError('Se detecta un ID de visita no sintético. Preflight cancelado.')
    return aggregate(persons,visits)


def main():
    parser=argparse.ArgumentParser(description='Preflight científico RADAR-CORUÑA sobre una base ficticia')
    parser.add_argument('--db',required=True,type=Path,help='Ruta de SQLite sintético existente')
    parser.add_argument('--out',type=Path,help='Destino opcional JSON; nunca modifica la base')
    args=parser.parse_args()
    report=inspect_db(args.db)
    content=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(content+'\n',encoding='utf-8')
        print(f'Informe creado: {args.out}')
    else:
        print(content)

if __name__=='__main__':
    main()
