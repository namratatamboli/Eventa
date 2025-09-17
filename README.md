# Eventa 🎉

Eventa is a web-based event management app built with Flask and SQLite. It allows users to create, manage, and track events, budgets, and guest lists easily.

## Features

- User authentication: Signup, Login, Logout
- Create, edit, and delete events
- Save events as drafts or finalize them
- Add and manage budget items for each event
- View a dashboard of all finalized events
- Search events by name
- Secure session management with Flask sessions

## Setup Instructions

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Eventa
```

2. Create a virtual environment (optional):
```bash
python -m venv venv
```
###   Linux / macOS
```bash
source venv/bin/activate
```
###   Windows
```bash
venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
python main.py
```

5. Open in browser:
   
Visit http://127.0.0.1:5000

## File Structure
```bash
Eventa/
├── main.py
├── database/
│   └── sqlitequery.py
├── templates/
│   ├── landing.html
│   ├── about.html
│   ├── signup.html
│   ├── login.html
│   ├── home.html
│   ├── add_event.html
│   ├── edit_event.html
│   ├── view_event.html
│   ├── dashboard.html
│   └── budget.html
├── static/
│   ├── css/
│   └── js/
├── requirements.txt
├── .gitignore
└── README.md
```

## How it Works

- #### Authentication:<br>
  Signup with username, email, and password; Login to access personalized events and dashboard; Logout ends the session securely
- #### Event Management:<br>
  Add events with name, description, host, date, time, venue, budget, guest count; Save events as drafts or finalize them; Edit or delete existing events
- #### Budget Management:<br>
  Add categories and amounts to track expenses; Update total budget and individual items; View total spent and remaining budget for each event
- #### Dashboard:<br>
  Displays all finalized events; Search events by name

## Technologies Used

- Python 3
- Flask
- SQLite3
- HTML / CSS / JavaScript

## Author  
Namrata Tamboli
