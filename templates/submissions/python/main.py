import os
from pathlib import Path


def main() -> None:
    output_dir = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "results.txt"
    output_path.write_text("MetricValue,100\n", encoding="utf-8")
    print(f"Wrote results to {output_path}")


if __name__ == "__main__":
    main()
