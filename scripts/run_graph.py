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

from graph.content_graph import build_graph
from configs.settings import get_settings
from utils.persistence import save_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph workflow")
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument("--niche", default=None, help="Optional niche or audience")
    parser.add_argument("--limit", type=int, default=None, help="Max results")
    parser.add_argument("--show-sources", action="store_true", help="Show sources")
    parser.add_argument("--show-versions", action="store_true", help="Show prompt versions")
    parser.add_argument("--feedback", default=None, help="Manual feedback for revisions")
    parser.add_argument("--save-output", action="store_true", help="Save output to disk")
    parser.add_argument("--output-file", default=None, help="Custom output file path")
    args = parser.parse_args()

    graph = build_graph()
    state = {
        "topic": args.topic,
        "niche": args.niche,
        "research_limit": args.limit,
        "manual_feedback": args.feedback,
    }
    result = graph.invoke(state)
    script = (
        result.get("final_script")
        or result.get("validated_script")
        or result.get("draft_script")
    )
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
        settings = get_settings()
        saved = save_run(
            settings.output_dir,
            {
                "topic": args.topic,
                "niche": args.niche,
                "result": result,
            },
            output_path=args.output_file,
        )
        print(f"saved_run_id={saved['run_id']}")
        print(f"saved_path={saved['path']}")


if __name__ == "__main__":
    main()
