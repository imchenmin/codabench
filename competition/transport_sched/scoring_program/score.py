#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def detect_dirs():
    input_dir = (
        os.environ.get('INPUT_DIR')
        or os.environ.get('DATA_DIR')
        or os.environ.get('CODABENCH_INPUT_DIR')
        or '/app/input'
    )
    output_dir = (
        os.environ.get('OUTPUT_DIR')
        or os.environ.get('SCORE_DIR')
        or os.environ.get('CODABENCH_OUTPUT_DIR')
        or '/app/output'
    )
    pred_dir = (
        os.environ.get('PREDICTIONS_DIR')
        or os.environ.get('CODABENCH_PREDICTIONS_DIR')
        or None
    )
    return Path(input_dir), Path(output_dir), (Path(pred_dir) if pred_dir else None)


def find_cases(input_root: Path) -> list[Path]:
    # Prefer hidden/reference data under /app/input/ref/cases if present (platform mounts reference here)
    if (input_root / 'ref' / 'cases').is_dir():
        root = input_root / 'ref' / 'cases'
    elif (input_root / 'cases').is_dir():
        root = input_root / 'cases'
    else:
        root = input_root
    return [p for p in sorted(root.iterdir()) if p.is_dir() and (p / 'jobs.json').exists()]


def load_constraints(case_dir: Path) -> dict:
    path = case_dir / 'constraints.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'windows': []}


