import argparse
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

from services.content_service import run_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph workflow")
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument("--niche", default=None, help="Optional niche or audience")
    parser.add_argument("--limit", type=int, default=None, help="Max results")
    parser.add_argument(
        "--research-mode",
        choices=("basic", "react"),
        default=None,
        help="Research strategy to use",
    )
    parser.add_argument("--show-sources", action="store_true", help="Show sources")
    parser.add_argument("--show-versions", action="store_true", help="Show prompt versions")
    parser.add_argument("--feedback", default=None, help="Manual feedback for revisions")
    parser.add_argument("--save-output", action="store_true", help="Save output to disk")
    parser.add_argument("--output-file", default=None, help="Custom output file path")
    args = parser.parse_args()

    payload = run_workflow(
        topic=args.topic,
        niche=args.niche,
        limit=args.limit,
        research_mode=args.research_mode,
        feedback=args.feedback,
        save_output_enabled=args.save_output,
        output_file=args.output_file,
    )
    result = payload["result"]
    script = payload["script"]
    if script:
        print(script)
    else:
        print(result.get("trends", ""))
    if args.show_sources:
        for source in result.get("research_sources", []):
            print(f"- {source}")

    if args.show_versions:
        writer_version = result.get("writer_prompt_version")
        creative_version = result.get("creative_prompt_version")
        if writer_version:
            print(f"writer_prompt_version={writer_version}")
        if creative_version:
            print(f"creative_prompt_version={creative_version}")

    if args.save_output:
        print(f"saved_run_id={payload['saved_run_id']}")
        print(f"saved_path={payload['saved_path']}")


if __name__ == "__main__":
    main()
