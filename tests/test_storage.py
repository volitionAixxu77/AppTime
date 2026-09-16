import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from storage import Store, credit


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.gettempdir()) / f'apptime-test-{uuid.uuid4().hex}.db'
        self.store = Store(self.path)
        self.start = datetime(2026, 9, 16, 23, 59, 59)

    def tearDown(self):
        self.store.close()
        self.path.unlink(missing_ok=True)

    def test_midnight_and_persistence(self):
        self.store.add(self.start, self.start + timedelta(seconds=3), 'editor.exe')
        self.assertEqual(self.store.rows('2026-09-16'), [('editor.exe', 1.0)])
        self.assertEqual(self.store.rows('2026-09-17'), [('editor.exe', 2.0)])
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.rows('2026-09-17'), [('editor.exe', 2.0)])

    def test_accumulates_and_sorts(self):
        for app, seconds in [('a.exe', 1), ('b.exe', 3), ('a.exe', 1)]:
            self.store.add(datetime(2026, 9, 16), datetime(2026, 9, 16) + timedelta(seconds=seconds), app)
        self.assertEqual(self.store.rows('2026-09-16'), [('b.exe', 3.0), ('a.exe', 2.0)])

    def test_active_sample(self):
        credit(self.store, self.start, self.start+timedelta(seconds=1), 1, 'a', 'a', 0, False)
        self.assertEqual(self.store.rows('2026-09-16'), [('a', 1.0)])

    def test_no_false_credit(self):
        for elapsed, previous, current, idle, paused in [
            (1, 'a', 'a', 300, False), (1, 'a', 'a', 0, True),
            (1, 'a', 'b', 0, False), (1, None, 'a', 0, False),
            (600, 'a', 'a', 0, False), (1, 'a', None, 0, False)]:
            credit(self.store, self.start, self.start+timedelta(seconds=elapsed), elapsed, previous, current, idle, paused)
        self.assertEqual(self.store.rows('2026-09-16'), [])

    def test_clock_jump(self):
        credit(self.store, self.start, self.start+timedelta(hours=1), 1, 'a', 'a', 0, False)
        self.assertEqual(self.store.rows('2026-09-16'), [])


if __name__ == '__main__':
    unittest.main()
