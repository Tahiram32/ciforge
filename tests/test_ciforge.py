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

if __name__ == '__main__':
    unittest.main()

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
