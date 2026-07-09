import unittest
from unittest.mock import patch, mock_open

from src.ciforge.scanner import Finding, _extract_diff_sections
from src.ciforge import code_quality, secrets, config_validator, coverage, ai_reviewer, assets, l10n, metrics

class TestCiforge(unittest.TestCase):

    def test_extract_diff_sections(self):
        diff = """--- a/file.py
+++ b/file.py
@@ -10,3 +10,4 @@
 def func():
-    pass
+    print('hello')
+    return True
"""
        added = _extract_diff_sections(diff)
        self.assertEqual(added, [(11, "    print('hello')"), (12, "    return True")])

    def test_code_quality(self):
        diff = "@@ -0,0 +1,55 @@\n+def large_func():\n" + "+    pass\n" * 50
        findings = code_quality.analyze("file.py", diff)
        self.assertTrue(any("Very large function" in f.message for f in findings))
        self.assertTrue(any(f.severity == "low" for f in findings))

        diff = "@@ -0,0 +1,2 @@\n+# TODO: fix this\n+console.log('test')\n"
        findings = code_quality.analyze("file.js", diff)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].message, "Found TODO")
        self.assertEqual(findings[1].message, "Found debug statement")

    def test_secrets(self):
        fake_aws = "AKIA" + "IOSFODNN7EXAMPLE"
        diff = f"@@ -0,0 +1,1 @@\n+my_var = '{fake_aws}'\n"
        findings = secrets.analyze("config.py", diff)
        self.assertEqual(len(findings), 1)
        self.assertTrue("aws_key" in findings[0].message)
        self.assertEqual(findings[0].severity, "critical")

        fake_gh = "ghp_" + "123456789012345678901234567890123456"
        diff2 = f"@@ -0,0 +1,1 @@\n+my_token_var = '{fake_gh}'\n"
        findings2 = secrets.analyze("auth.py", diff2)
        self.assertEqual(len(findings2), 1)
        self.assertTrue("github_token" in findings2[0].message)

    def test_config_validator_env(self):
        diff = "@@ -0,0 +1,1 @@\n+SECRET=123\n"
        findings = config_validator.analyze(".env", diff)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "high")
        
        findings2 = config_validator.analyze(".env.example", diff)
        self.assertEqual(len(findings2), 0)

    def test_config_validator_yaml(self):
        diff = "@@ -0,0 +1,1 @@\n+\tkey: value\n"
        findings = config_validator.analyze("config.yml", diff)
        self.assertEqual(len(findings), 1)
        self.assertTrue("tabs" in findings[0].message)
        self.assertEqual(findings[0].severity, "medium")

    def test_config_validator_toml_xml(self):
        import os
        with open("test_bad.xml", "w") as f:
            f.write("<unclosed>")
        findings_xml = config_validator.analyze("test_bad.xml", "")
        self.assertEqual(len(findings_xml), 1)
        self.assertIn("Invalid XML", findings_xml[0].message)
        os.remove("test_bad.xml")
        
        try:
            import tomllib
            with open("test_bad.toml", "wb") as f:
                f.write(b"[unclosed")
            findings_toml = config_validator.analyze("test_bad.toml", "")
            self.assertEqual(len(findings_toml), 1)
            self.assertIn("Invalid TOML", findings_toml[0].message)
            os.remove("test_bad.toml")
        except ImportError:
            pass

    @patch("os.path.exists", return_value=True)
    def test_coverage(self, mock_exists):
        with patch("builtins.open", mock_open(read_data='{"coverage": 75.0}')):
            findings = coverage.analyze()
            self.assertEqual(len(findings), 1)
            self.assertTrue("Code coverage too low" in findings[0].message)
            self.assertEqual(findings[0].severity, "medium")

    @patch("os.environ.get", return_value="dummy_key")
    @patch("src.ciforge.ai_reviewer.git_changed_files", return_value=["test.py"])
    @patch("src.ciforge.ai_reviewer.git_diff", return_value="+print('test')")
    @patch("urllib.request.urlopen")
    def test_ai_reviewer(self, mock_urlopen, mock_git_diff, mock_git_files, mock_env):
        from io import BytesIO
        import json
        mock_response = BytesIO(json.dumps({"choices": [{"message": {"content": "Looks good"}}]}).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = mock_response
        findings = ai_reviewer.analyze()
        self.assertEqual(len(findings), 1)
        self.assertTrue("Looks good" in findings[0].message)

    @patch("os.walk")
    @patch("os.path.getsize", return_value=600 * 1024)
    def test_assets(self, mock_getsize, mock_walk):
        mock_walk.return_value = [(".", [], ["large_image.png"])]
        findings = assets.analyze()
        self.assertEqual(len(findings), 1)
        self.assertTrue("Unoptimized asset" in findings[0].message)

    @patch("os.walk")
    @patch("builtins.open", new_callable=mock_open)
    def test_l10n(self, mock_open_file, mock_walk):
        mock_walk.return_value = [(".", [], ["en.json", "fr.json"])]
        def side_effect(filename, *args, **kwargs):
            if "en.json" in filename:
                return mock_open(read_data='{"hello": "world", "test": "1"}').return_value
            else:
                return mock_open(read_data='{"hello": "monde"}').return_value
        mock_open_file.side_effect = side_effect
        findings = l10n.analyze()
        self.assertEqual(len(findings), 1)
        self.assertTrue("Missing translation key: 'test'" in findings[0].message)

    @patch("subprocess.run")
    def test_metrics(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1000\n2000\n5600"
        findings = metrics.analyze()
        self.assertEqual(len(findings), 1)
        self.assertTrue("Velocity Report" in findings[0].message)

    @patch("os.path.exists", return_value=True)
    def test_code_quality_ast(self, mock_exists):
        python_code = "def complex_func():\n" + "".join([f"    if True:\n        pass\n" for _ in range(11)])
        with patch("builtins.open", mock_open(read_data=python_code)):
            findings = code_quality.analyze("file.py", "+def complex_func():")
            self.assertTrue(any("High cyclomatic complexity" in f.message for f in findings))

    def test_ignore_rules(self):
        import os
        from src.ciforge.ignore import rules
        with open('.ciforge-ignore', 'w') as f:
            f.write("tests/*\nAKIAIOSFODNN7EXAMPLE\n")
        rules.patterns = []
        rules._load()
        self.assertTrue(rules.is_ignored_file("tests/test_foo.py"))
        self.assertFalse(rules.is_ignored_file("src/ciforge/cli.py"))
        self.assertTrue(rules.is_ignored_secret("my_secret = 'AKIAIOSFODNN7EXAMPLE'"))
        self.assertFalse(rules.is_ignored_secret("my_secret = 'OTHERSECRET'"))
        os.remove('.ciforge-ignore')
        rules.patterns = []
    def test_fixer(self):
        import os
        from src.ciforge.fixer import fix_all
        from src.ciforge.scanner import Finding
        with open("test_fix.py", "w") as f:
            f.write("def foo():\n    print('debug')\n")
        with open("test_fix.yml", "w") as f:
            f.write("key:\n\tvalue\n")
        findings = [
            Finding("test_fix.py", 2, "Found debug statement", "medium"),
            Finding("test_fix.yml", 2, "YAML file indented with tabs", "medium")
        ]
        fixed = fix_all(findings)
        self.assertEqual(fixed, 2)
        with open("test_fix.py", "r") as f:
            self.assertEqual(f.read(), "def foo():\n    # print('debug')\n")
        with open("test_fix.yml", "r") as f:
            self.assertEqual(f.read(), "key:\n  value\n")
        os.remove("test_fix.py")
        os.remove("test_fix.yml")

    def test_badges(self):
        from src.ciforge import badges
        from src.ciforge.scanner import Finding
        import os
        
        findings = [Finding(file="f", line=1, message="m", severity="low")]
        badges.generate_badge(findings)
        self.assertTrue(os.path.exists("ciforge-badge.svg"))
        with open("ciforge-badge.svg", "r") as f:
            content = f.read()
            self.assertIn("B", content)
            self.assertIn("#97CA00", content)
        os.remove("ciforge-badge.svg")

    @patch("os.environ.get")
    @patch("os.path.exists", return_value=True)
    def test_community(self, mock_exists, mock_env_get):
        from src.ciforge import community
        import json
        
        mock_env_get.return_value = "dummy.json"
        with patch("builtins.open", mock_open(read_data=json.dumps({"pull_request": {"author_association": "FIRST_TIMER"}}))):
            msg = community.get_welcome_message()
            self.assertIn("Welcome", msg)

    @patch("os.path.isdir", return_value=True)
    @patch("os.path.exists", return_value=True)
    @patch("os.chmod")
    @patch("os.stat")
    def test_install_git_hook(self, mock_stat, mock_chmod, mock_exists, mock_isdir):
        from src.ciforge.cli import install_git_hook
        import sys
        
        mock_stat.return_value.st_mode = 0o644
        with patch("builtins.open", mock_open()) as m_open:
            try:
                install_git_hook()
            except SystemExit:
                pass
            m_open.assert_called_with(".git/hooks/pre-commit", "w")

    # ------------------------------------------------------------------
    # New v2.0.0 tests
    # ------------------------------------------------------------------

    def test_dead_code(self):
        """A function defined in one temp file but never referenced elsewhere
        should be flagged as dead code."""
        import os
        import sys
        import tempfile

        # Create a temporary directory and work inside it
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # File A defines a function that is NOT referenced anywhere else
                with open("module_a.py", "w") as f:
                    f.write("def orphaned_func():\n    pass\n")

                # File B contains no reference to orphaned_func
                with open("module_b.py", "w") as f:
                    f.write("x = 1\n")

                from src.ciforge import dead_code  # noqa: re-import in new cwd context
                # Reload to pick up fresh os.walk from new cwd
                import importlib
                importlib.reload(dead_code)

                findings = dead_code.analyze()
                messages = [f.message for f in findings]
                self.assertTrue(
                    any("orphaned_func" in m for m in messages),
                    f"Expected orphaned_func to be flagged as dead code. Got: {messages}"
                )
                for finding in findings:
                    if "orphaned_func" in finding.message:
                        self.assertEqual(finding.severity, "low")
            finally:
                os.chdir(orig_cwd)

    def test_changelog(self):
        """Mock git log output and verify sections are correctly generated."""
        from unittest.mock import patch, MagicMock
        from src.ciforge import changelog

        fake_log = (
            "abc1234 feat: add login page\n"
            "def5678 fix: handle null pointer\n"
            "aaa0001 breaking: remove deprecated API\n"
            "bbb0002 chore: update dependencies\n"
            "ccc0003 docs: update README\n"
            "ddd0004 refactor: simplify auth module\n"
            "eee0005 random commit without prefix\n"
        )

        mock_result = MagicMock()
        mock_result.stdout = fake_log
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            output = changelog.generate()

        self.assertIn("## ✨ Features", output)
        self.assertIn("## 🐛 Bug Fixes", output)
        self.assertIn("## 💥 Breaking Changes", output)
        self.assertIn("## 🔧 Chores", output)
        self.assertIn("add login page", output)
        self.assertIn("handle null pointer", output)
        self.assertIn("remove deprecated API", output)
        self.assertIn("update dependencies", output)

    def test_config_drift(self):
        """Two temp env files with differing keys should produce drift findings."""
        import os
        import tempfile
        from src.ciforge import config_drift

        with tempfile.TemporaryDirectory() as tmpdir:
            prod_path = os.path.join(tmpdir, ".env.production")
            staging_path = os.path.join(tmpdir, ".env.staging")

            with open(prod_path, "w") as f:
                f.write("DATABASE_URL=postgres://prod\n")
                f.write("SECRET_KEY=abc123\n")
                f.write("SHARED_KEY=same\n")

            with open(staging_path, "w") as f:
                f.write("STAGING_ONLY_VAR=foo\n")
                f.write("SHARED_KEY=same\n")

            findings = config_drift.analyze(prod_path, staging_path)

        messages = [f.message for f in findings]
        severities = [f.severity for f in findings]

        # DATABASE_URL and SECRET_KEY in prod but not staging
        self.assertTrue(any("DATABASE_URL" in m for m in messages))
        self.assertTrue(any("SECRET_KEY" in m for m in messages))
        # STAGING_ONLY_VAR in staging but not prod
        self.assertTrue(any("STAGING_ONLY_VAR" in m for m in messages))
        # SHARED_KEY present in both — should NOT appear
        self.assertFalse(any("SHARED_KEY" in m for m in messages))
        # All findings should be medium severity
        self.assertTrue(all(s == "medium" for s in severities))

    def test_multi_ai_openai(self):
        """multi_ai.analyze should parse JSON findings from an OpenAI-style response."""
        import json
        from io import BytesIO
        from unittest.mock import patch, MagicMock
        from src.ciforge import multi_ai

        fake_issues = [
            {"line": 5, "message": "Missing error handling", "severity": "high"},
        ]
        openai_response = {
            "choices": [{"message": {"content": json.dumps(fake_issues)}}]
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(openai_response).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", {"CIFORGE_AI_KEY": "test-key", "CIFORGE_AI_PROVIDER": "openai"}):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                findings = multi_ai.analyze("+x = 1/0")

        self.assertEqual(len(findings), 1)
        self.assertIn("Missing error handling", findings[0].message)
        self.assertEqual(findings[0].severity, "high")

    def test_multi_ai_no_key_returns_empty(self):
        """multi_ai.analyze should return [] gracefully when no API key is set."""
        import os
        from src.ciforge import multi_ai

        env = {k: v for k, v in os.environ.items()
               if k not in ("CIFORGE_AI_KEY", "OPENAI_API_KEY")}
        env["CIFORGE_AI_PROVIDER"] = "openai"

        from unittest.mock import patch
        with patch.dict("os.environ", env, clear=True):
            findings = multi_ai.analyze("+some code change")

        self.assertEqual(findings, [])


    # ------------------------------------------------------------------
    # Infra v2.0.0 tests
    # ------------------------------------------------------------------

    def test_deploy_check_fail(self):
        """When urlopen raises, deploy_check should return a critical finding."""
        import urllib.error
        from unittest.mock import patch
        from src.ciforge import deploy_check

        with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
            findings = deploy_check.check("http://localhost:9999", retries=1, timeout=1)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "critical")
        self.assertIn("could not reach", findings[0].message)

    def test_arch_diagram(self):
        """Temp py files with cross-imports should produce correct Mermaid edges."""
        import os
        import tempfile
        import importlib
        from src.ciforge import arch_diagram

        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # module_a imports module_b
                with open("module_a.py", "w") as f:
                    f.write("import module_b\n")
                # module_b has no internal imports
                with open("module_b.py", "w") as f:
                    f.write("x = 1\n")

                importlib.reload(arch_diagram)
                diagram = arch_diagram.generate()

                self.assertIn("graph TD", diagram)
                self.assertIn("module_a --> module_b", diagram)
            finally:
                os.chdir(orig_cwd)

    def test_mobile_lint(self):
        """pubspec.yaml missing 'version:' should produce a high-severity finding."""
        import os
        import tempfile
        import importlib
        from src.ciforge import mobile_lint

        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Write a pubspec.yaml without the version field
                with open("pubspec.yaml", "w") as f:
                    f.write("name: my_app\n")
                    f.write("environment:\n")
                    f.write("  sdk: flutter\n")

                importlib.reload(mobile_lint)
                findings = mobile_lint.analyze()

                high_findings = [f for f in findings if f.severity == "high"]
                self.assertTrue(
                    len(high_findings) >= 1,
                    f"Expected at least one high finding; got: {findings}"
                )
                self.assertTrue(
                    any("version" in f.message.lower() for f in high_findings),
                    f"Expected a 'version' finding; got: {[f.message for f in high_findings]}"
                )
            finally:
                os.chdir(orig_cwd)


if __name__ == '__main__':
    unittest.main()
