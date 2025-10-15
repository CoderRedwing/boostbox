## 🟢 STEP 1 — Open Command Prompt or PowerShell

## 🟢 STEP 2 — Clone the GitHub project

If your project is on GitHub:

```powershell
git clone https://github.com/yourusername/pc_cleaner.git
cd pc_cleaner
```

> Replace `yourusername` with the actual GitHub username.
> This will create a folder like `C:\Users\<You>\Desktop\pc_cleaner`.

If project is **on another PC / local folder**, either:

1. **Copy the folder** via USB / shared network drive, OR
2. Use **ZIP → Extract** to Desktop.

---

## 🟢 STEP 3 — Create & activate Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

> You’ll see `(venv)` appear in front of the prompt.

---

## 🟢 STEP 4 — Install dependencies

```powershell
pip install -r requirements.txt
```

> Make sure `requirements.txt` exists in the project folder.

---

## 🟢 STEP 5 — Run the app

```powershell
python main.py
```

✅ The **PC Cleaner GUI** should open immediately.

---

## 🟢 Optional: Build a standalone `.exe`

Once everything works, Windows users can make a single executable:

```powershell
pyinstaller --onefile --noconsole --icon=assets/app.ico --name "PCCleaner" main.py
```

_Output will be in `dist\PCCleaner.exe`._
