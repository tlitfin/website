import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import yaml

from scripts.workflowhub_finder import (
    WorkflowHubClient,
    build_parser,
    load_site_config,
    resolve_settings,
    write_workflows,
)


class WorkflowHubFinderTests(unittest.TestCase):
    def test_cli_accepts_explicit_integration_settings(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "--base-url",
                "https://dev.workflowhub.eu",
                "--collection-type",
                "collection",
                "--collection-id",
                "10",
                "--output",
                "_data/data_workflows.yaml",
            ]
        )

        self.assertEqual(args.base_url, "https://dev.workflowhub.eu")
        self.assertEqual(args.collection_type, "collection")
        self.assertEqual(args.collection_id, 10)
        self.assertEqual(args.output, Path("_data/data_workflows.yaml"))
        settings = resolve_settings(args, parser)
        self.assertEqual(settings["request_timeout"], 30.0)

    def test_disabled_site_integration_is_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "_config.yml"
            config.write_text("workflowhub:\n  enabled: false\n", encoding="utf-8")

            self.assertIsNone(load_site_config(config))

    def test_enabled_site_integration_is_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "_config.yml"
            config.write_text(
                "workflowhub:\n"
                "  enabled: true\n"
                "  base_url: https://example.test\n"
                "  collection_type: space\n"
                "  collection_id: 8\n"
                "  output: _data/workflows.yml\n",
                encoding="utf-8",
            )

            settings = load_site_config(config)

        self.assertEqual(settings["collection_type"], "space")
        self.assertEqual(settings["collection_id"], 8)

    def test_collection_data_is_rendered_and_sorted(self):
        client = WorkflowHubClient(
            "https://example.test/", "collection", 10, timeout=5
        )
        client._get_json = Mock(
            side_effect=[
                {"data": [{"id": "7", "attributes": {"title": "Project"}}]},
                {
                    "data": [
                        {"relationships": {"asset": {"data": {"id": "42"}}}}
                    ]
                },
                {
                    "data": {
                        "id": "42",
                        "attributes": {
                            "title": "Example_workflow",
                            "latest_version": 2,
                            "versions": [
                                {"version": 2, "remote": "https://example.test/repo"},
                                {"version": 1},
                            ],
                            "workflow_class": {"key": "nextflow"},
                            "updated_at": "2026-11-09T10:00:00Z",
                        },
                        "links": {"self": "/workflows/42?version=2"},
                        "relationships": {"projects": {"data": [{"id": "7"}]}},
                    }
                },
            ]
        )

        workflows = client.workflows()

        self.assertEqual(len(workflows), 1)
        self.assertEqual(workflows[0]["title"], "Example workflow")
        self.assertEqual(workflows[0]["remote_link"], "https://example.test/repo")
        self.assertEqual(workflows[0]["projects"], ["Project"])

    def test_requested_output_path_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "workflows.yaml"
            write_workflows([{"title": "Example"}], output)
            data = yaml.safe_load(output.read_text(encoding="utf-8"))

        self.assertEqual(data, [{"title": "Example"}])


if __name__ == "__main__":
    unittest.main()
