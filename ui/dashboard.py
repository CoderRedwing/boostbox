# ui/dashboard.py
import os
import platform
import psutil
import shutil
import customtkinter as ctk
from modules.scanner import Scanner
from modules.optimizer import Optimizer
from ui.components import ScrollableTextbox

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.scanner = Scanner()
        self.optimizer = Optimizer()
        self.create_ui()

    def create_ui(self):
        self.root.geometry("900x600")
        self.root.title("💻 PC Cleaner")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Title
        title = ctk.CTkLabel(
            self.root,
            text="💻 PC Cleaner",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=15)

        # Tabs
        self.tabs = ctk.CTkTabview(self.root, width=850, height=450)
        self.tabs.pack(pady=10)
        self.tab_system = self.tabs.add("System Info")
        self.tab_cleaner = self.tabs.add("Cleaner")
        self.tab_optimizer = self.tabs.add("Optimizer")

        # Add each tab UI
        self.setup_system_tab()
        self.setup_cleaner_tab()
        self.setup_optimizer_tab()

        # Footer
        footer = ctk.CTkLabel(
            self.root,
            text="© 2025 | Developed by Ajitesh Mishra",
            font=ctk.CTkFont(size=12)
        )
        footer.pack(side="bottom", pady=5)

    # ----------------- SYSTEM TAB -----------------
    def setup_system_tab(self):
        self.sys_log = ScrollableTextbox(self.tab_system)
        self.sys_log.update_text("Press 'Refresh Info' to load system info...")

        btn_frame = ctk.CTkFrame(self.tab_system)
        btn_frame.pack(pady=10)

        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="Refresh Info",
            width=140,
            command=self.show_system_info
        )
        refresh_btn.grid(row=0, column=0, padx=10)

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear Log",
            width=140,
            command=lambda: self.sys_log.update_text("")
        )
        clear_btn.grid(row=0, column=1, padx=10)

    def show_system_info(self):
        total, used, free = shutil.disk_usage("/")
        info = f"""
OS: {platform.system()} {platform.release()}
Processor: {platform.processor()}
CPU Cores: {psutil.cpu_count(logical=False)}
Logical CPUs: {psutil.cpu_count()}
RAM: {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB
Disk Total: {round(total / (1024 ** 3), 2)} GB
Disk Used: {round(used / (1024 ** 3), 2)} GB
Disk Free: {round(free / (1024 ** 3), 2)} GB
"""
        self.sys_log.update_text(info.strip())

    # ----------------- CLEANER TAB -----------------
    def setup_cleaner_tab(self):
        self.cleaner_log = ScrollableTextbox(self.tab_cleaner)
        self.cleaner_log.update_text("Press 'Scan' to detect junk files...")

        btn_frame = ctk.CTkFrame(self.tab_cleaner)
        btn_frame.pack(pady=10)

        scan_btn = ctk.CTkButton(
            btn_frame,
            text="Scan Files",
            width=140,
            command=self.scan_files
        )
        scan_btn.grid(row=0, column=0, padx=10)

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear Junk Files",
            width=140,
            command=self.clear_junk_files
        )
        clear_btn.grid(row=0, column=1, padx=10)

    def scan_files(self):
        self.cleaner_log.update_text("Scanning for junk files...")
        self.root.update()

        summary = self.scanner.scan_all(
            age_seconds=84600,
            size_threshold_bytes=1,
            include_downloads=True,
            include_browser_cache=True,
            dry_run=True
        )
        self.scanner.last_scan = summary

        text = f"Scan Completed!\nTotal Files: {summary['total_files']}\n"
        text += f"Junk Files Found: {summary['counts'].get('junk', 0)}\n"
        junk_files = summary['lists'].get('junk', [])
        if junk_files:
            text += "\nSample Junk Files:\n" + "\n".join(junk_files[:10])

        self.cleaner_log.update_text(text)

    def clear_junk_files(self):
        self.cleaner_log.update_text("Deleting junk files...")
        self.root.update()

        summary = getattr(self.scanner, "last_scan", None)
        if not summary or not summary['lists'].get('junk'):
            self.cleaner_log.update_text("No junk files found. Scan first.")
            return

        junk_files = summary['lists']['junk']
        deleted_files = []

        for f in junk_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    deleted_files.append(f)
            except Exception:
                continue

        text = f"Deleted {len(deleted_files)} junk files successfully!\n"
        if deleted_files:
            text += "Sample Deleted Files:\n" + "\n".join(deleted_files[:10])

        self.cleaner_log.update_text(text)

    # ----------------- OPTIMIZER TAB -----------------
    def setup_optimizer_tab(self):
        self.optimizer_log = ScrollableTextbox(self.tab_optimizer)
        self.optimizer_log.update_text("Press 'Optimize Memory' or 'Optimize Disk'...")

        btn_frame = ctk.CTkFrame(self.tab_optimizer)
        btn_frame.pack(pady=10)

        mem_btn = ctk.CTkButton(
            btn_frame,
            text="Optimize Memory",
            width=140,
            command=self.optimize_memory
        )
        mem_btn.grid(row=0, column=0, padx=10)

        disk_btn = ctk.CTkButton(
            btn_frame,
            text="Optimize Disk",
            width=140,
            command=self.optimize_disk
        )
        disk_btn.grid(row=0, column=1, padx=10)

    # ----------------- OPTIMIZER FUNCTIONS -----------------
    def optimize_memory(self):
        self.optimizer_log.update_text("Optimizing memory...")
        self.root.update()
        result = self.optimizer.optimize_memory()
        self.optimizer_log.update_text(result)

    def optimize_disk(self):
        self.optimizer_log.update_text("Optimizing disk...")
        self.root.update()
        removed = self.optimizer.optimize_disk()
        text = f"Disk Optimization Completed!\nFiles Removed: {len(removed)}"
        if removed:
            text += "\nSample Removed Files:\n" + "\n".join(removed[:10])
        self.optimizer_log.update_text(text)
