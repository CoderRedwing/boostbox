# ui/components.py
import customtkinter as ctk

class ScrollableTextbox(ctk.CTkTextbox):
    """
    Custom scrollable textbox for displaying logs or junk files.
    """
    def __init__(self, master, width=600, height=250):
        super().__init__(master, width=width, height=height)
        self.configure(state="normal")
        self.pack(pady=10, padx=20)

    def update_text(self, text):
        """
        Clear and update textbox content safely.
        """
        self.configure(state="normal")
        self.delete("0.0", "end")
        self.insert("0.0", text)
        self.configure(state="disabled")
