#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'competition' / 'transport_sched'
DATA = ROOT / 'datasets' / 'public'
OUT = ROOT / 'out' / 'baseline'
BASELINE = ROOT / 'baseline_submission'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 运行摄取
    subprocess.run([
        'python3', str(ROOT / 'ingestion_program' / 'run.py'),
        str(DATA), str(OUT), str(BASELINE)
    ], check=True)
    # 运行评分
    subprocess.run([
        'python3', str(ROOT / 'scoring_program' / 'score.py')
    ], check=True)
    # 校验输出
    sj = OUT / 'scores.json'
    assert sj.exists(), 'scores.json 未生成'
    with open(sj, 'r', encoding='utf-8') as f:
        s = json.load(f)
    ov = s.get('overall', {})
    for k in ('total_flow_time', 'w2w_consistency', 'weighted_score'):
        assert k in ov, f'总体缺少指标 {k}'
    print('OK: 指标与输出校验通过')

if __name__ == '__main__':
    main()
