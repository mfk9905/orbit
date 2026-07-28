"""
Service for detecting currently active foreground window and application executable name.
Cross-platform support for Windows, Linux, and macOS.
"""

import os
import sys
import ctypes
from typing import Tuple
from app.core.logging.logger import get_logger

logger = get_logger("orbit.services.active_window")


class ActiveWindowService:
    """Detects active foreground window process executable name and title."""

    @staticmethod
    def get_active_window_info() -> Tuple[str, str]:
        """
        Returns a tuple of (executable_name, window_title).
        executable_name is lowercased, e.g. ('code.exe', 'main.py - Visual Studio Code').
        """
        if sys.platform == "win32":
            return ActiveWindowService._get_win32_window_info()
        elif sys.platform.startswith("linux"):
            return ActiveWindowService._get_linux_window_info()
        elif sys.platform == "darwin":
            return ActiveWindowService._get_mac_window_info()
        return "", ""

    @staticmethod
    def get_active_executable() -> str:
        """Returns lowercased executable name of active window (e.g. 'code.exe')."""
        exe, _ = ActiveWindowService.get_active_window_info()
        return exe

    @staticmethod
    def _get_win32_window_info() -> Tuple[str, str]:
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", ""

            # Get Window Title
            length = user32.GetWindowTextLengthW(hwnd)
            title_buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buf, length + 1)
            window_title = title_buf.value

            # Get Process ID
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                return "", window_title

            # Open Process with PROCESS_QUERY_LIMITED_INFORMATION (0x1000)
            h_process = kernel32.OpenProcess(0x1000, False, pid.value)
            if not h_process:
                return "", window_title

            buf_size = ctypes.c_ulong(1024)
            buf = ctypes.create_unicode_buffer(1024)
            success = kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size))
            kernel32.CloseHandle(h_process)

            if success and buf.value:
                exe_name = os.path.basename(buf.value).lower()
                return exe_name, window_title

            return "", window_title
        except Exception as e:
            logger.debug(f"Win32 get active window error: {e}")
            return "", ""

    @staticmethod
    def get_open_windows() -> list:
        """
        Returns a list of tuples: [(hwnd, exe_name, window_title), ...]
        Enumerates visible main desktop windows.
        """
        if sys.platform != "win32":
            return []

        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            current_pid = os.getpid()
            results = []

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def enum_cb(hwnd, lparam):
                if not user32.IsWindowVisible(hwnd):
                    return True

                ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                # Ignore WS_EX_TOOLWINDOW unless WS_EX_APPWINDOW is set
                if (ex_style & 0x00000080) and not (ex_style & 0x00040000):
                    return True

                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0:
                    return True

                title_buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title_buf, length + 1)
                title = title_buf.value.strip()

                if not title or title in ("Program Manager", "Settings", "NVIDIA GeForce Overlay", "MSCTFIME UI"):
                    return True

                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == current_pid:
                    return True  # Skip Orbit's own windows

                exe_name = ""
                h_process = kernel32.OpenProcess(0x1000, False, pid.value)
                if h_process:
                    buf_size = ctypes.c_ulong(1024)
                    buf = ctypes.create_unicode_buffer(1024)
                    if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size)):
                        exe_name = os.path.basename(buf.value).lower()
                    kernel32.CloseHandle(h_process)

                results.append((int(hwnd), exe_name, title))
                return True

            cb = WNDENUMPROC(enum_cb)
            user32.EnumWindows(cb, 0)
            return results
        except Exception as e:
            logger.error(f"Error enumerating open windows: {e}")
            return []

    @staticmethod
    def activate_window(hwnd: int) -> bool:
        """Restores and brings target window handle (hwnd) to the foreground."""
        if sys.platform != "win32" or not hwnd:
            return False

        try:
            user32 = ctypes.windll.user32
            # If window is minimized (IsIconic), restore it (SW_RESTORE = 9)
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)

            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            logger.info(f"Successfully activated window handle: {hwnd}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate window handle {hwnd}: {e}")
            return False
