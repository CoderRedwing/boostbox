import customtkinter as ctk
from ui.dashboard import Dashboard
import platform

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("💻 PC Cleaner")
    app.geometry("1000x600")

    # Maximize safely across platforms
    if platform.system() == "Windows":
        app.state("zoomed")
    else:
        app.attributes("-zoomed", True)

    Dashboard(app)
    app.mainloop()

if __name__ == "__main__":
    main()
