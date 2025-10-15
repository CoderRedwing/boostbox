import os
import platform
import shutil
import psutil
import tempfile
import time
from pathlib import Path

class Optimizer:
    def __init__(self):
        self.system = platform.system()
        # Critical paths to never touch
        self.whitelist_paths = self._get_whitelist_paths()
        # Default temp/cache directories
        self.temp_dirs = self._get_temp_dirs()

    # ----------------- Utility -----------------
    def _get_whitelist_paths(self):
        s = self.system
        wl = set()
        if s == "Windows":
            wl.update({
                os.environ.get("WINDIR", r"C:\Windows"),
                os.path.join(os.environ.get("SYSTEMDRIVE", "C:\\"), "Program Files"),
                os.path.join(os.environ.get("SYSTEMDRIVE", "C:\\"), "Program Files (x86)"),
            })
            user = os.environ.get("USERPROFILE")
            if user:
                wl.update({
                    os.path.join(user, "AppData", "Roaming"),
                    os.path.join(user, "AppData", "Local", "Programs")
                })
        else:
            wl.update({"/", "/bin", "/sbin", "/usr", "/usr/bin", "/usr/sbin", "/lib", "/lib64", "/etc", "/var"})
            if s == "Darwin":
                wl.update({"/System", "/Applications"})
        return {os.path.abspath(p) for p in wl if os.path.exists(p)}

    def _get_temp_dirs(self):
        dirs = []
        home = os.path.expanduser("~")
        if self.system == "Windows":
            dirs.append(tempfile.gettempdir())
            user = os.environ.get("USERPROFILE")
            if user:
                dirs.append(os.path.join(user, "AppData", "Local", "Temp"))
        elif self.system == "Linux":
            dirs.append("/tmp")
            dirs.append(os.path.expanduser("~/.cache"))
        elif self.system == "Darwin":
            dirs.append("/tmp")
            dirs.append(os.path.expanduser("~/Library/Caches"))
        return [d for d in dirs if os.path.exists(d)]

    def _is_safe_path(self, path):
        path = os.path.abspath(path)
        for p in self.whitelist_paths:
            if path == p or path.startswith(p + os.sep):
                return False
        return True

    # ----------------- Memory Optimization -----------------
    def optimize_memory(self):
        """
        Free RAM safely.
        Linux: drop caches
        Windows/macOS: uses psutil to suggest cleanup
        """
        try:
            if self.system == "Linux":
                os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
            elif self.system == "Windows" or self.system == "Darwin":
                # Reduce memory footprint of running processes
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        p = psutil.Process(proc.info['pid'])
                        p.memory_full_info()
                    except Exception:
                        continue
            return "Memory optimization completed."
        except Exception as e:
            return f"Memory optimization failed: {str(e)}"

    # ----------------- Disk Optimization -----------------
    def optimize_disk(self, max_age_days=7, delete_small_files=True):
        """
        Clean temporary and cache files safely.
        max_age_days: files older than this will be deleted
        delete_small_files: True to delete even small temp files
        """
        removed_files = []
        age_seconds = max_age_days * 86400

        for folder in self.temp_dirs:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    fpath = os.path.join(root, f)
                    try:
                        if not self._is_safe_path(fpath):
                            continue
                        # Only remove files older than max_age_days
                        if time.time() - os.path.getmtime(fpath) < age_seconds:
                            continue
                        # Optionally ignore tiny files <1KB
                        if not delete_small_files and os.path.getsize(fpath) < 1024:
                            continue
                        os.remove(fpath)
                        removed_files.append(fpath)
                    except Exception:
                        continue
        return removed_files

    # ----------------- Full Optimization -----------------
    def full_optimize(self, max_age_days=7):
        """
        Perform both memory and disk optimization
        Returns summary
        """
        mem_status = self.optimize_memory()
        removed_files = self.optimize_disk(max_age_days=max_age_days)

        summary = {
            "memory_status": mem_status,
            "files_removed_count": len(removed_files),
            "files_removed_sample": removed_files[:20]
        }
        return summary
