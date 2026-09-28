"""Keep GitHub issue forms and workflow configuration parseable."""

from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # CI installs PyYAML; keep runtime-only local test installs optional.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
GITHUB_DIR = ROOT / ".github"
ISSUE_TEMPLATE_DIR = GITHUB_DIR / "ISSUE_TEMPLATE"
ISSUE_FORM_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}


@unittest.skipIf(yaml is None, "PyYAML is installed by CI for GitHub config checks")
class GitHubYamlTests(unittest.TestCase):
    def test_all_github_yaml_files_parse(self):
        config_files = sorted(
            path
            for path in GITHUB_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        )
        self.assertTrue(config_files, "No GitHub YAML files were found")

        for path in config_files:
            with self.subTest(path=path.relative_to(ROOT)):
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(document, dict)

    def test_issue_forms_have_required_metadata_and_valid_fields(self):
        forms = sorted(ISSUE_TEMPLATE_DIR.glob("*.yml")) + sorted(
            ISSUE_TEMPLATE_DIR.glob("*.yaml")
        )
        self.assertTrue(forms, "No GitHub issue forms were found")

        for path in forms:
            with self.subTest(path=path.relative_to(ROOT)):
                form = yaml.safe_load(path.read_text(encoding="utf-8"))
                for key in ("name", "description", "body"):
                    self.assertIn(key, form)
                self.assertIsInstance(form["name"], str)
                self.assertIsInstance(form["description"], str)
                if "title" in form:
                    self.assertIsInstance(form["title"], str)
                self.assertIsInstance(form["body"], list)

                seen_ids = set()
                for field in form["body"]:
                    self.assertIsInstance(field, dict)
                    field_type = field.get("type")
                    self.assertIn(field_type, ISSUE_FORM_TYPES)
                    attributes = field.get("attributes", {})
                    self.assertIsInstance(attributes, dict)

                    if field_type == "markdown":
                        self.assertIn("value", attributes)
                        continue

                    field_id = field.get("id")
                    self.assertIsInstance(field_id, str)
                    self.assertTrue(field_id)
                    self.assertNotIn(field_id, seen_ids)
                    seen_ids.add(field_id)
                    self.assertIsInstance(attributes.get("label"), str)

                    if field_type in {"dropdown", "checkboxes"}:
                        self.assertIsInstance(attributes.get("options"), list)
                        self.assertTrue(attributes["options"])
                        if field_type == "dropdown":
                            self.assertTrue(
                                all(
                                    isinstance(option, str) and option.strip()
                                    for option in attributes["options"]
                                )
                            )
                        else:
                            self.assertTrue(
                                all(
                                    isinstance(option, dict)
                                    and isinstance(option.get("label"), str)
                                    and option["label"].strip()
                                    for option in attributes["options"]
                                )
                            )


if __name__ == "__main__":
    unittest.main()
