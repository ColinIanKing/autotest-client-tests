#!/usr/bin/python3
import os
import re
import shutil
import subprocess
import unittest


class TestRevocationList(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = "/boot/config-" + os.uname()[2]
        revocation_list_available = False
        with open(config_file) as f:
            for line in f:
                if re.search("CONFIG_SYSTEM_REVOCATION_KEYS", line):
                    revocation_list_available = True
                    break
        if not revocation_list_available:
            raise unittest.SkipTest("CONFIG_SYSTEM_REVOCATION_KEYS not available")

        if not shutil.which("keyctl"):
            raise unittest.SkipTest("keyutils not installed")

    def test_revocations(self):
        revocations = subprocess.check_output(
            ["keyctl", "list", "%:.blacklist"], universal_newlines=True
        )
        patterns = [
            ".* asymmetric: Canonical Ltd. Secure Boot Signing: 61482aa2830d0ab2ad5af10b7250da9033ddcef0",
        ]
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNotNone(re.search(pattern, revocations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
