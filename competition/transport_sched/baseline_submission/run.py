#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def load_jobs(case_dir: Path) -> dict:
    jobs_file = case_dir / 'jobs.json'
    eprint(f"[DEBUG] 尝试加载 jobs.json: {jobs_file}")
    if not jobs_file.exists():
        raise FileNotFoundError(f"jobs.json 文件不存在: {jobs_file}")
    with open(jobs_file, 'r', encoding='utf-8') as f:
        return json.load(f)


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

        jobs = load_jobs(case_dir)
        eprint(f"[DEBUG] 成功加载 jobs.json，包含 {len(jobs.get('jobs', []))} 个作业")
        
        t = 0.0
        timeline = []
        for job in jobs.get('jobs', []):
            jid = job.get('job_id')
            for op in job.get('operations', []):
                dur = float(op.get('processing_time', 0))
                timeline.append({
                    'type': 'task', 'job_id': jid, 'op_id': op.get('op_id'), 'start': t, 'end': t + dur
                })
                t += dur

        result = {
            'case_id': case_id,
            'machines': [
                {'machine_id': 'V1', 'timeline': timeline}
            ]
        }
        
        eprint(f"[DEBUG] 生成的调度包含 {len(timeline)} 个任务")
        eprint(f"[DEBUG] 创建输出目录: {out_file.parent}")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        eprint(f"[DEBUG] 写入输出文件: {out_file}")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        eprint(f"[DEBUG] 成功完成，输出文件大小: {out_file.stat().st_size} 字节")
        
    except Exception as e:
        eprint(f"[ERROR] 基线提交程序失败: {type(e).__name__}: {e}")
        import traceback
        eprint(f"[ERROR] 详细错误信息:")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()