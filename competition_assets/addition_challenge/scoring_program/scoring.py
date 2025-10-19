import csv
import json
import time
from pathlib import Path

REF_PATH = Path("/app/input/ref/answers.csv")
PREDICTION_LOCATIONS = [
    Path("/app/output/res/predictions.csv"),
    Path("/app/input/res/predictions.csv"),
]
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCORES_FILE = OUTPUT_DIR / "scores.json"
DETAILS_FILE = OUTPUT_DIR / "detailed_results.html"


def read_csv(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    records = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected_columns = {"id", "sum"}
        if set(reader.fieldnames or []) != expected_columns:
            raise ValueError(f"{path.name} must contain columns: id,sum")
        for row in reader:
            try:
                idx = int(row["id"])
                value = float(row["sum"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value in {path.name}: {row}") from exc
            records[idx] = value
    return records


def resolve_predictions_path(
    candidates: list[Path], timeout: float = 10.0, poll_interval: float = 0.5
) -> Path:
    """Return the first existing predictions.csv path among candidates."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for path in candidates:
            if path.exists():
                return path
        time.sleep(poll_interval)

    formatted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Missing predictions file. Checked: {formatted}")


def main() -> None:
    reference = read_csv(REF_PATH)
    predictions_path = resolve_predictions_path(PREDICTION_LOCATIONS)
    predictions = read_csv(predictions_path)

    if reference.keys() != predictions.keys():
        missing = reference.keys() - predictions.keys()
        extra = predictions.keys() - reference.keys()
        raise ValueError(
            "Prediction IDs do not match reference. "
            f"Missing: {sorted(missing)} Extra: {sorted(extra)}"
        )

    absolute_errors = []
    for idx, truth in reference.items():
        pred = predictions[idx]
        absolute_errors.append(abs(pred - truth))

    mae = sum(absolute_errors) / len(absolute_errors)
    score = max(0.0, 1.0 - mae)

    with SCORES_FILE.open("w", encoding="utf-8") as f:
        json.dump({"accuracy": score}, f)

    DETAILS_FILE.write_text(
        """
        <html>
            <head><title>Detailed Results</title></head>
            <body>
                <h1>Simple Addition Challenge</h1>
                <p>Average absolute error (MAE): {mae:.4f}</p>
                <p>Final score (1 - MAE, lower bounded at 0): {score:.4f}</p>
            </body>
        </html>
        """.format(mae=mae, score=score),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
