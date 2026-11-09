#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import yaml


REQUIRED_FIELDS = ("title", "url")


def load_workflows(path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"Could not read valid YAML from {path}: {error}") from error

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a top-level list")
    return data


def validate_workflows(workflows):
    if not workflows:
        raise ValueError("Workflow data must not be empty")

    urls = set()
    for index, workflow in enumerate(workflows, start=1):
        if not isinstance(workflow, dict):
            raise ValueError(f"Workflow {index} must be a mapping")

        missing = [field for field in REQUIRED_FIELDS if not workflow.get(field)]
        if missing:
            raise ValueError(
                f"Workflow {index} is missing required values: {', '.join(missing)}"
            )

        url = workflow["url"]
        if url in urls:
            raise ValueError(f"Duplicate workflow URL: {url}")
        urls.add(url)


def validate_record_count(workflows, baseline, minimum_ratio):
    if baseline is None or not baseline:
        return

    minimum_count = math.ceil(len(baseline) * minimum_ratio)
    if len(workflows) < minimum_count:
        raise ValueError(
            f"Generated {len(workflows)} workflows; expected at least "
            f"{minimum_count} based on the current {len(baseline)} records"
        )


def build_parser():
    parser = argparse.ArgumentParser(description="Validate generated workflow data.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--minimum-ratio", type=float)
    return parser


def main():
    args = build_parser().parse_args()
    minimum_ratio = args.minimum_ratio
    if minimum_ratio is None and args.config:
        try:
            config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as error:
            raise ValueError(f"Could not read site configuration: {error}") from error
        minimum_ratio = (config.get("workflowhub") or {}).get(
            "minimum_record_ratio", 0.8
        )
    if minimum_ratio is None:
        minimum_ratio = 0.8
    if not 0 <= minimum_ratio <= 1:
        raise ValueError("--minimum-ratio must be between 0 and 1")

    workflows = load_workflows(args.candidate)
    baseline = load_workflows(args.baseline) if args.baseline else None
    validate_workflows(workflows)
    validate_record_count(workflows, baseline, minimum_ratio)
    print(f"Validated {len(workflows)} workflow records in {args.candidate}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(f"Validation failed: {error}") from error
