#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


INPUT_DIR = Path('/app/input_data')
INPUT_RES_DIR = Path('/app/input/res')
SUBMISSION_DIR = Path('/app/ingested_program')
OUTPUT_DIR = Path('/app/output')
RES_DIR = OUTPUT_DIR / 'res'
METADATA_FILE = OUTPUT_DIR / 'metadata.json'


def locate_input_csv(root: Path) -> Path:
    """Find inputs.csv within the extracted input directory."""
    direct = root / 'inputs.csv'
    if direct.exists():
        return direct

    matches = sorted(
        (path for path in root.rglob('inputs.csv') if path.is_file()),
        key=lambda path: len(path.relative_to(root).parts),
    )
    if not matches:
        raise FileNotFoundError('未找到输入数据文件 inputs.csv，请确认数据包结构正确。')
    return matches[0]


def locate_build_script(root: Path) -> Path:
    """Resolve the participant build.sh path, even if wrapped in a sub目录."""
    candidate = root / 'build.sh'
    if candidate.exists():
        return candidate

    matches = sorted(
        (path for path in root.rglob('build.sh') if path.is_file()),
        key=lambda path: len(path.relative_to(root).parts),
    )
    if not matches:
        raise FileNotFoundError('提交中缺少 build.sh，请确认包含该脚本。')
    return matches[0]


def ensure_paths() -> tuple[Path, Path, Path]:
    """Validate expected layout and return build script, input csv, output path."""
    input_csv = locate_input_csv(INPUT_DIR)
    build_script = locate_build_script(SUBMISSION_DIR)
    RES_DIR.mkdir(parents=True, exist_ok=True)
    predictions_csv = RES_DIR / 'predictions.csv'
    return build_script, input_csv, predictions_csv


def run_submission(build_script: Path, input_csv: Path, predictions_csv: Path) -> float:
    """Execute participant build script and return elapsed seconds."""
    # 允许脚本在未标记可执行位时运行
    os.chmod(build_script, 0o755)

    env = os.environ.copy()
    env['INPUT_CSV'] = str(input_csv)
    env['OUTPUT_CSV'] = str(predictions_csv)

    start = time.time()
    completed = subprocess.run(
        ['bash', str(build_script), str(input_csv), str(predictions_csv)],
        cwd=str(build_script.parent),
        env=env,
        check=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f'build.sh 返回非零退出码: {completed.returncode}')

    if not predictions_csv.exists():
        raise FileNotFoundError('build.sh 执行后仍未生成预测文件 predictions.csv。')

    return time.time() - start


def validate_predictions(predictions_csv: Path) -> None:
    """确保预测文件包含必要的表头。"""
    import csv

    with predictions_csv.open('r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError('预测文件为空，缺少表头。') from exc
        if header != ['id', 'sum']:
            raise ValueError('预测文件表头必须为: id,sum')


def write_metadata(elapsed: float) -> None:
    METADATA_FILE.write_text(json.dumps({'duration': elapsed}), encoding='utf-8')


def mirror_predictions(predictions_csv: Path) -> None:
    """在评分阶段将预测复制到 /app/input/res."""
    try:
        INPUT_RES_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f'警告: 创建 {INPUT_RES_DIR} 失败: {exc}', file=sys.stderr)
        return

    target = INPUT_RES_DIR / predictions_csv.name
    try:
        shutil.copy2(predictions_csv, target)
        print(f'已同步预测文件到 {target}')
    except Exception as exc:  # noqa: BLE001
        print(f'警告: 无法复制预测到 {target}: {exc}', file=sys.stderr)


def main() -> None:
    build_script, input_csv, predictions_csv = ensure_paths()
    print(f'使用输入数据: {input_csv}')
    print(f'使用 build.sh: {build_script}')
    elapsed = run_submission(build_script, input_csv, predictions_csv)
    validate_predictions(predictions_csv)
    mirror_predictions(predictions_csv)
    write_metadata(elapsed)
    print(f'预测生成完成，用时 {elapsed:.2f} 秒。输出文件位于: {predictions_csv}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f'Ingestion 失败: {exc}', file=sys.stderr)
        raise
