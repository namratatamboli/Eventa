import sqlite3

# connect to database
def get_db_connection():
    conn = sqlite3.connect("database/database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- USERS ----------------

# create user table if not exists
def create_user_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# insert new user
def create_user(username, email, password):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None  # duplicate username/email

# check if user exists 
def get_user_by_username(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()
    return user


# ---------------- EVENTS ----------------

# create events table if not exists
def create_event_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            description TEXT,
            host_name TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            venue TEXT NOT NULL,
            budget REAL,
            guest_count INTEGER,
            is_draft INTEGER DEFAULT 1,   -- 1 = draft, 0 = finalized
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

# insert new event (defaults to draft)
def create_event(user_id, event_name, description, host_name, date, time, venue, budget=None, guest_count=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (user_id, event_name, description, host_name, date, time, venue, budget, guest_count, is_draft)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (user_id, event_name, description, host_name, date, time, venue, budget, guest_count))
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id

# update existing event
def update_event(event_id, event_name, description, host_name, date, time, venue, budget=None, guest_count=None, is_draft=1):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events
        SET event_name = ?, description = ?, host_name = ?, date = ?, time = ?, venue = ?, budget = ?, guest_count = ?, is_draft = ?
        WHERE id = ?
    """, (event_name, description, host_name, date, time, venue, budget, guest_count, is_draft, event_id))
    conn.commit()
    conn.close()

# fetch a single event by ID
def get_event_by_id(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()
    conn.close()
    return event

# get all events for a user
def get_events_by_user(user_id, include_drafts=False):
    conn = get_db_connection()
    cur = conn.cursor()
    if include_drafts:
        cur.execute("SELECT * FROM events WHERE user_id = ? ORDER BY date, time", (user_id,))
    else:
        cur.execute("SELECT * FROM events WHERE user_id = ? AND is_draft = 0 ORDER BY date, time", (user_id,))
    events = cur.fetchall()
    conn.close()
    return events


# ---------------- BUDGET ----------------

def create_budget_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def add_budget_item(event_id, category, amount):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO budgets (event_id, category, amount) VALUES (?, ?, ?)",
        (event_id, category, amount)
    )
    conn.commit()
    conn.close()

def get_budget_by_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM budgets WHERE event_id = ?", (event_id,))
    budgets = cur.fetchall()
    conn.close()
    return budgets

def get_total_budget(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) as total FROM budgets WHERE event_id = ?", (event_id,))
    total = cur.fetchone()["total"]
    conn.close()
    return total if total else 0

def update_event_budget(event_id, budget):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE events SET budget = ? WHERE id = ?", (budget, event_id))
    conn.commit()
    conn.close()

def clear_budget_items(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM budgets WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()

def migrate_add_is_draft():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE events ADD COLUMN is_draft INTEGER DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists → ignore
        pass
    conn.close()



# ---------------- DELETE ----------------    

def delete_event_by_id(event_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # First delete related budget items (because of FK constraint)
    cur.execute("DELETE FROM budgets WHERE event_id = ?", (event_id,))
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()



