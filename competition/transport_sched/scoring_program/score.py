#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def detect_dirs():
    argv = sys.argv[1:]
    input_arg = argv[0] if len(argv) >= 1 else None
    output_arg = argv[1] if len(argv) >= 2 else None
    input_dir = (
        input_arg
        or os.environ.get('INPUT_DIR')
        or '/app/input'
    )
    output_dir = (
        output_arg
        or os.environ.get('OUTPUT_DIR')
        or '/app/output'
    )
    pred_dir = (
        os.environ.get('PREDICTIONS_DIR')
        or None
    )
    return Path(input_dir), Path(output_dir), (Path(pred_dir) if pred_dir else None)


def find_cases(input_root: Path) -> list[Path]:
    if (input_root / 'ref' / 'cases').is_dir():
        root = input_root / 'ref' / 'cases'
    elif (input_root / 'cases').is_dir():
        root = input_root / 'cases'
    else:
        root = input_root
    out = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and (p / 'job.json').exists() and (p / 'machine.json').exists():
            out.append(p)
    return out


def load_constraints(case_dir: Path) -> dict:
    path = case_dir / 'constraints.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'windows': []}


def load_machine_new(case_dir: Path) -> dict:
    with open(case_dir / 'machine.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_job_new(case_dir: Path) -> dict:
    with open(case_dir / 'job.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_am_new(case_dir: Path) -> dict:
    p = case_dir / 'am.json'
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


pass


def load_predictions(output_root: Path) -> dict[str, dict]:
    idx = output_root / 'predictions_index.json'
    if idx.exists():
        with open(idx, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        out = {}
        for cid, info in meta.get('predictions', {}).items():
            path = output_root / info['path']
            with open(path, 'r', encoding='utf-8') as f:
                out[cid] = json.load(f)
        return out
    agg = output_root / 'predictions.json'
    if agg.exists():
        with open(agg, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {c.get('case_id'): c for c in data.get('cases', [])}
    # fallback: scan predictions directory
    pred_root = output_root / 'predictions'
    out = {}
    if pred_root.is_dir():
        for case_dir in pred_root.iterdir():
            p = case_dir / 'schedule.json'
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                out[data.get('case_id', case_dir.name)] = data
    return out


# ===== 新协议解析与校验 =====

ACTION_STAY = 'Stay'
ACTION_PLACE = 'Place'
ACTION_PICK = 'Pick'
ACTION_EXECUTE = 'Execute'
ACTION_VENT = 'Vent'
ACTION_PUMP = 'Pump'

def _events_by_resource(schedule: dict) -> dict[str, list[dict]]:
    return {res: list(evts) for res, evts in schedule.items() if isinstance(evts, list)}

def _end_time(evt: dict) -> float:
    return float(evt.get('StartTime', 0)) + float(evt.get('Duration', 0))

def _wafer_label(lot_id: int, wafer_id: int) -> str:
    return f"W{lot_id}-{wafer_id}"

def validate_and_score_case_new(case_id: str, machine: dict, job: dict, am: dict, pred_schedule: dict) -> dict:
    messages = []
    ok = True

    # 资源互斥：同一资源事件不重叠
    for res, evts in _events_by_resource(pred_schedule).items():
        last_end = -1e18
        for e in sorted(evts, key=lambda x: (float(x.get('StartTime', 0)), _end_time(x))):
            s = float(e.get('StartTime', 0))
            d = float(e.get('Duration', 0))
            if d < 0:
                ok = False
                messages.append(f'{res} 存在负时长事件')
                continue
            if s < last_end - 1e-9:
                ok = False
                messages.append(f'{res} 时间片重叠 at {s}')
            last_end = max(last_end, s + d)

    # 时长与机台定义一致性（抽样校验）：
    # EFEM AtmRobot: Pick/Place；TMx VacRobot: Pick/Place；LLx: Vent/Pump；PMx: Execute >= 最小时长
    def dur_eq(x: float, y: float) -> bool:
        return abs(float(x) - float(y)) <= 1e-9

    # AtmRobot 校验
    efem = machine.get('EFEM', {})
    atm = efem.get('AtmRobot', {})
    for res, evts in _events_by_resource(pred_schedule).items():
        if res.startswith('AtmRobot'):
            for e in evts:
                act = e.get('Action')
                dur = float(e.get('Duration', 0))
                if act == ACTION_PICK and not dur_eq(dur, atm.get('pick', 0)):
                    ok = False; messages.append(f'{res} Pick 时长不匹配')
                if act == ACTION_PLACE and not dur_eq(dur, atm.get('place', 0)):
                    ok = False; messages.append(f'{res} Place 时长不匹配')

    # VacRobot 校验
    for tm_key in [k for k in machine.keys() if k.startswith('TM')]:
        vcfg = machine[tm_key].get('VacRobot', {})
        for res, evts in _events_by_resource(pred_schedule).items():
            if res.startswith(f'{tm_key}-VacRobot'):
                for e in evts:
                    act = e.get('Action'); dur = float(e.get('Duration', 0))
                    if act == ACTION_PICK and not dur_eq(dur, vcfg.get('pick', 0)):
                        ok = False; messages.append(f'{res} Pick 时长不匹配')
                    if act == ACTION_PLACE and not dur_eq(dur, vcfg.get('place', 0)):
                        ok = False; messages.append(f'{res} Place 时长不匹配')

    # LoadLock 校验
    for ll_key in [k for k in machine.keys() if k.startswith('LoadLock')]:
        llcfg = machine[ll_key]
        for res, evts in _events_by_resource(pred_schedule).items():
            if res.startswith(ll_key):
                for e in evts:
                    act = e.get('Action'); dur = float(e.get('Duration', 0))
                    if act == ACTION_VENT and not dur_eq(dur, llcfg.get('vent', 0)):
                        ok = False; messages.append(f'{res} Vent 时长不匹配')
                    if act == ACTION_PUMP and not dur_eq(dur, llcfg.get('pump', 0)):
                        ok = False; messages.append(f'{res} Pump 时长不匹配')

    # PM Execute 最小时长与路径一致性
    # 构建每片 wafer 的目标最小时长（按 Sequence）与允许的 PM 集合
    seqs = job.get('Lot', [])
    wafer_completion: dict[str, float] = {}
    for lot in seqs:
        lot_id = int(lot.get('Id'))
        start_time = float(lot.get('StartTime', 0))
        wafers = list(lot.get('Wafer', []))
        # 找到包含 PM 的步骤（数组，允许并行选择）与最后步骤，作为完成判断依据
        pm_steps = [step for step in lot.get('Sequence', []) if isinstance(step, list) and any(isinstance(x, dict) and list(x.keys())[0].startswith('PM') for x in step)]
        last_pm = pm_steps[-1] if pm_steps else []
        allowed_pm = set(k for d in last_pm for k in (d.keys() if isinstance(d, dict) else []))
        min_proc = {k: float(list(d.values())[0]) for d in last_pm if isinstance(d, dict) for k in d.keys()}

        for w in wafers:
            label = _wafer_label(lot_id, int(w))
            # 在所有 PM 资源中查找该 Wafer 的最后一次 Execute 结束时间
            last_end = -1e18
            pm_execute_ok = False
            for res, evts in _events_by_resource(pred_schedule).items():
                if res.startswith('PM'):
                    for e in evts:
                        if e.get('Wafer') == label and e.get('Action') == ACTION_EXECUTE:
                            endt = _end_time(e)
                            last_end = max(last_end, endt)
                            # 最小时长校验（若该 PM 在允许集合中）
                            if res in allowed_pm:
                                if float(e.get('Duration', 0)) + 1e-9 >= float(min_proc.get(res, 0)):
                                    pm_execute_ok = True
            if last_end < -1e17:
                ok = False; messages.append(f'缺少 Wafer 完成事件: {label}')
                continue
            if allowed_pm and not pm_execute_ok:
                ok = False; messages.append(f'Wafer 完成事件未满足最小时长或路径: {label}')
            wafer_completion[label] = last_end

        # 串行 Mode：同 Lot 首次进入时间按 Wafer ID 递增
        if job.get('Mode') == 'Serial':
            enter_times = []
            for w in wafers:
                label = _wafer_label(lot_id, int(w))
                et = 1e99
                for res, evts in _events_by_resource(pred_schedule).items():
                    for e in evts:
                        if e.get('Wafer') == label:
                            et = min(et, float(e.get('StartTime', 0)))
                enter_times.append((int(w), et))
            last_t = -1e18
            for wid, t in sorted(enter_times, key=lambda x: x[0]):
                if t < last_t - 1e-9:
                    ok = False; messages.append(f'串行模式下后片超车: Lot {lot_id} Wafer {wid}')
                last_t = max(last_t, t)

    # 指标计算
    # Total Flow Time：sum(end - lot.StartTime)
    tft = 0.0
    w2w_vals = []
    for lot in seqs:
        lot_id = int(lot.get('Id'))
        start_time = float(lot.get('StartTime', 0))
        wafers = list(lot.get('Wafer', []))
        finishes = []
        for w in wafers:
            label = _wafer_label(lot_id, int(w))
            ft = wafer_completion.get(label, start_time)
            tft += max(0.0, ft - start_time)
            finishes.append(max(0.0, ft - start_time))
        # 标准差
        if finishes:
            avg = sum(finishes) / len(finishes)
            var = sum((x - avg) ** 2 for x in finishes) / len(finishes)
            std = var ** 0.5
            # 以 Wafer 数量加权
            w2w_vals.append((len(finishes), std))
    w2w_consistency = (sum(w * s for w, s in w2w_vals) / max(1, sum(w for w, _ in w2w_vals))) if w2w_vals else 0.0
    alpha = float(os.environ.get('WEIGHT_ALPHA', '0.6'))
    weighted_score = alpha * tft + (1 - alpha) * w2w_consistency

    return {
        'case_id': case_id,
        'valid': ok,
        'messages': messages,
        'total_flow_time': tft,
        'w2w_consistency': w2w_consistency,
        'weighted_score': weighted_score,
    }


def collect_machine_ids(machines_json: dict) -> set[str]:
    ids = set()
    for m in machines_json.get('machines', []):
        mid = m.get('machine_id') or m.get('id')
        if mid:
            ids.add(mid)
    return ids


def build_op_time_map(jobs_json: dict) -> dict[tuple[str, str], float]:
    mp = {}
    for job in jobs_json.get('jobs', []):
        jid = job.get('job_id') or job.get('id')
        for op in job.get('operations', []):
            oid = op.get('op_id') or op.get('id')
            mp[(jid, oid)] = float(op.get('processing_time', 0))
    return mp


pass


def render_html(summary: dict) -> str:
    rows = []
    for s in summary['cases']:
        msg = '; '.join(s.get('messages', [])) if s.get('messages') else ''
        rows.append(
            f"<tr><td>{s['case_id']}</td><td>{'✅' if s['valid'] else '❌'}</td>"
            f"<td>{s.get('total_flow_time', 0.0):.3f}</td><td>{s.get('w2w_consistency', 0.0):.3f}</td><td>{s.get('weighted_score', 0.0):.3f}</td><td>{msg}</td></tr>"
        )
    html = f"""
<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>Transport Scheduling Detailed Result</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
    th {{ background: #fafafa; }}
  </style>
</head><body>
  <h2>传输调度评测报告</h2>
  <p>总体：Total Flow Time={summary['overall']['total_flow_time']:.3f}，W2W Consistency={summary['overall']['w2w_consistency']:.3f}，Weighted Score={summary['overall']['weighted_score']:.3f}，全部有效={summary['overall']['all_valid']}</p>
  <table>
    <thead>
      <tr><th>Case</th><th>Valid</th><th>Total Flow Time</th><th>W2W Consistency</th><th>Weighted Score</th><th>Messages</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body></html>
"""
    return html


def main():
    input_dir, output_dir, pred_dir_env = detect_dirs()
    eprint(f'INPUT_DIR={input_dir}')
    eprint(f'OUTPUT_DIR={output_dir}')
    eprint(f'PRED_DIR_ENV={pred_dir_env}')
    
    # 调试：打印 /app 下的所有路径和文件
    eprint('=== SCORING PROGRAM: /app 目录结构 ===')
    import os
    for root, dirs, files in os.walk('/app'):
        level = root.replace('/app', '').count(os.sep)
        indent = ' ' * 2 * level
        eprint(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            eprint(f'{subindent}{file}')
    eprint('=== END /app 目录结构 ===')

    # 优先从共享目录读取预测文件
    shared_dir = Path('/app/shared')
    if not shared_dir.exists():
        shared_dir = output_dir  # 本地运行时回退到输出目录
    eprint(f'SHARED_DIR={shared_dir}')

    cases = find_cases(input_dir)
    if not cases:
        raise RuntimeError('未发现用例目录（需要包含 jobs.json）。')

    # 按优先级顺序尝试加载预测文件：1. 共享目录 2. input/res目录 3. 输出目录 4. 环境变量指定目录
    predictions = {}
    if shared_dir.exists():
        eprint('尝试从共享目录加载预测文件...')
        eprint(f'=== 共享目录内容调试 ===')
        eprint(f'共享目录路径: {shared_dir}')
        if shared_dir.is_dir():
            for item in sorted(shared_dir.rglob('*')):
                if item.is_file():
                    eprint(f'  文件: {item.relative_to(shared_dir)}')
                elif item.is_dir():
                    eprint(f'  目录: {item.relative_to(shared_dir)}/')
        eprint(f'=== END 共享目录内容调试 ===')
        predictions = load_predictions(shared_dir)
        eprint(f'从共享目录加载了 {len(predictions)} 个预测文件')
    
    if not predictions:
        # 尝试从 /app/input/res/ 目录加载（Codabench平台标准位置）
        input_res_dir = input_dir / 'res'
        if input_res_dir.exists():
            eprint('共享目录中未找到预测文件，尝试从input/res目录加载...')
            eprint(f'=== input/res目录内容调试 ===')
            eprint(f'input/res目录路径: {input_res_dir}')
            if input_res_dir.is_dir():
                for item in sorted(input_res_dir.rglob('*')):
                    if item.is_file():
                        eprint(f'  文件: {item.relative_to(input_res_dir)}')
                    elif item.is_dir():
                        eprint(f'  目录: {item.relative_to(input_res_dir)}/')
            eprint(f'=== END input/res目录内容调试 ===')
            predictions = load_predictions(input_res_dir)
            eprint(f'从input/res目录加载了 {len(predictions)} 个预测文件')
    
    if not predictions:
        eprint('input/res目录中未找到预测文件，尝试从输出目录加载...')
        predictions = load_predictions(output_dir)
        eprint(f'从输出目录加载了 {len(predictions)} 个预测文件')
    
    if not predictions and pred_dir_env and pred_dir_env.exists():
        eprint('输出目录中未找到预测文件，尝试从环境变量指定目录加载...')
        predictions = load_predictions(pred_dir_env)
        eprint(f'从环境变量目录加载了 {len(predictions)} 个预测文件')

    per_case = []
    for case_dir in cases:
        cid = case_dir.name
        if cid not in predictions:
            per_case.append({
                'case_id': cid,
                'valid': False,
                'messages': ['缺少该用例的 schedule.json'],
                'total_flow_time': 1e12,
                'w2w_consistency': 0.0,
                'weighted_score': 1e12,
            })
            continue
        pred = predictions[cid]
        machine = load_machine_new(case_dir)
        job = load_job_new(case_dir)
        am = load_am_new(case_dir)
        per_case.append(validate_and_score_case_new(cid, machine, job, am, pred))

    # 新指标汇总（避免 Infinity）
    finite_tft = [s.get('total_flow_time', 1e12) for s in per_case if s.get('total_flow_time', 1e12) < 9e11]
    avg_tft = sum(finite_tft) / len(finite_tft) if finite_tft else 1e12
    avg_w2w = sum(s.get('w2w_consistency', 0.0) for s in per_case) / max(1, len(per_case))
    avg_ws = sum(s.get('weighted_score', 0.0) for s in per_case) / max(1, len(per_case))
    summary = {
        'overall': {
            'total_flow_time': avg_tft,
            'w2w_consistency': avg_w2w,
            'weighted_score': avg_ws,
            'all_valid': all(s.get('valid', False) for s in per_case),
            'case_count': len(per_case),
        },
        'cases': per_case,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / 'scores.txt', 'w', encoding='utf-8') as f:
        f.write(f"weighted_score: {avg_ws}\n")
        f.write(f"total_flow_time: {avg_tft}\n")
        f.write(f"w2w_consistency: {avg_w2w}\n")
        f.write(f"all_valid: {int(summary['overall']['all_valid'])}\n")

    with open(output_dir / 'scores.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    html = render_html(summary)
    with open(output_dir / 'detailed_result.html', 'w', encoding='utf-8') as f:
        f.write(html)

    eprint('Scoring 完成。')


if __name__ == '__main__':
    main()
