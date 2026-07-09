import unittest
from unittest.mock import patch, mock_open

from src.ciforge.scanner import Finding, _extract_diff_sections
from src.ciforge import code_quality, secrets, config_validator, coverage

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
        diff = "@@ -0,0 +1,1 @@\n+my_var = 'AKIAIOSFODNN7EXAMPLE'\n"
        findings = secrets.analyze("config.py", diff)
        self.assertEqual(len(findings), 1)
        self.assertTrue("aws_key" in findings[0].message)
        self.assertEqual(findings[0].severity, "critical")

        diff2 = "@@ -0,0 +1,1 @@\n+my_token_var = 'ghp_123456789012345678901234567890123456'\n"
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

    @patch("os.path.exists", return_value=True)
    def test_coverage(self, mock_exists):
        with patch("builtins.open", mock_open(read_data='{"coverage": 75.0}')):
            findings = coverage.analyze()
            self.assertEqual(len(findings), 1)
            self.assertTrue("Code coverage too low" in findings[0].message)
            self.assertEqual(findings[0].severity, "medium")

if __name__ == '__main__':
    unittest.main()
