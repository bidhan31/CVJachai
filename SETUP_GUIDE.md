# CVJachai: Full VSCode Setup & Run Guide

This guide covers everything you need to set up and run the CVJachai project (Frontend + Backend) from scratch using VSCode on a Windows machine.

---

## 1. Prerequisites (What you need installed)

Before you begin, ensure you have the following installed:
1. **Python 3.13 (64-bit)**
   - If not installed, open PowerShell and run: `winget install Python.Python.3.13`
2. **Node.js (LTS version)**
   - If not installed, open PowerShell and run: `winget install OpenJS.NodeJS.LTS`
   - *Note: After installing Node.js, you MUST restart VSCode so your terminal recognizes the `npm` command.*

---

## 2. Fix Windows Terminal Permissions (One-time setup)

By default, Windows blocks Python virtual environments from running in VSCode. To fix this permanently:

1. Open a **new** PowerShell terminal (or open one in VSCode).
2. Run this exact command:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. If prompted, type `Y` and press Enter.

---

## 3. Initial Project Setup

You only need to do this the very first time you set up the project.

### Backend Setup (Django)
1. Open a terminal in VSCode and navigate to the backend folder:
   ```powershell
   cd backend
   ```
2. Create a virtual environment:
   ```powershell
   py -3.13 -m venv venv
   ```
3. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```
4. Install the required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```
5. Apply database migrations (sets up the SQLite database):
   ```powershell
   python manage.py migrate
   ```

### Frontend Setup (React/Vite)
1. Open a **new** terminal in VSCode and navigate to the frontend folder:
   ```powershell
   cd frontend
   ```
2. Install the required Node packages:
   ```powershell
   npm install
   ```

---

## 4. How to Run the Project

You can run the project using either the **One-Click Method** or the **Manual Method**.

### Method A: The One-Click VSCode Way (Recommended)
Since we created the `.vscode/launch.json` file, VSCode can handle everything for you automatically.

1. Open the root `CVJachai` folder in VSCode.
2. Click the **Run and Debug** icon on the left sidebar (the play button with a bug, or press `Ctrl+Shift+D`).
3. At the top dropdown, select **"Start CVJachai (Frontend + Backend)"**.
4. Click the green Play button (or press `F5`).
5. VSCode will automatically open a split terminal, start the Django server, and start the Vite frontend server. 

### Method B: The Manual Terminal Way
If you prefer typing the commands yourself, you need to open two separate terminals in VSCode.

**Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\activate
python manage.py runserver
```
*The backend will be running at: http://localhost:8000*

**Terminal 2 (Frontend):**
Click the `+` icon in the terminal window to open a second terminal.
```powershell
cd frontend
npm run dev
```
*The frontend will be running at: http://localhost:5173*

---

## 5. Environment Variables (.env)

Make sure you have `.env` files created in both folders.

**`backend/.env`**
```env
SECRET_KEY=your-dev-secret-key-123
DEBUG=True
# Optional AI features:
# GROQ_API_KEY=your_groq_key_here
```

**`frontend/.env`**
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

> **Missing ML Models Warning**: When you run the backend, you will see a warning: *"Model artifacts not found or could not be loaded: best_classifier.pkl"*. This is perfectly normal. Because the ML model files are too large for Git, the backend automatically switches to **fallback mode** (using the Groq LLM) so the app won't crash.
