#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def load_inputs(case_dir: Path):
    with open(case_dir / 'machine.json', 'r', encoding='utf-8') as f:
        machine = json.load(f)
    with open(case_dir / 'job.json', 'r', encoding='utf-8') as f:
        job = json.load(f)
    am = {}
    p = case_dir / 'am.json'
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            am = json.load(f)
    return machine, job, am

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    case_dir = Path(args.input)
    out_file = Path(args.output)

    machine, job, am = load_inputs(case_dir)

    atm_pick = float(machine.get('EFEM', {}).get('AtmRobot', {}).get('pick', 0))
    atm_place = float(machine.get('EFEM', {}).get('AtmRobot', {}).get('place', 0))
    vac_pick = float(machine.get('TM1', {}).get('VacRobot', {}).get('pick', 0))
    vac_place = float(machine.get('TM1', {}).get('VacRobot', {}).get('place', 0))
    ll1_pump = float(machine.get('LoadLock1', {}).get('pump', 0))
    ll1_vent = float(machine.get('LoadLock1', {}).get('vent', 0))

    schedule = {
        'AtmRobot-1': [],
        'LoadLock1-1': [],
        'TM1-VacRobot-1': [],
        'PM1': [],
        'LoadLock2-1': [],
    }
    avail = {k: 0.0 for k in schedule.keys()}

    for lot in job.get('Lot', []):
        start = float(lot.get('StartTime', 0))
        lot_id = int(lot.get('Id'))
        wafers = list(lot.get('Wafer', []))
        pm_steps = [step for step in lot.get('Sequence', []) if isinstance(step, list) and any(isinstance(x, dict) and list(x.keys())[0].startswith('PM') for x in step)]
        min_proc = 180.0
        if pm_steps:
            first_pm = pm_steps[0]
            for d in first_pm:
                if isinstance(d, dict) and 'PM1' in d:
                    min_proc = float(d['PM1'])
                    break
        t = start
        for w in wafers:
            label = f"W{lot_id}-{int(w)}"
            s1 = max(t, avail['AtmRobot-1'])
            schedule['AtmRobot-1'].append({'Wafer': label, 'StartTime': s1, 'Action': 'Pick', 'Duration': atm_pick})
            schedule['AtmRobot-1'].append({'Wafer': label, 'StartTime': s1 + atm_pick, 'Action': 'Place', 'Duration': atm_place})
            end1 = s1 + atm_pick + atm_place
            avail['AtmRobot-1'] = end1

            s2 = max(end1, avail['LoadLock1-1'])
            schedule['LoadLock1-1'].append({'StartTime': s2, 'Action': 'Vent', 'Duration': ll1_vent})
            end2 = s2 + ll1_vent
            avail['LoadLock1-1'] = end2

            s3 = max(end2, avail['TM1-VacRobot-1'])
            schedule['TM1-VacRobot-1'].append({'Wafer': label, 'StartTime': s3, 'Action': 'Pick', 'Duration': vac_pick})
            schedule['TM1-VacRobot-1'].append({'Wafer': label, 'StartTime': s3 + vac_pick, 'Action': 'Place', 'Duration': vac_place})
            end3 = s3 + vac_pick + vac_place
            avail['TM1-VacRobot-1'] = end3

            s4 = max(end3, avail['PM1'])
            schedule['PM1'].append({'Wafer': label, 'StartTime': s4, 'Action': 'Execute', 'Duration': min_proc})
            end4 = s4 + min_proc
            avail['PM1'] = end4

            s5 = max(end4, avail['LoadLock2-1'])
            schedule['LoadLock2-1'].append({'Wafer': label, 'StartTime': s5, 'Action': 'Place', 'Duration': atm_place})
            end5 = s5 + atm_place
            avail['LoadLock2-1'] = end5

            t = end5 + 10.0

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
