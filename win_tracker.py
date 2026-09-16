"""Windows foreground process and idle time via documented Win32 APIs."""
import ctypes
import ntpath
from ctypes import wintypes as W


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [('cbSize', W.UINT), ('dwTime', W.DWORD)]


class WindowsTracker:
    def __init__(self):
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.user.GetForegroundWindow.restype = W.HWND
        self.user.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
        self.user.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
        self.kernel.GetTickCount.restype = W.DWORD
        self.kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        self.kernel.OpenProcess.restype = W.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
        self.kernel.CloseHandle.argtypes = [W.HANDLE]
        self.user.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        self.user.OpenInputDesktop.restype = W.HANDLE
        self.user.CloseDesktop.argtypes = [W.HANDLE]

    def sample(self):
        info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
        if not self.user.GetLastInputInfo(ctypes.byref(info)):
            return None, 300
        idle = ((self.kernel.GetTickCount() - info.dwTime) & 0xffffffff) / 1000
        desktop = self.user.OpenInputDesktop(0, False, 0x0100)
        if not desktop:
            return None, idle
        self.user.CloseDesktop(desktop)
        window = self.user.GetForegroundWindow()
        if not window:
            return None, idle
        pid = W.DWORD()
        self.user.GetWindowThreadProcessId(window, ctypes.byref(pid))
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return None, idle
        try:
            size = W.DWORD(32768)
            name = ctypes.create_unicode_buffer(size.value)
            if self.kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
                app = ntpath.basename(name.value).lower()
                if app not in {'lockapp.exe', 'logonui.exe'}:
                    return app, idle
            return None, idle
        finally:
            self.kernel.CloseHandle(handle)
