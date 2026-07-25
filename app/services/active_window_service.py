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
    def _get_linux_window_info() -> Tuple[str, str]:
        try:
            import subprocess
            pid_out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowpid"], stderr=subprocess.DEVNULL).strip()
            pid = int(pid_out)
            exe_path = os.readlink(f"/proc/{pid}/exe")
            exe_name = os.path.basename(exe_path).lower()

            title_out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowname"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore").strip()
            return exe_name, title_out
        except Exception:
            return "", ""

    @staticmethod
    def _get_mac_window_info() -> Tuple[str, str]:
        try:
            from AppKit import NSWorkspace
            curr_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if curr_app:
                name = curr_app.localizedName() or ""
                return name.lower(), name
            return "", ""
        except Exception:
            return "", ""
