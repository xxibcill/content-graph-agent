import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv

from configs.settings import get_settings
from utils.persistence import save_metrics


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Record engagement metrics")
    parser.add_argument("--run-id", required=True, help="Run ID from saved output")
    parser.add_argument("--views", type=int, default=None)
    parser.add_argument("--likes", type=int, default=None)
    parser.add_argument("--comments", type=int, default=None)
    parser.add_argument("--shares", type=int, default=None)
    parser.add_argument("--saves", type=int, default=None)
    parser.add_argument("--notes", default=None, help="Optional notes")
    parser.add_argument("--output-file", default=None, help="Custom metrics file path")
    args = parser.parse_args()

    settings = get_settings()
    payload = {
        "run_id": args.run_id,
        "views": args.views,
        "likes": args.likes,
        "comments": args.comments,
        "shares": args.shares,
        "saves": args.saves,
        "notes": args.notes,
    }
    save_metrics(settings.output_dir, payload, output_path=args.output_file)


if __name__ == "__main__":
    main()
