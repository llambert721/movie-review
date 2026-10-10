# Movie Review

A Flask web app for browsing movies, writing reviews, and managing accounts. Movies, users, and reviews are stored in MongoDB.

## Setup

### 1. Create a `.env` file

In the project root, create a file named `.env` with your MongoDB Atlas username and password:

```
MONGO_USER=your_username
MONGO_PASSWORD=your_password
```

The app builds the connection string from those two values. If you already have a full connection string, you can set `MONGO_URI` instead. `.env` is gitignored.

### 2. Create and activate a virtual environment

From the project root, in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Launch the app

```powershell
python app.py
```

Open [http://localhost:5000](http://localhost:5000). The login page is the home page.
