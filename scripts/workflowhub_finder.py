#!/usr/bin/env python3
import argparse
from pathlib import Path

import requests
import yaml


class WorkflowHubClient:
    def __init__(
        self,
        base_url,
        collection_type,
        collection_id,
        timeout=30,
        galaxy_launch_url_template="",
    ):
        self.base_url = base_url.rstrip("/")
        self.collection_type = collection_type
        self.collection_id = collection_id
        self.timeout = timeout
        self.galaxy_launch_url_template = galaxy_launch_url_template

    def _get_json(self, path):
        response = requests.get(f"{self.base_url}/{path}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _workflow_ids(self):
        if self.collection_type == "space":
            data = self._get_json(
                f"programmes/{self.collection_id}/workflows.json"
            )["data"]
            return [item["id"] for item in data]

        data = self._get_json(
            f"collections/{self.collection_id}/items.json"
        )["data"]
        return [item["relationships"]["asset"]["data"]["id"] for item in data]

    def _projects(self):
        data = self._get_json("projects.json")["data"]
        return {item["id"]: item["attributes"]["title"] for item in data}

    def _render_workflow(self, metadata, project_titles):
        data = metadata["data"]
        attributes = data["attributes"]
        workflow_id = str(data["id"])
        latest_version = attributes["latest_version"]
        versions = attributes.get("versions", [])
        remote = next(
            (
                version.get("remote", "")
                for version in versions
                if version.get("version") == latest_version
            ),
            "",
        )
        project_ids = data.get("relationships", {}).get("projects", {}).get("data", [])
        projects = list(
            dict.fromkeys(
                project_titles[item["id"]]
                for item in project_ids
                if item["id"] in project_titles
            )
        )
        workflow_class = attributes.get("workflow_class") or {}
        class_key = workflow_class.get("key", "")

        return {
            "title": attributes.get("title", "").replace("_", " "),
            "class": class_key,
            "url": data.get("links", {}).get("self", ""),
            "remote_link": remote,
            "edam_top": [
                annotation["label"]
                for annotation in attributes.get("topic_annotations", [])
            ] or "",
            "edam_ops": [
                annotation["label"]
                for annotation in attributes.get("operation_annotations", [])
            ] or "",
            "license": attributes.get("license") or "",
            "updated_at": (attributes.get("updated_at") or "").split("T")[0],
            "doi": attributes.get("doi") or "",
            "projects": projects or "",
            "guide_link": "",
            "launch_link": (
                self.galaxy_launch_url_template.format(workflow_id=workflow_id)
                if class_key == "galaxy" and self.galaxy_launch_url_template
                else ""
            ),
            "tools": attributes.get("tools") or "",
        }

    def workflows(self):
        project_titles = self._projects()
        workflows = [
            self._render_workflow(
                self._get_json(f"workflows/{workflow_id}.json"), project_titles
            )
            for workflow_id in sorted(set(self._workflow_ids()), key=str)
        ]
        return sorted(
            workflows,
            key=lambda workflow: (workflow["title"].casefold(), workflow["url"]),
        )


def write_workflows(workflows, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(
            workflows,
            default_flow_style=False,
            sort_keys=True,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def load_site_config(path):
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"Could not read site configuration from {path}: {error}") from error

    integration = config.get("workflowhub")
    if not isinstance(integration, dict) or not integration.get("enabled", False):
        return None
    return integration


def resolve_settings(args, parser):
    settings = {}
    if args.config:
        try:
            integration = load_site_config(args.config)
        except ValueError as error:
            parser.error(str(error))
        if integration is None:
            return None
        settings.update(integration)

    overrides = {
        "base_url": args.base_url,
        "collection_type": args.collection_type,
        "collection_id": args.collection_id,
        "output": args.output,
        "request_timeout": args.request_timeout,
        "galaxy_launch_url_template": args.galaxy_launch_url_template,
    }
    settings.update({key: value for key, value in overrides.items() if value is not None})

    required = ("base_url", "collection_type", "collection_id", "output")
    missing = [key for key in required if settings.get(key) in (None, "")]
    if missing:
        parser.error(
            "missing required integration settings: " + ", ".join(missing)
        )
    if settings["collection_type"] not in ("space", "collection"):
        parser.error("collection_type must be 'space' or 'collection'")

    settings.setdefault("request_timeout", 30.0)
    settings.setdefault("galaxy_launch_url_template", "")
    settings["collection_id"] = int(settings["collection_id"])
    settings["output"] = Path(settings["output"])
    return settings


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate WorkflowHub data for a Jekyll site."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Jekyll configuration containing an optional workflowhub section",
    )
    parser.add_argument("--base-url")
    parser.add_argument(
        "--collection-type",
        choices=("space", "collection"),
    )
    parser.add_argument("--collection-id", type=int)
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument("--request-timeout", type=float)
    parser.add_argument(
        "--galaxy-launch-url-template",
        help="Optional URL template containing {workflow_id}",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    settings = resolve_settings(args, parser)
    if settings is None:
        print("WorkflowHub integration is disabled; nothing to generate")
        return

    client = WorkflowHubClient(
        base_url=settings["base_url"],
        collection_type=settings["collection_type"],
        collection_id=settings["collection_id"],
        timeout=settings["request_timeout"],
        galaxy_launch_url_template=settings["galaxy_launch_url_template"],
    )
    workflows = client.workflows()
    write_workflows(workflows, settings["output"])
    print(f"Wrote {len(workflows)} workflows to {settings['output']}")


if __name__ == "__main__":
    main()
