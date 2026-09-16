"""AppTime: a small, offline Windows application usage tracker."""
import csv
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from storage import Store, credit


def duration(seconds):
    seconds = int(seconds)
    return f'{seconds//3600} 小时 {seconds%3600//60} 分 {seconds%60} 秒'


class App:
    def __init__(self, root, store, tracker):
        self.root, self.store, self.tracker = root, store, tracker
        self.paused = False
        self.last_time, self.last_tick = datetime.now(), time.monotonic()
        self.last_app = None
        root.title('AppTime · 每日软件时长')
        root.geometry('820x600')
        root.minsize(680, 480)
        root.configure(bg='#f4f6fb')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', rowheight=34, font=('Microsoft YaHei UI', 10))
        style.configure('Treeview.Heading', font=('Microsoft YaHei UI', 10, 'bold'))
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='AppTime', font=('Segoe UI', 26, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='了解时间花在哪里 · 数据仅保存在你的电脑', font=('Microsoft YaHei UI', 10)).pack(anchor='w', pady=(0, 16))
        bar = ttk.Frame(frame)
        bar.pack(fill='x')
        self.day = tk.StringVar(value=datetime.now().date().isoformat())
        ttk.Label(bar, text='日期').pack(side='left')
        ttk.Entry(bar, textvariable=self.day, width=13).pack(side='left', padx=8)
        ttk.Button(bar, text='查看', command=self.refresh).pack(side='left')
        ttk.Button(bar, text='今天', command=self.today).pack(side='left', padx=6)
        self.pause_btn = ttk.Button(bar, text='暂停记录', command=self.toggle)
        self.pause_btn.pack(side='right')
        self.total = tk.StringVar()
        ttk.Label(frame, textvariable=self.total, font=('Microsoft YaHei UI', 18, 'bold')).pack(anchor='w', pady=18)
        table = ttk.Frame(frame)
        table.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(table, columns=('app', 'time', 'share'), show='headings')
        for key, title, width in [('app', '软件进程', 270), ('time', '使用时长', 210), ('share', '当日占比', 110)]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.status = tk.StringVar(value='正在启动记录…')
        ttk.Label(frame, textvariable=self.status).pack(anchor='w', pady=(14, 6))
        ttk.Label(frame, text='前台软件每秒采样 · 空闲 5 分钟暂停 · 最小化后继续记录，关闭后停止').pack(anchor='w')
        bottom = ttk.Frame(frame)
        bottom.pack(fill='x', pady=(12, 0))
        ttk.Button(bottom, text='导出当日 CSV', command=self.export).pack(side='left')
        ttk.Label(bottom, text='首次使用没有数据？切换到其他软件操作几秒即可。').pack(side='left', padx=12)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh()
        self.job = root.after(1000, self.tick)

    def today(self):
        self.day.set(datetime.now().date().isoformat())
        self.refresh()

    def refresh(self):
        try:
            datetime.strptime(self.day.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror('日期格式', '请输入 YYYY-MM-DD，例如 2026-09-17。')
            return
        rows = self.store.rows(self.day.get())
        total = sum(seconds for _, seconds in rows)
        self.total.set(f'当日累计  {duration(total)}')
        self.tree.delete(*self.tree.get_children())
        for app, seconds in rows:
            self.tree.insert('', 'end', values=(app, duration(seconds), f'{seconds/total:.1%}' if total else '0%'))

    def toggle(self):
        self.paused = not self.paused
        self.last_app = None
        self.pause_btn.configure(text='继续记录' if self.paused else '暂停记录')
        self.status.set('已手动暂停' if self.paused else '正在恢复记录…')

    def tick(self):
        now, tick = datetime.now(), time.monotonic()
        try:
            app, idle = self.tracker.sample()
            credit(self.store, self.last_time, now, tick-self.last_tick, self.last_app, app, idle, self.paused)
            self.last_app = app
            status = '已手动暂停' if self.paused else ('空闲中，暂停计时' if idle >= 300 else f'正在记录：{app}' if app else '等待可识别的前台软件（锁屏或受保护进程不记录）')
            self.status.set(status)
            # Refresh without validating partial date entry or showing popups every second.
            if len(self.day.get()) == 10:
                try:
                    datetime.strptime(self.day.get(), '%Y-%m-%d')
                except ValueError:
                    pass
                else:
                    self.refresh()
        except Exception as exc:
            self.paused = True
            self.last_app = None
            self.pause_btn.configure(text='继续记录')
            self.status.set(f'记录失败，已暂停：{exc}')
        finally:
            self.last_time, self.last_tick = now, tick
            self.job = self.root.after(1000, self.tick)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile=f'apptime-{self.day.get()}.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(['日期', '软件', '秒数', '时长'])
                for app, seconds in self.store.rows(self.day.get()):
                    safe_app = "'" + app if app.startswith(('=', '+', '-', '@')) else app
                    writer.writerow([self.day.get(), safe_app, round(seconds, 2), duration(seconds)])
            messagebox.showinfo('导出完成', f'已保存到：{path}')
        except OSError as exc:
            messagebox.showerror('导出失败', str(exc))

    def close(self):
        self.root.after_cancel(self.job)
        self.store.close()
        self.root.destroy()


def main():
    if sys.platform != 'win32':
        raise SystemExit('AppTime 的自动记录功能仅支持 Windows 10 / 11。')
    from win_tracker import WindowsTracker
    # Exclusive local socket avoids counting twice when opened twice. No server listens.
    guard = socket.socket()
    guard.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    root = tk.Tk()
    root.withdraw()
    try:
        guard.bind(('127.0.0.1', 47839))
    except OSError:
        messagebox.showerror('无法启动', 'AppTime 已运行，或本机端口 47839 被占用。请检查已打开的窗口。')
        root.destroy()
        guard.close()
        return
    folder = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'AppTime'
    try:
        folder.mkdir(parents=True, exist_ok=True)
        App(root, Store(folder / 'usage.db'), WindowsTracker())
        root.deiconify()
        root.mainloop()
    finally:
        guard.close()


if __name__ == '__main__':
    main()
