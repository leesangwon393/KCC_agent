from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import threading
import unittest

from agent_v5 import doc_text
from demo_v5 import Watcher
from lifecycle_v3 import Lifecycle


class DownloadTrackingTests(unittest.TestCase):
    def test_pdf_readable_without_external_pdf_tools(self):
        from reportlab.pdfgen import canvas
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'AWS application.pdf'
            pdf = canvas.Canvas(str(path)); pdf.drawString(30, 700, 'AWS application development'); pdf.save()
            with patch('subprocess.run', side_effect=AssertionError('No external PDF programs')):
                self.assertIn('AWS application development', doc_text(path))

    def test_existing_download_is_ingested_once_and_original_is_preserved(self):
        with TemporaryDirectory() as temp:
            base = Path(temp); root = base / 'workspace'; root.mkdir()
            inbox = base / 'Downloads'; inbox.mkdir()
            file = inbox / 'AWS application.pdf'; file.write_bytes(b'fixture bytes')
            demo = SimpleNamespace(root=root, lock=threading.Lock(), engine=lambda: Lifecycle(root), sources={}, save_sources=lambda: None)
            watcher = Watcher(demo, [], strict_inboxes=[str(inbox)], scan_existing=True)
            watcher.tick()  # first size observation
            with patch('demo_v5.where_froms', return_value=[]):
                watcher.tick()  # stable download is copied and fingerprinted
            self.assertTrue(file.exists())
            self.assertEqual((root / 'screenshots' / file.name).read_bytes(), b'fixture bytes')
            restarted = Watcher(demo, [], strict_inboxes=[str(inbox)], scan_existing=True)
            self.assertNotIn(file, [p for p, _ in restarted.candidates()])

    def test_manifest_access_waits_for_http_state_lock(self):
        with TemporaryDirectory() as temp:
            root = Path(temp); lock = threading.Lock(); touched = threading.Event()
            def engine():
                touched.set()
                return Lifecycle(root)
            demo = SimpleNamespace(root=root, lock=lock, engine=engine)
            watcher = Watcher(demo, [], scan_existing=True)
            with lock:
                worker = threading.Thread(target=watcher.tick); worker.start()
                self.assertFalse(touched.wait(.05))
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertTrue(touched.is_set())