def load_jobs(case_dir: Path) -> dict:
    with open(case_dir / 'jobs.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def load_machines(case_dir: Path) -> dict:
    with open(case_dir / 'machines.json', 'r', encoding='utf-8') as f:
        return json.load(f)


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


def validate_and_score_case(case_id: str, inputs: dict, pred: dict) -> dict:
    machines_set = collect_machine_ids(inputs['machines'])
    machine_count = max(1, len(machines_set))

    planned_maint = 0.0
    for w in inputs['constraints'].get('windows', []):
        planned_maint += float(w.get('duration', 0)) * float(w.get('machine_count', 1))

    makespan = 0.0
    task_time = 0.0
    maint_time = 0.0
    ok = True
    messages = []

    op_time_map = build_op_time_map(inputs['jobs'])

    # basic schema checks
    if 'machines' not in pred:
        ok = False
        messages.append('缺少 machines 字段')
        return {
            'case_id': case_id,
            'valid': ok,
            'messages': messages,
            'makespan': float('inf'),
            'utilization': 0.0,
            'oee': 0.0,
        }

    for m in pred.get('machines', []):
        mid = m.get('machine_id') or m.get('id')
        if mid and mid not in machines_set:
            ok = False
            messages.append(f'未知机台: {mid}')
        last_end = -1e18
        for seg in sorted(m.get('timeline', []), key=lambda x: (float(x.get('start', 0)), float(x.get('end', 0)))):
            start = float(seg.get('start', 0))
            end = float(seg.get('end', 0))
            if end < start:
                ok = False
                messages.append(f'负时长片段 machine={mid} start={start} end={end}')
                continue
            if start < last_end - 1e-9:
                ok = False
                messages.append(f'同机台时间片重叠 machine={mid} at {start}')
            last_end = max(last_end, end)
            makespan = max(makespan, end)
            if seg.get('type') == 'task':
                jid = seg.get('job_id')
                oid = seg.get('op_id')
                dur = end - start
                task_time += dur
                # optional op time check
                expected = op_time_map.get((jid, oid))
                if expected is not None and abs(dur - float(expected)) > 1e-6:
                    messages.append(f'时长不一致 job={jid} op={oid} got={dur} expect={expected}')
                # constraints window check: task must not overlap forbidden windows
                for w in inputs['constraints'].get('windows', []):
                    ws = float(w.get('start', 0.0))
                    we = ws + float(w.get('duration', 0.0))
                    # overlap if start < we and end > ws
                    if start < we - 1e-12 and end > ws + 1e-12:
                        ok = False
                        messages.append(
                            f'任务与约束窗口重叠 machine={mid} job={jid} op={oid} seg=({start},{end}) window=({ws},{we})'
                        )
            elif seg.get('type') == 'maintenance':
                maint_time += end - start

    denom_util = makespan * machine_count
    utilization = (task_time / denom_util * 100.0) if denom_util > 0 else 0.0
    denom_oee = makespan * machine_count - planned_maint
    oee = (task_time / denom_oee * 100.0) if denom_oee > 1e-12 else 0.0
    utilization = max(0.0, min(100.0, utilization))
    oee = max(0.0, min(100.0, oee))

    return {
        'case_id': case_id,
        'valid': ok,
        'messages': messages,
        'makespan': makespan,
        'utilization': utilization,
        'oee': oee,
        'task_time': task_time,
        'maintenance_time': maint_time,
        'machine_count': machine_count,
    }


def render_html(summary: dict) -> str:
    rows = []
    for s in summary['cases']:
        msg = '; '.join(s.get('messages', [])) if s.get('messages') else ''
        rows.append(
            f"<tr><td>{s['case_id']}</td><td>{'✅' if s['valid'] else '❌'}</td>"
            f"<td>{s['makespan']:.3f}</td><td>{s['utilization']:.2f}%</td><td>{s['oee']:.2f}%</td><td>{msg}</td></tr>"
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
  <h2>传输调度 benchmark 评测报告</h2>
  <p>总体：平均 Makespan={summary['overall']['avg_makespan']:.3f}，平均 Utilization={summary['overall']['avg_utilization']:.2f}%，平均 OEE={summary['overall']['avg_oee']:.2f}%，全部有效={summary['overall']['all_valid']}</p>
  <table>
    <thead>
      <tr><th>Case</th><th>Valid</th><th>Makespan</th><th>Utilization</th><th>OEE</th><th>Messages</th></tr>
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
    eprint(f'SHARED_DIR={shared_dir}')

    cases = find_cases(input_dir)
    if not cases:
        raise RuntimeError('未发现用例目录（需要包含 jobs.json）。')

    # 按优先级顺序尝试加载预测文件：1. 共享目录 2. 输出目录 3. 环境变量指定目录
    predictions = {}
    if shared_dir.exists():
        eprint('尝试从共享目录加载预测文件...')
        predictions = load_predictions(shared_dir)
        eprint(f'从共享目录加载了 {len(predictions)} 个预测文件')
    
    if not predictions:
        eprint('共享目录中未找到预测文件，尝试从输出目录加载...')
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
            # 避免使用无效的 JSON 浮点（Infinity），以免提交分数时失败
            per_case.append({
                'case_id': cid,
                'valid': False,
                'messages': ['缺少该用例的 schedule.json'],
                'makespan': 1e12,
                'utilization': 0.0,
                'oee': 0.0,
            })
            continue
        inputs = {
            'jobs': load_jobs(case_dir),
            'machines': load_machines(case_dir),
            'constraints': load_constraints(case_dir),
        }
        pred = predictions[cid]
        per_case.append(validate_and_score_case(cid, inputs, pred))

    # 计算平均值时避免 Infinity 导致 JSON 提交失败
    finite_makes = [s['makespan'] for s in per_case if s['makespan'] < 9e11]
    avg_makespan = sum(finite_makes) / len(finite_makes) if finite_makes else 1e12
    avg_util = sum(s.get('utilization', 0.0) for s in per_case) / max(1, len(per_case))
    avg_oee = sum(s.get('oee', 0.0) for s in per_case) / max(1, len(per_case))
    summary = {
        'overall': {
            'avg_makespan': avg_makespan,
            'avg_utilization': avg_util,
            'avg_oee': avg_oee,
            'all_valid': all(s.get('valid', False) for s in per_case),
            'case_count': len(per_case),
        },
        'cases': per_case,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / 'scores.txt', 'w', encoding='utf-8') as f:
        f.write(f"avg_makespan: {avg_makespan}\n")
        f.write(f"avg_utilization: {avg_util}\n")
        f.write(f"avg_oee: {avg_oee}\n")
        f.write(f"all_valid: {int(summary['overall']['all_valid'])}\n")

    with open(output_dir / 'scores.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    html = render_html(summary)
    with open(output_dir / 'detailed_result.html', 'w', encoding='utf-8') as f:
        f.write(html)

    eprint('Scoring 完成。')


if __name__ == '__main__':
    main()