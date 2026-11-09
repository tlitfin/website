import unittest

from scripts.validate_workflow_data import validate_record_count, validate_workflows


def workflow(title, url):
    return {"title": title, "class": "nextflow", "url": url}


class WorkflowDataValidationTests(unittest.TestCase):
    def test_valid_workflows(self):
        validate_workflows([workflow("One", "/workflows/1")])

    def test_duplicate_urls_are_rejected(self):
        workflows = [
            workflow("One", "/workflows/1"),
            workflow("Two", "/workflows/1"),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate workflow URL"):
            validate_workflows(workflows)

    def test_large_record_count_drop_is_rejected(self):
        candidate = [workflow("One", "/workflows/1")]
        baseline = [
            workflow("One", "/workflows/1"),
            workflow("Two", "/workflows/2"),
        ]

        with self.assertRaisesRegex(ValueError, "expected at least 2"):
            validate_record_count(candidate, baseline, 0.8)


if __name__ == "__main__":
    unittest.main()
