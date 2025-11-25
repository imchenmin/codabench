#!/usr/bin/env python3
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    case_dir = Path(args.input)
    case_id = case_dir.name
    with open(case_dir / 'machines.json', 'r', encoding='utf-8') as f:
        mjson = json.load(f)
    with open(case_dir / 'jobs.json', 'r', encoding='utf-8') as f:
        jjson = json.load(f)
    with open(case_dir / 'constraints.json', 'r', encoding='utf-8') as f:
        cjson = json.load(f)
    out = {"case_id": case_id, "machines": []}
    for m in mjson.get('machines', []):
        mid = m.get('machine_id') or m.get('id')
        if mid:
            out["machines"].append({"machine_id": mid, "timeline": []})
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()