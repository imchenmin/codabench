#!/usr/bin/env python3
import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

try:
    import resource  # POSIX only
except Exception:
    resource = None


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def detect_dirs_and_limits(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', nargs='?')
    parser.add_argument('output_dir', nargs='?')
    parser.add_argument('program_dir', nargs='?')
    args, _ = parser.parse_known_args(argv)

    env = os.environ
    input_dir = (
        args.input_dir
        or env.get('INPUT_DIR')
        or env.get('DATA_DIR')
        or env.get('CODABENCH_INPUT_DIR')
        or '/app/input'
    )
    output_dir = (
        args.output_dir
        or env.get('OUTPUT_DIR')
        or env.get('PREDICTIONS_DIR')
        or env.get('CODABENCH_OUTPUT_DIR')
        or '/app/output'
    )
    program_dir = (
        args.program_dir
        or env.get('PROGRAM_DIR')
        or env.get('SUBMISSION_DIR')
        or env.get('CODABENCH_PROGRAM_DIR')
        or '/app/program'
    )
    timeout_sec = float(env.get('TIMEOUT_SECONDS', '300'))
    mem_limit_mb = float(env.get('MEMORY_LIMIT_MB', '2048'))
    return Path(input_dir), Path(output_dir), Path(program_dir), timeout_sec, mem_limit_mb


def find_cases(input_root: Path) -> list[Path]:
    candidates = [
        input_root / 'cases',
        input_root / 'public_data' / 'cases',
        Path('/app/input') / 'ref' / 'cases',
    ]
    root = None
    for cand in candidates:
        if cand.is_dir():
            root = cand
            break
    if root is None:
        return []
    out = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and (p / 'job.json').exists() and (p / 'machine.json').exists():
            out.append(p)
    return out


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def set_memory_limit_bytes(limit_mb: float):
    if resource is None:
        return None
    limit_bytes = int(limit_mb * 1024 * 1024)

    def _preexec():
        try:
            # Address space (best-effort), and data segment
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            resource.setrlimit(resource.RLIMIT_DATA, (limit_bytes, limit_bytes))
        except Exception:
            pass

    return _preexec


def build_command(program_dir: Path, case_dir: Path, out_file: Path):
    if (program_dir / 'run.sh').exists():
        return ['bash', str(program_dir / 'run.sh'), str(case_dir), str(out_file)]
    if (program_dir / 'run.py').exists():
        return [sys.executable, str(program_dir / 'run.py'), '--input', str(case_dir), '--output', str(out_file)]
    if (program_dir / 'main.py').exists():
        return [sys.executable, str(program_dir / 'main.py'), '--input', str(case_dir), '--output', str(out_file)]
    if (program_dir / 'predict.py').exists():
        # Python module call style
        return None  # handled separately
    raise FileNotFoundError('未找到可执行入口（run.sh / run.py / main.py / predict.py::predict）。')


def run_participant(program_dir: Path, case_dir: Path, out_file: Path, timeout_sec: float, mem_limit_mb: float):
    cmd = build_command(program_dir, case_dir, out_file)
    if cmd is not None:
        eprint('Executing:', ' '.join(cmd))
        preexec = set_memory_limit_bytes(mem_limit_mb)
        subprocess.run(cmd, cwd=str(program_dir), check=True, timeout=timeout_sec, preexec_fn=preexec)
        return
    # predict.py::predict
    sys.path.insert(0, str(program_dir))
    mod = __import__('predict')
    if not hasattr(mod, 'predict'):
        raise FileNotFoundError('predict.py 中缺少 predict(case_dir, out_file)')
    mod.predict(str(case_dir), str(out_file))


def main(argv=None):
    argv = argv or sys.argv[1:]
    input_dir, output_dir, program_dir, timeout_sec, mem_limit_mb = detect_dirs_and_limits(argv)
    eprint(f'INPUT_DIR={input_dir}')
    eprint(f'OUTPUT_DIR={output_dir}')
    eprint(f'PROGRAM_DIR={program_dir}')
    eprint(f'TIMEOUT_SECONDS={timeout_sec}')
    eprint(f'MEMORY_LIMIT_MB={mem_limit_mb}')
    
    # 调试：打印 /app 下的所有路径和文件
    eprint('=== INGESTION PROGRAM: /app 目录结构 ===')
    import os
    for root, dirs, files in os.walk('/app'):
        level = root.replace('/app', '').count(os.sep)
        indent = ' ' * 2 * level
        eprint(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            eprint(f'{subindent}{file}')
    eprint('=== END /app 目录结构 ===')

    # 调试：检查用户提交代码的可能位置
    eprint('=== 检查用户提交代码位置 ===')
    possible_dirs = ['/app/ingested_program', '/app/program', '/app/submission', '/app/code']
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            eprint(f'{dir_path} 存在:')
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    eprint(f'  文件: {item}')
                else:
                    eprint(f'  目录: {item}/')
        else:
            eprint(f'{dir_path} 不存在')
    eprint('=== END 检查用户提交代码位置 ===')

    # 调试：检查 program_dir 指向的目录内容
    eprint(f'=== 检查 program_dir={program_dir} 内容 ===')
    if program_dir.exists():
        for item in program_dir.iterdir():
            if item.is_file():
                eprint(f'  文件: {item.name}')
            else:
                eprint(f'  目录: {item.name}/')
    else:
        eprint(f'program_dir {program_dir} 不存在')
    eprint('=== END 检查 program_dir 内容 ===')

    # 使用共享目录而不是输出目录来存储预测文件
    shared_dir = Path('/app/shared')
    if not shared_dir.exists():
        shared_dir = output_dir  # 本地运行时回退到输出目录
    eprint(f'SHARED_DIR={shared_dir}')

    cases = find_cases(input_dir)
    if not cases:
        eprint('未发现用例目录（需要包含 jobs.json）。跳过摄取并正常退出。')
        # 摄取阶段可能在预测或评分前并行运行；没有用例时不应失败。
        # 创建空索引以便后续流程仍可检测到输出目录存在。
        ensure_dir(output_dir)
        ensure_dir(shared_dir)
        with open(output_dir / 'predictions_index.json', 'w', encoding='utf-8') as f:
            json.dump({'predictions': {}}, f, ensure_ascii=False, indent=2)
        with open(shared_dir / 'predictions_index.json', 'w', encoding='utf-8') as f:
            json.dump({'predictions': {}}, f, ensure_ascii=False, indent=2)
        eprint('Ingestion 完成（无用例）。')
        return

    # 在共享目录和输出目录都创建预测文件
    predictions_root = output_dir / 'predictions'
    shared_predictions_root = shared_dir / 'predictions'
    ensure_dir(predictions_root)
    ensure_dir(shared_predictions_root)

    index = {'predictions': {}}
    for case_dir in cases:
        case_id = case_dir.name
        out_dir = predictions_root / case_id
        shared_out_dir = shared_predictions_root / case_id
        ensure_dir(out_dir)
        ensure_dir(shared_out_dir)
        out_file = out_dir / 'schedule.json'
        shared_out_file = shared_out_dir / 'schedule.json'

        run_participant(program_dir, case_dir, out_file, timeout_sec, mem_limit_mb)

        # 复制到共享目录
        import shutil
        if out_file.exists():
            if out_file.resolve() != shared_out_file.resolve():
                eprint(f'复制预测文件到共享目录: {out_file} -> {shared_out_file}')
                shutil.copy2(out_file, shared_out_file)
            else:
                eprint('共享目录与输出目录相同，跳过复制')
        else:
            eprint(f'警告：用户程序未生成预测文件: {out_file}')

        # 轻量校验
        with open(out_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as ex:
                raise RuntimeError(f'{case_id} 的 schedule.json 不是合法 JSON: {ex}')
        # 新协议不要求 case_id 字段，若存在则校验一致
        if 'case_id' in data and data.get('case_id') != case_id:
            eprint(f'警告：schedule.json 的 case_id 与目录名不一致：{case_id} != {data.get("case_id")}')

        index['predictions'][case_id] = {'path': str(out_file.relative_to(output_dir))}

    # 写入索引与聚合到两个目录
    with open(output_dir / 'predictions_index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    # 为共享目录创建单独的索引，路径指向共享目录
    shared_index = {'predictions': {}}
    for case_id in index['predictions']:
        shared_index['predictions'][case_id] = {'path': f'predictions/{case_id}/schedule.json'}
    with open(shared_dir / 'predictions_index.json', 'w', encoding='utf-8') as f:
        json.dump(shared_index, f, ensure_ascii=False, indent=2)

    merged = {'cases': []}
    for case_id in sorted(index['predictions'].keys()):
        sch_path = output_dir / index['predictions'][case_id]['path']
        with open(sch_path, 'r', encoding='utf-8') as f:
            merged['cases'].append(json.load(f))
    with open(output_dir / 'predictions.json', 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False)
    with open(shared_dir / 'predictions.json', 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False)

    eprint('Ingestion 完成。')


if __name__ == '__main__':
    main()
