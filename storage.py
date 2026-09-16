"""Local daily totals; no titles, keystrokes or network traffic."""
import sqlite3
from datetime import datetime, timedelta


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS usage(day TEXT, app TEXT, seconds REAL, PRIMARY KEY(day, app))')
        self.db.commit()

    def add(self, start, end, app):
        if not app or end <= start:
            return
        with self.db:
            while start < end:
                midnight = datetime.combine(start.date() + timedelta(days=1), datetime.min.time())
                stop = min(end, midnight)
                self.db.execute('INSERT INTO usage VALUES(?,?,?) ON CONFLICT(day,app) DO UPDATE SET seconds=seconds+excluded.seconds',
                                (start.date().isoformat(), app, (stop-start).total_seconds()))
                start = stop

    def rows(self, day):
        return self.db.execute('SELECT app,seconds FROM usage WHERE day=? ORDER BY seconds DESC,app', (day,)).fetchall()

    def close(self):
        self.db.close()


def credit(store, start, end, elapsed, previous_app, current_app, idle, paused):
    # Discard sleep / delayed callbacks / clock changes and app transitions.
    wall = (end-start).total_seconds()
    if paused or idle >= 300 or not previous_app or previous_app != current_app:
        return
    if 0 < elapsed <= 5 and abs(wall-elapsed) < 1:
        store.add(start, end, previous_app)
