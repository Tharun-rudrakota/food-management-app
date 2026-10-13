# FreshPantry — Food Item & Daily Food Management System

A web application designed for smart food inventory tracking, expiry date monitoring, food waste reduction, and daily food consumption management.

---

## 📸 Overview & Design

Built with an intuitive, clean interface:
- **Dark Forest Green Sidebar** with **Dashboard** header in golden-yellow typography (`#f3ba2f`), navigation links (**Home**, **About**, **Contact**, **Food Inventory**, **Daily Food Usage**, **Profile**), and a red **Logout** button.
- **Home Dashboard**:
  - Headline: *"Keep Food Fresh, Waste Less, Live Better"*
  - Subtitle: *"Track your food inventory, monitor shelf life, and effortlessly manage daily meals."*
  - **4 Status Metric Cards**:
    1. **Total Food Items** (Soft light blue)
    2. **Fresh Items** (Soft mint green)
    3. **Expiring Soon** (Soft pastel yellow, ≤ 7 days)
    4. **Expired Items** (Soft light red, past expiry date)
- **Footer**: `©2026 FreshPantry. All rights Reserved. freshpantry2026@gmail.com`

---

## 🌟 Key Features

### 1. User Authentication & Credentials
- **Sign In & Sign Up** with PBKDF2 secure password hashing (`werkzeug.security`).
- **Instant Demo Account**: Pre-seeded `demo` / `demo123` with 1-click autofill on the login screen.
- Private inventories and consumption logs per user.

### 2. Food Item Management (Inventory)
- Add, Edit, and Delete food items.
- Fields: Item Name, Category, Quantity, Unit, Storage Location (Fridge, Freezer, Pantry, Counter), Purchase Date, Expiry Date, and Notes.
- Automatic shelf life calculation:
  - **Fresh**: Expiry > 7 days away.
  - **Expiring Soon**: Expiry within 0–7 days.
  - **Expired**: Expiry date passed.
- Filters: Search by name, filter by status, storage location, and category.

### 3. Daily Food Management (Consumption & Waste Prevention)
- **"Use / Consume" Action**: Easily record how much of an item was used today (for Breakfast, Lunch, Dinner, Snacks, or Recipes). The quantity is automatically deducted from inventory!
- **Cook / Eat First Alerts**: Visual banner highlighting items expiring in the next 1–3 days, prompting you to plan meals around them before they spoil.
- **Consumption History**: Date-based log of all food consumed or cooked.

### 4. About & Contact Pages
- **About**: Explains the mission to reduce food waste, along with optimal temperature and storage guides for Fridge, Freezer, and Pantry.
- **Contact**: Displays `freshpantry2026@gmail.com` and an interactive message inquiry form.

---

## 🚀 How to Run the Project

### One-Click Launch (Windows)
Double-click `run.bat` or execute `run.ps1` in PowerShell.

### Manual Launch
```powershell
cd C:\Users\jayak\.gemini\antigravity\scratch\food-management-app
py app.py
```

Open your browser at:
```
http://127.0.0.1:5000
```

### 🔑 Demo Login Credentials
- **Username:** `demo`
- **Password:** `demo123`

---

## ☁️ Deploying to Vercel

FreshPantry is configured for 1-click deployment on [Vercel](https://vercel.com) using Python Serverless Functions.

### Deployment Files Included:
- `vercel.json`: Rewrites all routes to `/api/index.py`.
- `api/index.py`: Serverless WSGI entrypoint.
- `requirements.txt`: Python package specifications.
- `.vercelignore` & `.gitignore`: Keeps the deployment bundle clean.
- `database.py`: Automatically detects Vercel's serverless environment and mounts SQLite in `/tmp` with auto-seeding.

### Option 1: Deploy via GitHub (Recommended — 2 Minutes)
1. Initialize git and push this folder to your GitHub account:
   ```bash
   git init
   git add .
   git commit -m "FreshPantry initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **Add New...** → **Project**.
4. Select your GitHub repository and click **Import**.
5. Leave all build settings as default and click **Deploy**.
6. Your app will be live at `https://<your-project-name>.vercel.app`!

### Option 2: Deploy via Vercel CLI
1. Install the Vercel CLI:
   ```bash
   npm i -g vercel
   ```
2. Inside the project folder, run:
   ```bash
   vercel
   ```
3. Follow the CLI prompts (press `Enter` to accept defaults).
4. For production:
   ```bash
   vercel --prod
   ```

