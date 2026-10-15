"""Regression checks for repository tester write limits (no network calls)."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ai_repo_tester.py"
SPEC = importlib.util.spec_from_file_location("ai_repo_tester", SCRIPT)
tester = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tester
SPEC.loader.exec_module(tester)


class PullRequestLimitTests(unittest.TestCase):
    def run_tester(self, max_prs, dry_run=False):
        repos = [
            SimpleNamespace(name=f"repo{i}", full_name=f"owner/repo{i}",
                            clone_url=f"https://github.com/owner/repo{i}.git",
                            language="Python", archived=False)
            for i in range(3)
        ]
        gh = Mock()
        gh.get_user.return_value.get_repos.return_value = repos

        def failed_result(**kwargs):
            return tester.RepoResult(
                repo_name=kwargs["repo_name"], full_name=kwargs["full_name"],
                url=kwargs["clone_url"], language=kwargs["language"],
                checks=[tester.CheckResult("python_lint", False)],
            )

        with tempfile.TemporaryDirectory() as output:
            args = SimpleNamespace(user="owner", max_prs=max_prs, dry_run=dry_run,
                                   output_dir=output, allowlist="unused", verbose=False)
            with patch.object(tester, "_GITHUB_AVAILABLE", True), \
                 patch.object(tester, "parse_args", return_value=args), \
                 patch.object(tester, "Github", return_value=gh), \
                 patch.object(tester, "load_allowlist",
                              return_value={repo.full_name for repo in repos}), \
                 patch.object(tester, "test_repo", side_effect=failed_result), \
                 patch.object(tester, "open_fix_pr", return_value="https://example.test/pr") as create, \
                 patch.dict("os.environ", {}, clear=True), patch("builtins.print"):
                self.assertEqual(tester.main(), 1)
                return create.call_count

    def test_zero_disables_pr_creation(self):
        self.assertEqual(self.run_tester(0), 0)

    def test_one_limits_pr_creation(self):
        self.assertEqual(self.run_tester(1), 1)

    def test_two_limits_pr_creation(self):
        self.assertEqual(self.run_tester(2), 2)

    def test_negative_limit_does_not_create_prs(self):
        self.assertEqual(self.run_tester(-1), 0)


if __name__ == "__main__":
    unittest.main()
