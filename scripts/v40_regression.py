"""Bounded four-batch regression; writes results even when a batch times out."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GROUPS={
    'operational_and_recent': ['phase40_operations','phase38_multicentre','phase39_intelligence','phase32_intelligent_capture','phase29_reliability'],
    'clinical_core': ['audit_v07','clinical_review_v10','crd_workflow_v11','export','phase12_scientific_readiness','phase13_outcomes','phase18_reporting','phase20_crd_alignment','phase21_episodes_actions'],
    'historical_workflows': ['phase14_completion','phase15_acceptance','phase16_usability','phase19_release','phase22_episode_care'],
    'concordance_portability': ['phase27_concordance','phase28_journey','phase31_scientific_uat','phase33_workflow_intelligence','pilot','portability_v08','study_v09'],
}

def main():
    parser=argparse.ArgumentParser(description='Execute exactly ONE bounded regression batch.')
    parser.add_argument('--group',required=True,choices=sorted(GROUPS))
    parser.add_argument('--timeout',type=int,default=60)
    args=parser.parse_args()
    files=GROUPS[args.group]
    paths=[f'tests/test_{name}.py' for name in files]
    env={**os.environ,'RADAR_MODE':'local_demo','RADAR_SEED_DEMO':'0'}
    for key in ('RADAR_PUBLIC_ORIGIN','RADAR_BOOTSTRAP_ADMIN_PASSWORD','RADAR_PERSISTENT_DATA_DIR','RADAR_WORKERS'):
        env.pop(key,None)
    started=time.monotonic()
    try:
        run=subprocess.run([sys.executable,'-m','pytest','-q',*paths,'--disable-warnings'],
                           cwd=ROOT,env=env,text=True,timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f'{args.group}: TIMEOUT after {args.timeout}s; NOT a pass',flush=True)
        return 124
    print(f'{args.group}: exit={run.returncode}; elapsed={time.monotonic()-started:.1f}s',flush=True)
    return run.returncode

if __name__=='__main__':raise SystemExit(main())
