#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def load_new_inputs(case_dir: Path) -> tuple[dict, dict, dict]:
    mfile = case_dir / 'machine.json'
    jfile = case_dir / 'job.json'
    afile = case_dir / 'am.json'
    eprint(f"[DEBUG] 加载 machine.json: {mfile}")
    eprint(f"[DEBUG] 加载 job.json: {jfile}")
    if not mfile.exists() or not jfile.exists():
        raise FileNotFoundError("缺少 machine.json 或 job.json")
    with open(mfile, 'r', encoding='utf-8') as f:
        machine = json.load(f)
    with open(jfile, 'r', encoding='utf-8') as f:
        job = json.load(f)
    am = {}
    if afile.exists():
        with open(afile, 'r', encoding='utf-8') as f:
            am = json.load(f)
    return machine, job, am


def main():
    try:
        eprint(f"[DEBUG] 基线提交程序启动")
        eprint(f"[DEBUG] 命令行参数: {sys.argv}")
        
        ap = argparse.ArgumentParser()
        ap.add_argument('--input', required=True)
        ap.add_argument('--output', required=True)
        args = ap.parse_args()

        case_dir = Path(args.input)
        out_file = Path(args.output)
        case_id = case_dir.name

        eprint(f"[DEBUG] 输入目录: {case_dir}")
        eprint(f"[DEBUG] 输出文件: {out_file}")
        eprint(f"[DEBUG] 用例ID: {case_id}")
        
        # 检查输入目录是否存在
        if not case_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {case_dir}")
        if not case_dir.is_dir():
            raise NotADirectoryError(f"输入路径不是目录: {case_dir}")
            
        # 列出输入目录内容
        eprint(f"[DEBUG] 输入目录内容: {list(case_dir.iterdir())}")

        machine, job, am = load_new_inputs(case_dir)
        eprint(f"[DEBUG] 成功加载新输入，Lot 数量: {len(job.get('Lot', []))}")

        # 简化基线：每片 Wafer 选择 PM1 执行一次工艺（Execute），并插入必要的搬运与 LL 动作。
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
            # 取最小时长（PM 步）
            pm_steps = [step for step in lot.get('Sequence', []) if isinstance(step, list) and any(isinstance(x, dict) and list(x.keys())[0].startswith('PM') for x in step)]
            min_proc = 180.0
            if pm_steps:
                first_pm = pm_steps[0]
                # 选 PM1 的定义
                for d in first_pm:
                    if isinstance(d, dict) and 'PM1' in d:
                        min_proc = float(d['PM1'])
                        break
            t = start
            for w in wafers:
                label = f"W{lot_id}-{int(w)}"
                # EFEM 取片、放片到 LL1（受 AtmRobot 时间线约束）
                s1 = max(t, avail['AtmRobot-1'])
                schedule['AtmRobot-1'].append({'Wafer': label, 'StartTime': s1, 'Action': 'Pick', 'Duration': atm_pick})
                schedule['AtmRobot-1'].append({'Wafer': label, 'StartTime': s1 + atm_pick, 'Action': 'Place', 'Duration': atm_place})
                end1 = s1 + atm_pick + atm_place
                avail['AtmRobot-1'] = end1

                # LL1 Vent（受 LoadLock1 时间线约束）
                s2 = max(end1, avail['LoadLock1-1'])
                schedule['LoadLock1-1'].append({'StartTime': s2, 'Action': 'Vent', 'Duration': ll1_vent})
                end2 = s2 + ll1_vent
                avail['LoadLock1-1'] = end2

                # 真空侧取放至 PM1（受 TM1-VacRobot 时间线约束）
                s3 = max(end2, avail['TM1-VacRobot-1'])
                schedule['TM1-VacRobot-1'].append({'Wafer': label, 'StartTime': s3, 'Action': 'Pick', 'Duration': vac_pick})
                schedule['TM1-VacRobot-1'].append({'Wafer': label, 'StartTime': s3 + vac_pick, 'Action': 'Place', 'Duration': vac_place})
                end3 = s3 + vac_pick + vac_place
                avail['TM1-VacRobot-1'] = end3

                # PM1 Execute（受 PM1 时间线约束）
                s4 = max(end3, avail['PM1'])
                schedule['PM1'].append({'Wafer': label, 'StartTime': s4, 'Action': 'Execute', 'Duration': min_proc})
                end4 = s4 + min_proc
                avail['PM1'] = end4

                # 送回 LL2（示意：Place 事件，受 LoadLock2 时间线约束）
                s5 = max(end4, avail['LoadLock2-1'])
                schedule['LoadLock2-1'].append({'Wafer': label, 'StartTime': s5, 'Action': 'Place', 'Duration': atm_place})
                end5 = s5 + atm_place
                avail['LoadLock2-1'] = end5

                # 基准时间推进（确保串行模式不超车）
                t = end5 + 10.0

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        
        eprint(f"[DEBUG] 成功完成，输出文件大小: {out_file.stat().st_size} 字节")
        
    except Exception as e:
        eprint(f"[ERROR] 基线提交程序失败: {type(e).__name__}: {e}")
        import traceback
        eprint(f"[ERROR] 详细错误信息:")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
