import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Public files must not reveal workstation paths; URLs remain valid."""
from pathlib import Path
import json
import tempfile
import unittest
from pcbtools.rules.repository import repository_api
_family = repository_api(resolve_project("ads8588s"))
path_lines = _family.path_lines
scan_file = _family.scan_file
portable_netlist_text = _family.portable_netlist_text


class PublicPathsTests(unittest.TestCase):
    def test_windows_paths_and_json_escapes_are_rejected(self):
        path = "Z:" + chr(92) + "private" + chr(92) + "python.exe"
        self.assertEqual(path_lines(path), [1])
        self.assertEqual(path_lines(json.dumps({"python": path})), [1])
        self.assertEqual(path_lines("Z:" + "/private/tool"), [1])

    def test_user_posix_paths_are_rejected(self):
        self.assertEqual(path_lines("/" + "Users/example/tool"), [1])
        self.assertEqual(path_lines("/" + "home/example/repo"), [1])

    def test_urls_and_portable_paths_are_allowed(self):
        self.assertEqual(path_lines("https://example.org/source\nhardware/project/sheet.kicad_sch\npython -X utf8 tools/check.py"), [])

    def test_only_line_numbers_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text("header\nZ:" + "/private/report\n", encoding="utf-8")
            self.assertEqual(scan_file(path), [2])

    def test_native_export_metadata_is_portable_without_changing_graph(self):
        source = "Z:" + "/private/project.kicad_sch"
        for text in (f'<export><design><source>{source}</source></design><nets/></export>',
                     f'(export (design (source "{source}")) (nets (net (name "GND"))))'):
            clean = portable_netlist_text(text, "hardware/project.kicad_sch")
            self.assertEqual(clean, text.replace(source, "hardware/project.kicad_sch"))
            self.assertEqual(path_lines(clean), [])

    def test_library_source_metadata_is_preserved(self):
        source = "Z:" + "/private/project.kicad_sch"
        for text in (f'<export><design><source>{source}</source></design><libsource><source>Device</source></libsource></export>',
                     f'(export (design (source "{source}")) (libpart (source "Device")))'):
            self.assertEqual(portable_netlist_text(text, "hardware/project.kicad_sch"),
                             text.replace(source, "hardware/project.kicad_sch"))

    def test_export_metadata_requires_relative_source_and_known_format(self):
        with self.assertRaises(ValueError):
            portable_netlist_text("unknown export", "hardware/project.kicad_sch")
        with self.assertRaises(ValueError):
            portable_netlist_text('<source>old</source>', "Z:" + "/private/project")

    def test_sensitive_environment_files_are_never_read(self):
        self.assertEqual(scan_file(Path(".env")), [])
        self.assertEqual(scan_file(Path(".env.local")), [])


if __name__ == "__main__":
    unittest.main()
