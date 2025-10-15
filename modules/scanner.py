import os
import platform
import tempfile
import time
from pathlib import Path

class Scanner:
    def __init__(self, extra_dirs=None):
        self.system = platform.system()
        self.extra_dirs = extra_dirs or []
        self.junk_extensions = {
            ".tmp", ".log", ".bak", ".old", ".crdownload", ".part", ".cache",
            ".swp", ".~", ".trashinfo"
        }
        # Extensions that could be potentially harmful when present in Downloads / temp
        self.potentially_dangerous_extensions = {
            ".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".scr", ".jar", ".apk", ".dmg", ".pkg"
        }
        # Suspicious script extensions on Unix
        self.suspicious_script_extensions = {".sh", ".py", ".pl", ".rb"}
        # Set up default folders to scan per-OS
        self.temp_dirs = self._get_temp_dirs()
        self.browser_cache_dirs = self._get_browser_cache_dirs()
        self.download_dirs = self._get_download_dirs()
        # Critical/system paths to never touch
        self.whitelist_paths = self._get_whitelist_paths()

        # internal last-scan list
        self._found = {
            "junk": [],
            "large": [],
            "suspicious": [],
            "harmful": [],
            "skipped": []  # files skipped due to whitelist or protection
        }

    def _get_temp_dirs(self):
        s = self.system
        dirs = []
        try:
            if s == "Windows":
                dirs.append(tempfile.gettempdir())
                windir = os.environ.get("WINDIR", r"C:\Windows")
                dirs.append(os.path.join(windir, "Temp"))
                user = os.environ.get("USERPROFILE")
                if user:
                    dirs.append(os.path.join(user, "AppData", "Local", "Temp"))
            elif s == "Linux":
                dirs.append("/tmp")
                dirs.append(os.path.expanduser("~/.cache"))
            elif s == "Darwin":  # macOS
                dirs.append("/tmp")
                dirs.append(os.path.expanduser("~/Library/Caches"))
        except Exception:
            # fallback
            dirs.append(tempfile.gettempdir())
        # add user-provided extra dirs
        dirs.extend(self.extra_dirs)
        # filter out non-existing
        return [d for d in dirs if os.path.exists(d)]

    def _get_browser_cache_dirs(self):
        s = self.system
        dirs = []
        home = os.path.expanduser("~")
        if s == "Windows":
            local = os.environ.get("LOCALAPPDATA")
            if local:
                # Chrome, Edge, Firefox typical locations (may vary per install)
                dirs += [
                    os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache"),
                    os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
                    os.path.join(local, "Mozilla", "Firefox", "Profiles")
                ]
        elif s == "Linux":
            dirs += [
                os.path.join(home, ".cache", "google-chrome"),
                os.path.join(home, ".cache", "chromium"),
                os.path.join(home, ".cache", "mozilla")
            ]
        elif s == "Darwin":
            dirs += [
                os.path.join(home, "Library", "Caches", "Google", "Chrome"),
                os.path.join(home, "Library", "Caches", "Firefox")
            ]
        return [d for d in dirs if os.path.exists(d)]

    def _get_download_dirs(self):
        s = self.system
        home = os.path.expanduser("~")
        candidates = []
        if s == "Windows":
            user = os.environ.get("USERPROFILE")
            if user:
                candidates.append(os.path.join(user, "Downloads"))
        else:
            candidates.append(os.path.join(home, "Downloads"))
        return [c for c in candidates if os.path.exists(c)]

    def _get_whitelist_paths(self):
        """
        Returns a list of folders/paths that MUST NEVER be deleted or scanned as deletable junk.
        Add common system paths and program folders.
        """
        s = self.system
        wl = set()
        if s == "Windows":
            # Windows system folders and Program Files
            wl.update({
                os.environ.get("WINDIR", r"C:\Windows"),
                os.path.join(os.environ.get("SYSTEMDRIVE", "C:\\"), "Program Files"),
                os.path.join(os.environ.get("SYSTEMDRIVE", "C:\\"), "Program Files (x86)"),
            })
            user = os.environ.get("USERPROFILE")
            if user:
                # User profile root is safe for scanning but we will protect certain subfolders
                wl.update({
                    os.path.join(user, "AppData", "Roaming"),
                    os.path.join(user, "AppData", "Local", "Programs")
                })
        else:
            # Unix-like: protect root-level system dirs
            wl.update({
                "/", "/bin", "/sbin", "/usr", "/usr/bin", "/usr/sbin", "/lib", "/lib64", "/etc", "/var"
            })
            # macOS additional protections
            if s == "Darwin":
                wl.update({"/System", "/Applications"})
        return {os.path.abspath(p) for p in wl if p}

    def _is_under_whitelist(self, path):
        """
        True if path is inside any whitelist path; we skip any such file.
        """
        try:
            path = os.path.abspath(path)
            for p in self.whitelist_paths:
                # if path equals whitelist or is a descendant -> skip
                if path == p or path.startswith(p + os.sep):
                    return True
        except Exception:
            return True  # be conservative and skip if doubt
        return False

    def _classify_file(self, file_path, age_seconds, size_threshold_bytes):
        """
        Return category string: 'junk'|'large'|'suspicious'|'harmful'|'skip' or None
        """
        try:
            stat = os.stat(file_path)
            mtime = stat.st_mtime
            size = stat.st_size
        except Exception:
            return "skip"

        # Skip if in whitelist (never remove system files)
        if self._is_under_whitelist(file_path):
            return "skipped"

        # If file is recent, skip (we only remove older files by default)
        if age_seconds is not None and (time.time() - mtime) < age_seconds:
            return None

        suffix = Path(file_path).suffix.lower()

        # Potentially harmful: dangerous extension in Downloads or temp
        if suffix in self.potentially_dangerous_extensions:
            # If it's located in Downloads or temp -> mark harmful
            if any(os.path.commonpath([file_path, d]) == d for d in (self.download_dirs + self.temp_dirs)):
                return "harmful"
            else:
                # executable somewhere else -> be cautious and skip
                return "skipped"

        # Suspicious scripts (shell/python/perl) located in Downloads or temp
        if suffix in self.suspicious_script_extensions:
            if any(os.path.commonpath([file_path, d]) == d for d in (self.download_dirs + self.temp_dirs)):
                return "suspicious"
            else:
                return None

        # Junk by extension
        if suffix in self.junk_extensions:
            # Also ignore very small files below threshold
            if size_threshold_bytes and size < size_threshold_bytes:
                return None
            return "junk"

        # Large leftover files (installers/archives) - considered large if > 20 MB default
        if size_threshold_bytes and size >= max(size_threshold_bytes, 20 * 1024 * 1024):
            # If it's inside downloads or temp, probably leftover installer -> mark large
            if any(os.path.commonpath([file_path, d]) == d for d in (self.download_dirs + self.temp_dirs)):
                return "large"
            # If located in cache folders, treat as junk
            if any(os.path.commonpath([file_path, d]) == d for d in self.browser_cache_dirs):
                return "junk"

        return None

    def _walk_and_collect(self, folders, age_seconds, size_threshold_bytes, category_limits=None):
        """
        Walk folders and collect classified files. category_limits optional dict to limit how many per category to store.
        """
        if category_limits is None:
            category_limits = {}

        for folder in folders:
            if not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        cat = self._classify_file(file_path, age_seconds, size_threshold_bytes)
                    except Exception:
                        cat = "skipped"
                    if cat:
                        # apply per-category limit
                        if cat not in self._found:
                            self._found[cat] = []
                        if category_limits.get(cat) and len(self._found[cat]) >= category_limits[cat]:
                            # ignore storing beyond limit, but counts/size may still be calculated elsewhere
                            continue
                        self._found.setdefault(cat, []).append(file_path)

    def scan_all(
        self,
        age_seconds=86400,
        size_threshold_bytes=1024,
        include_downloads=False,
        include_browser_cache=True,
        extra_scan_dirs=None,
        category_limits=None,
        dry_run=True
    ):
        """
        Master scanning function.

        Returns a summary dict:
            {
                "counts": {"junk": n, "large": n, "suspicious": n, "harmful": n, "skipped": n},
                "sizes": {"junk": bytes, ...},
                "lists": {"junk": [paths...], ...},
                "scanned_folders": [...]
            }

        Important:
            - dry_run=True will not delete any file (just report).
            - include_downloads=False by default (safer).
            - include_browser_cache=True by default.
        """
        # reset
        self._found = {"junk": [], "large": [], "suspicious": [], "harmful": [], "skipped": []}
        scanned = []

        # build folder list
        folders = list(self.temp_dirs)
        if include_browser_cache:
            folders += self.browser_cache_dirs
        if include_downloads:
            folders += self.download_dirs
        if extra_scan_dirs:
            folders += extra_scan_dirs

        # dedupe & filter
        folders = [f for i, f in enumerate(dict.fromkeys(folders)) if os.path.exists(f)]

        # collect files (but limit storing per category, counts/sizes computed below)
        self._walk_and_collect(folders, age_seconds, size_threshold_bytes, category_limits=category_limits)
        scanned = folders

        # compute counts and sizes for categories (iterate the found lists)
        summary_counts = {}
        summary_sizes = {}
        summary_lists = {}
        for cat, files in self._found.items():
            count = 0
            size = 0
            for p in files:
                try:
                    count += 1
                    size += os.path.getsize(p)
                except Exception:
                    continue
            summary_counts[cat] = count
            summary_sizes[cat] = size
            summary_lists[cat] = files

        total_files = sum(summary_counts.get(k, 0) for k in summary_counts)
        total_size_bytes = sum(summary_sizes.get(k, 0) for k in summary_sizes)

        # human readable sizes
        def _human(b):
            for unit in ["B","KB","MB","GB","TB"]:
                if b < 1024:
                    return f"{round(b,2)} {unit}"
                b /= 1024
            return f"{round(b,2)} PB"

        summary = {
            "counts": summary_counts,
            "sizes": {k: _human(v) for k,v in summary_sizes.items()},
            "lists": summary_lists,
            "total_files": total_files,
            "total_size": _human(total_size_bytes),
            "scanned_folders": scanned,
            "dry_run": bool(dry_run),
            "notes": {
                "whitelist_paths": list(self.whitelist_paths),
                "download_dirs": self.download_dirs,
                "browser_cache_dirs": self.browser_cache_dirs
            }
        }
        return summary
