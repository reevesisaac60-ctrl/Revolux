import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bootstrap"))
import host_check

class HostCheckTest(unittest.TestCase):
    def setUp(self):
        self.host_patches = [
            patch.object(host_check.platform, "system", return_value="Linux"),
            patch.object(host_check.platform, "release", return_value="test-kernel"),
            patch.object(host_check.platform, "machine", return_value="x86_64"),
            patch.object(host_check.platform, "python_version", return_value="3.14.7"),
            patch.object(host_check.platform, "python_version_tuple", return_value=("3", "14", "7")),
            patch.object(host_check.os, "cpu_count", return_value=12)
        ]
        
        for patcher in self.host_patches:
            patcher.start()
            self.addCleanup(patcher.stop)
    
    def test_ready_when_all_required_tools_are_present(self):
        tools = [{"gcc": {"available": True}}, {"git": {"available": True}}]

        with patch.object(host_check, "inspect_tools", side_effect=tools):
            report = host_check.run_check()

        self.assertTrue(report["ready_for_next_stage"])
        self.assertEqual(report["missing_required"], [])
        self.assertEqual(report["host"]["architecture"], "x86_64")
    
    def test_not_ready_when_a_required_tool_is_missing(self):
        tools = [{"gcc": {"available": True}, "bison": {"available": False}}, {"git": {"available": True}}]

        with patch.object(host_check, "inspect_tools", side_effect=tools):
            report = host_check.run_check()
        
        self.assertFalse(report["ready_for_next_stage"])
        self.assertEqual(report["missing_required"], ["bison"])
    
    def test_not_ready_when_python_is_too_old(self):
        with patch.object(host_check.platform, "python_version_tuple", return_value=("3", "9", "0")):
            tools = [{"gcc": {"available": True}}, {"git": {"available": True}}]
            with patch.object(host_check, "inspect_tools", side_effect=tools):
                report = host_check.run_check()
            
        self.assertFalse(report["host"]["python_supported"])
        self.assertFalse(report["ready_for_next_stage"])

if __name__ == "__main__":
    unittest.main()
