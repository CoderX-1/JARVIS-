import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from created_files import (CreatedFileError, list_created_files,
                           recycle_created_file, resolve_created_file)


class CreatedFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reports = self.root / "output" / "reports"
        self.decks = self.root / "output" / "presentations"
        self.reports.mkdir(parents=True)
        self.decks.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_lists_both_shelves_but_not_other_files(self):
        (self.reports / "brief.pdf").write_bytes(b"pdf")
        (self.decks / "talk.pptx").write_bytes(b"pptx")
        (self.decks / "notes.txt").write_text("private", encoding="utf-8")
        ids = {item["id"] for item in list_created_files(self.root)}
        self.assertEqual(ids, {"reports/brief.pdf", "presentations/talk.pptx"})

    def test_rejects_traversal_stale_version_and_unsupported_file(self):
        (self.reports / "brief.pdf").write_bytes(b"pdf")
        (self.reports / "private.txt").write_text("private", encoding="utf-8")
        for file_id in ("reports/../brief.pdf", "reports/brief.pdf/extra", "reports\\brief.pdf",
                        "reports/private.txt", "other/brief.pdf"):
            with self.subTest(file_id=file_id), self.assertRaises(CreatedFileError):
                resolve_created_file(self.root, file_id)
        with self.assertRaises(CreatedFileError):
            recycle_created_file(self.root, "reports/brief.pdf", "stale")
        self.assertTrue((self.reports / "brief.pdf").exists())

    def test_recycle_calls_only_exact_versioned_file(self):
        path = self.decks / "demo.pptx"
        path.write_bytes(b"deck")
        item = list_created_files(self.root)[0]
        with patch("created_files._send_to_recycle_bin", side_effect=lambda target: target.unlink()) as recycle:
            result = recycle_created_file(self.root, item["id"], item["version"])
        recycle.assert_called_once_with(path)
        self.assertTrue(result["recycled"])
        self.assertFalse(path.exists())

    def test_symlink_is_never_listed_or_recycled(self):
        target = self.root / "private.pdf"
        target.write_bytes(b"private")
        link = self.reports / "linked.pdf"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink privilege unavailable")
        self.assertEqual(list_created_files(self.root), [])
        with self.assertRaises(CreatedFileError):
            resolve_created_file(self.root, "reports/linked.pdf")

    @unittest.skipUnless(os.name == "nt" and os.environ.get("JARVIS_TEST_WINDOWS_RECYCLE") == "1",
                         "opt-in Windows Recycle Bin fixture")
    def test_actual_windows_recycle_bin_with_disposable_fixture(self):
        path = self.reports / "jarvis-recycle-smoke.pdf"
        path.write_bytes(b"disposable test fixture")
        item = list_created_files(self.root)[0]
        result = recycle_created_file(self.root, item["id"], item["version"])
        self.assertTrue(result["recycled"])
        self.assertFalse(path.exists())
