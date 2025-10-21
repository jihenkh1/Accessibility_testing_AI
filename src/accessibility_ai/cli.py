import argparse
import json
from pathlib import Path
from typing import Optional

from .analyzer import AccessibilityAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Analyze accessibility reports and optionally enrich with AI.")
    parser.add_argument("--input", required=True, help="Path to accessibility JSON report (axe/Pa11y)")
    parser.add_argument("--url", default="Uploaded Report", help="Context URL or report name")
    parser.add_argument("--framework", default="html", help="Target framework for fixes (html, react, ...)")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI enrichment")
    parser.add_argument("--max-ai-issues", type=int, default=None, help="Max unique issue groups to enrich with AI (default: unlimited)")
    parser.add_argument("--out", default=None, help="Output JSON file to write results")
    args = parser.parse_args()

    report_path = Path(args.input)
    data = json.loads(report_path.read_text(encoding="utf-8"))

    analyzer = AccessibilityAnalyzer(use_ai=args.use_ai, max_ai_issues=args.max_ai_issues)
    enhanced = analyzer.analyze_issues(data, url=args.url, framework=args.framework)
    summary = analyzer.get_analysis_summary(enhanced)

    # Print a concise summary to stdout
    print("Analysis Summary:")
    print(json.dumps(summary, indent=2))

    if args.out:
        out_payload = {
            "enhanced_issues": [e.dict() for e in enhanced],
            "summary": summary,
            "url": args.url,
            "framework": args.framework,
        }
        Path(args.out).write_text(json.dumps(out_payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

