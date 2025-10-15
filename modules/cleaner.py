# modules/cleaner.py
"""
Cleaner module: move files to Trash (safe) or permanently delete (with force).
Uses send2trash when available.

Usage:
    from modules.cleaner import Cleaner
    cleaner = Cleaner()
    deleted, errors = cleaner.clean_paths(list_of_paths, dry_run=True)
"""

import os

try:
    from send2trash import send2trash
    _HAS_SEND2TRASH = True
except Exception:
    _HAS_SEND2TRASH = False

class Cleaner:
    def __init__(self):
        self.use_trash = _HAS_SEND2TRASH

    def clean_paths(self, paths, dry_run=True, force=False):
        """
        Attempt to remove/move to trash the given paths.

        - dry_run=True: do not actually remove, just report would-be actions.
        - force=False: if send2trash unavailable, do not permanently delete; return errors instead.
                     set force=True to allow permanent deletes (use with caution).

        Returns: (results, errors)
            results: list of (path, action) where action is "trashed"|"deleted"|"skipped"
            errors: list of (path, error_message)
        """
        results = []
        errors = []

        for p in paths:
            try:
                if not os.path.exists(p):
                    errors.append((p, "NotFound"))
                    continue

                if dry_run:
                    # don't perform, just report intent
                    action = "trashed" if self.use_trash else ("deleted" if force else "would_delete_but_no_trash")
                    results.append((p, action))
                    continue

                if self.use_trash:
                    send2trash(p)
                    results.append((p, "trashed"))
                else:
                    if force:
                        # permanent delete
                        if os.path.isdir(p):
                            # recursively delete dir
                            for root, dirs, files in os.walk(p, topdown=False):
                                for name in files:
                                    os.remove(os.path.join(root, name))
                                for name in dirs:
                                    os.rmdir(os.path.join(root, name))
                            os.rmdir(p)
                        else:
                            os.remove(p)
                        results.append((p, "deleted"))
                    else:
                        errors.append((p, "send2trash_not_available"))
            except Exception as e:
                errors.append((p, str(e)))

        return results, errors
