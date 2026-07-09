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



    # ------------------------------------------------------------------
    # V4 tests
    # ------------------------------------------------------------------

    def test_blast_radius(self):
        import os, tempfile
        from src.ciforge import blast_radius
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                for i in range(15):
                    with open(f"mod{i}.py", "w") as f:
                        f.write("x=1\n")
                with open("main.py", "w") as f:
                    for i in range(15):
                        f.write(f"import mod{i}\n")
                findings = blast_radius.analyze()
                self.assertTrue(len(findings) == 1)
                self.assertIn("Blast Radius Risk", findings[0].message)
                self.assertEqual(findings[0].severity, "medium")
            finally:
                os.chdir(orig_cwd)

    def test_mcp_scan(self):
        import os, tempfile
        from src.ciforge import mcp_scan
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with open("mcp.json", "w") as f:
                    f.write('{"name": "test"}')
                findings = mcp_scan.analyze()
                self.assertTrue(len(findings) == 1)
                self.assertIn("Missing mcpServers key", findings[0].message)
                self.assertEqual(findings[0].severity, "high")
            finally:
                os.chdir(orig_cwd)

    def test_schema_guardian(self):
        import os, tempfile
        from src.ciforge import schema_guardian
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with open("schema.sql", "w") as f:
                    f.write("CREATE TABLE xyz;\nDROP TABLE xyz;\n")
                findings = schema_guardian.analyze()
                self.assertTrue(len(findings) == 1)
                self.assertIn("Breaking Schema Change detected", findings[0].message)
                self.assertEqual(findings[0].severity, "high")
            finally:
                os.chdir(orig_cwd)

    def test_prompt_scan(self):
        import os, tempfile
        from src.ciforge import prompt_scan
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with open("llm_call.py", "w") as f:
                    f.write("llm.invoke(f'hello {user_input}')\n")
                findings = prompt_scan.analyze()
                self.assertTrue(len(findings) == 1)
                self.assertIn("Potential Prompt Injection", findings[0].message)
                self.assertEqual(findings[0].severity, "high")
            finally:
                os.chdir(orig_cwd)

    @patch("urllib.request.urlopen")
    def test_discord_notify(self, mock_urlopen):
        from src.ciforge import discord_notify
        discord_notify.send_notification("http://discord.com/webhook", 5)
        self.assertTrue(mock_urlopen.called)

    @patch("subprocess.run")
    def test_semantic_bump_major(self, mock_run):
        from src.ciforge import semantic_bump
        import os, tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_run.return_value.stdout = "abc1234 feat!: big change\n"
            with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
                f.write('version = "1.2.3"\n')
            new_v = semantic_bump.bump_version(tmpdir)
            self.assertEqual(new_v, "2.0.0")

    @patch("subprocess.run")
    def test_semantic_bump_minor(self, mock_run):
        from src.ciforge import semantic_bump
        import os, tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_run.return_value.stdout = "abc1234 feat: minor feature\n"
            with open(os.path.join(tmpdir, "pyproject.toml"), "w") as f:
                f.write('version = "1.2.3"\n')
            new_v = semantic_bump.bump_version(tmpdir)
            self.assertEqual(new_v, "1.3.0")

    @patch("os.path.exists")
    @patch("urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open)
    def test_vuln_scan(self, mock_file, mock_urlopen, mock_exists):
        from src.ciforge import vuln_scan
        import json
        from io import BytesIO
        from unittest.mock import MagicMock
        mock_exists.side_effect = lambda x: x in ['requirements.txt', 'package.json']
        
        def mock_read(filename, *args, **kwargs):
            if filename == 'requirements.txt':
                return mock_open(read_data="requests==2.30.0\ndjango==4.3\n").return_value
            elif filename == 'package.json':
                return mock_open(read_data='{"dependencies": {"lodash": "4.17.20"}}').return_value
            return mock_open(read_data="").return_value
        
        mock_file.side_effect = mock_read
        
        # Mock OSV API response
        def mock_urlopen_call(*args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"vulns": [{"id": "OSV-1"}]}).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_resp.__exit__.return_value = False
            return mock_resp
            
        mock_urlopen.side_effect = mock_urlopen_call
        
        findings = vuln_scan.analyze()
        self.assertEqual(len(findings), 3) # requests, django, lodash
        self.assertTrue(any("requests" in f.message for f in findings))
        self.assertTrue(any("lodash" in f.message for f in findings))

    @patch("os.path.exists")
    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_iac_scan(self, mock_file, mock_glob, mock_exists):
        from src.ciforge import iac_scan
        mock_exists.return_value = True
        mock_glob.return_value = ["main.tf"]
        
        def mock_read(filename, *args, **kwargs):
            if filename == 'Dockerfile':
                return mock_open(read_data="FROM ubuntu\nUSER root\nEXPOSE 0.0.0.0").return_value
            elif filename == 'docker-compose.yml':
                return mock_open(read_data="ports:\n  - '0.0.0.0:80:80'").return_value
            elif filename == 'main.tf':
                return mock_open(read_data='access_key = "AKIA123"\nbind = "0.0.0.0"').return_value
            return mock_open(read_data="").return_value
            
        mock_file.side_effect = mock_read
        findings = iac_scan.analyze()
        self.assertEqual(len(findings), 5)

    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_duplication(self, mock_file, mock_glob):
        from src.ciforge import duplication
        mock_glob.return_value = ["file1.py", "file2.py"]
        
        def mock_read(filename, *args, **kwargs):
            if filename == "file1.py":
                return mock_open(read_data="def func1():\n  a = 1\n  return a\n").return_value
            elif filename == "file2.py":
                return mock_open(read_data="def func2():\n  a = 1\n  return a\n").return_value
            return mock_open(read_data="").return_value
            
        mock_file.side_effect = mock_read
        findings = duplication.analyze()
        self.assertEqual(len(findings), 1)
        self.assertIn("Consider merging", findings[0].message)

    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_cloud_cost(self, mock_file, mock_glob):
        from src.ciforge import cloud_cost
        mock_glob.return_value = ["main.tf"]
        mock_file.return_value = mock_open(read_data='resource "aws_instance" "app" {}\nresource "aws_db_instance" "db" {}').return_value
        
        findings = cloud_cost.analyze()
        self.assertEqual(len(findings), 3)

    @patch("urllib.request.urlopen")
    def test_load_test(self, mock_urlopen):
        from src.ciforge import load_test
        with patch("src.ciforge.load_test.fetch", return_value=(2.0, None)):
            findings = load_test.analyze("http://example.com")
            self.assertEqual(len(findings), 1)
            self.assertIn("Load Test Failed", findings[0].message)

    @patch("os.environ.get")
    @patch("urllib.request.urlopen")
    def test_telemetry_report_crash(self, mock_urlopen, mock_env_get):
        from src.ciforge import telemetry
        import json
        
        def mock_env(key, default=None):
            if key == "CIFORGE_CRASH_WEBHOOK":
                return "http://crash.webhook"
            return default
        mock_env_get.side_effect = mock_env
        
        try:
            1 / 0
        except Exception as e:
            telemetry.report_crash(e, "test_module")
            
        self.assertTrue(mock_urlopen.called)
        request = mock_urlopen.call_args[0][0]
        data = json.loads(request.data.decode("utf-8"))
        self.assertEqual(data["module_name"], "test_module")
        self.assertEqual(data["exception_type"], "ZeroDivisionError")

    @patch("os.environ.get")
    @patch("urllib.request.urlopen")
    def test_telemetry_report_ai_finding(self, mock_urlopen, mock_env_get):
        from src.ciforge import telemetry
        import json
        
        def mock_env(key, default=None):
            if key == "CIFORGE_AI_WEBHOOK":
                return "http://ai.webhook"
            return default
        mock_env_get.side_effect = mock_env
        
        telemetry.report_ai_finding("Test finding")
        
        self.assertTrue(mock_urlopen.called)
        request = mock_urlopen.call_args[0][0]
        data = json.loads(request.data.decode("utf-8"))
        self.assertEqual(data["finding_message"], "Test finding")

    @patch("sys.stdout")
    def test_mcp_server_initialize(self, mock_stdout):
        from src.ciforge import mcp_server
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        resp = mcp_server.handle_request(req)
        self.assertIn("serverInfo", resp)
        self.assertEqual(resp["serverInfo"]["name"], "ciforge")

    @patch("subprocess.run")
    @patch("src.ciforge.auto_fixer.call_llm_for_fixes")
    def test_auto_fixer(self, mock_call_llm, mock_run):
        from src.ciforge import auto_fixer
        from src.ciforge.scanner import Finding
        import os, tempfile
        
        mock_call_llm.return_value = [{"file": "test_auto.py", "content": "print('fixed')"}]
        mock_run.return_value.stdout = "git@github.com:test/repo.git\n"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with open("test_auto.py", "w") as f:
                    f.write("print('bug')")
                    
                finding = Finding("test_auto.py", 1, "bug", "low")
                auto_fixer.run_agentic_fixes([finding], tmpdir)
                
                with open("test_auto.py", "r") as f:
                    content = f.read()
                self.assertEqual(content, "print('fixed')")
            finally:
                os.chdir(orig_cwd)

    @patch("src.ciforge.auto_update.get_latest_pypi_version")
    def test_auto_update_requirements(self, mock_pypi):
        from src.ciforge import auto_update
        import os, tempfile
        
        mock_pypi.return_value = "2.0.0"
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with open("requirements.txt", "w") as f:
                    f.write("requests==1.0.0\n")
                    
                auto_update.update_dependencies(tmpdir)
                
                with open("requirements.txt", "r") as f:
                    content = f.read()
                self.assertEqual(content, "requests==2.0.0\n")
            finally:
                os.chdir(orig_cwd)

    def test_incremental_scanner_get_all_files(self):
        from src.ciforge import scanner
        import os, tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("x = 1")
            
            os.mkdir(os.path.join(tmpdir, ".git"))
            with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
                f.write("something")
                
            files = scanner.get_all_files(tmpdir)
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0], "test.py")
    def test_v61_dead_code_dunder_and_fixtures(self):
        import os, tempfile
        from src.ciforge import dead_code
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Dunder method, fixture, and normal orphaned func
                with open("module_a.py", "w") as f:
                    f.write('''
import pytest

def __dunder_method__():
    pass

@pytest.fixture
def my_fixture():
    pass

@pytest.fixture()
def my_fixture2():
    pass

def orphaned_func():
    pass
''')
                # Test files should be ignored
                os.mkdir("tests")
                with open("tests/test_foo.py", "w") as f:
                    f.write("def orphaned_test_func():\n    pass\n")
                    
                import importlib
                importlib.reload(dead_code)
                findings = dead_code.analyze()
                messages = [f.message for f in findings]
                
                self.assertTrue(any("orphaned_func" in m for m in messages))
                self.assertFalse(any("__dunder_method__" in m for m in messages))
                self.assertFalse(any("my_fixture" in m for m in messages))
                self.assertFalse(any("my_fixture2" in m for m in messages))
                self.assertFalse(any("orphaned_test_func" in m for m in messages))
            finally:
                os.chdir(orig_cwd)

    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_v61_duplication_abstract(self, mock_file, mock_glob):
        from src.ciforge import duplication
        mock_glob.return_value = ["file1.py", "file2.py"]
        
        # Test for small functions and NotImplementedError skipping
        def mock_read(filename, *args, **kwargs):
            if filename == "file1.py":
                return mock_open(read_data='''
def small1():
    pass
def small2():
    return True
def notimpl1():
    raise NotImplementedError
def notimpl2():
    raise NotImplementedError()
def notimpl3():
    """Docstring"""
    pass
def real_func():
    a = 1
    b = 2
    return a + b
''').return_value
            elif filename == "file2.py":
                return mock_open(read_data='''
def small1_dup():
    pass
def small2_dup():
    return True
def notimpl1_dup():
    raise NotImplementedError
def notimpl2_dup():
    raise NotImplementedError()
def notimpl3_dup():
    """Docstring 2"""
    pass
def real_func_dup():
    a = 1
    b = 2
    return a + b
''').return_value
            return mock_open(read_data="").return_value
            
        mock_file.side_effect = mock_read
        findings = duplication.analyze()
        messages = [f.message for f in findings]
        
        self.assertEqual(len(messages), 1)
        self.assertTrue("real_func" in messages[0])

if __name__ == '__main__':
    unittest.main()
