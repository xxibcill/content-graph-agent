import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv

from utils.logging import configure_logging

load_dotenv()
configure_logging()

from agents.research_agent import format_bullets, run_research


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the research agent")
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument("--niche", default=None, help="Optional niche or audience")
    parser.add_argument("--limit", type=int, default=None, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output full JSON")
    args = parser.parse_args()

    result = run_research(args.topic, args.niche, args.limit)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return

    print(format_bullets(result.get("bullets", [])))


if __name__ == "__main__":
    main()
