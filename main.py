from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from database.sqlitequery import (
    create_user, get_user_by_username, create_event, get_events_by_user,
    create_user_table, create_event_table, get_db_connection,
    update_event, get_event_by_id, add_budget_item, get_budget_by_event, create_budget_table,
    update_event_budget, clear_budget_items, migrate_add_is_draft, delete_event_by_id
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure required tables exist
create_user_table()
create_event_table()
create_budget_table()
migrate_add_is_draft()

# ---------------- LANDING ----------------
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- AUTH ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        # Check if username already exists
        if get_user_by_username(username):
            flash("Username already taken.")
            return redirect(url_for("signup"))

        # Create new user
        user_id = create_user(username, email, password)
        if not user_id:  # Email already registered
            flash("Email already registered.")
            return redirect(url_for("signup"))

        # Log user in after signup
        session["user_id"] = user_id
        session["username"] = username
        flash("Account created successfully!")
        return redirect(url_for("home"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = get_user_by_username(username)
        # Verify credentials
        if user and user["password"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("landing"))

# ---------------- HOME ----------------
@app.route("/home")
def home():
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    return render_template("home.html")

# ---------------- ADD / EDIT EVENT ----------------
@app.route("/add_event", methods=["GET", "POST"])
@app.route("/add_event/<int:event_id>", methods=["GET", "POST"])
def add_event(event_id=None):
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    # Create draft event if no ID given
    if not event_id:
        event_id = create_event(
            session["user_id"], event_name="", description="", host_name="",
            date="", time="", venue="", budget=None, guest_count=None
        )
        return redirect(url_for("add_event", event_id=event_id))

    event = get_event_by_id(event_id)

    if request.method == "POST":
        # Gather form data
        event_name = request.form.get("event_name", "").strip()
        description = request.form.get("description", "").strip()
        host_name = request.form.get("host_name", "").strip()
        date = request.form.get("date", "")
        time = request.form.get("time", "")
        venue = request.form.get("venue", "").strip()
        budget = float(request.form.get("budget") or 0) or None
        guest_count = int(request.form.get("guest_count") or 0) or None
        finalize = request.form.get("finalize")  # Hidden input

        # Update event
        update_event(
            event_id, event_name, description, host_name,
            date, time, venue, budget, guest_count,
            is_draft=0 if finalize else 1
        )

        flash("Event updated and finalized!" if finalize else "Draft saved.")
        return redirect(url_for("dashboard") if finalize else url_for("add_event", event_id=event_id))

    return render_template("add_event.html", event=event, event_id=event_id)

# ---------------- BUDGET ----------------
@app.route("/budget/<int:event_id>", methods=["GET", "POST"])
def manage_budget(event_id):
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    event = get_event_by_id(event_id)
    if not event or event["user_id"] != session["user_id"]:
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Update total budget
        total_budget = request.form.get("total_budget")
        if total_budget:
            update_event_budget(event_id, float(total_budget))

        # Update budget items
        categories = request.form.getlist("category[]")
        amounts = request.form.getlist("amount[]")
        clear_budget_items(event_id)

        for category, amount in zip(categories, amounts):
            if category.strip() and amount.strip():
                add_budget_item(event_id, category.strip(), float(amount))

        flash("Budget updated successfully!")
        return redirect(url_for("manage_budget", event_id=event_id))

    budgets = get_budget_by_event(event_id) or []
    total_spent = sum(b["amount"] for b in budgets)
    remaining = (event["budget"] or 0) - total_spent

    return render_template("budget.html", event=event, budgets=budgets, total_spent=total_spent, remaining=remaining)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    search_query = request.args.get("q", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    # Search events if query exists
    if search_query:
        cur.execute(
            "SELECT * FROM events WHERE user_id = ? AND event_name LIKE ? AND is_draft = 0 ORDER BY date DESC",
            (user_id, f"%{search_query}%"),
        )
    else:
        cur.execute(
            "SELECT * FROM events WHERE user_id = ? AND is_draft = 0 ORDER BY date DESC",
            (user_id,)
        )

    events = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", events=events)

# ---------------- VIEW EVENT ----------------
@app.route("/event/<int:event_id>")
def view_event(event_id):
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    event = get_event_by_id(event_id)
    if not event or event["user_id"] != session["user_id"]:
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))

    budgets = get_budget_by_event(event_id) or []
    total_spent = sum(b["amount"] for b in budgets)
    remaining = (event["budget"] or 0) - total_spent

    return render_template("view_event.html", event=event, budgets=budgets, total_spent=total_spent, remaining=remaining)

# ---------------- EDIT EVENT ----------------
@app.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    event = get_event_by_id(event_id)
    if not event or event["user_id"] != session["user_id"]:
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))

    budgets = get_budget_by_event(event_id)

    if request.method == "POST":
        # Update event details
        event_name = request.form["event_name"].strip()
        description = request.form.get("description", "").strip()
        host_name = request.form.get("host_name", "").strip()
        date = request.form["date"]
        time = request.form["time"]
        venue = request.form["venue"].strip()
        budget = float(request.form.get("budget") or 0) or None
        guest_count = int(request.form.get("guest_count") or 0) or None

        update_event(event_id, event_name, description, host_name, date, time, venue, budget, guest_count, is_draft=0)

        # Update budget items
        categories = request.form.getlist("category[]")
        amounts = request.form.getlist("amount[]")
        clear_budget_items(event_id)
        for c, a in zip(categories, amounts):
            if c.strip() and a.strip():
                add_budget_item(event_id, c.strip(), float(a))

        flash("Event and budget updated successfully!")
        return redirect(url_for("view_event", event_id=event_id))

    return render_template("edit_event.html", event=event, budgets=budgets)

# ---------------- DELETE EVENT ----------------
@app.route("/event/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    event = get_event_by_id(event_id)
    if not event or event["user_id"] != session["user_id"]:
        flash("Unauthorized action.")
        return redirect(url_for("dashboard"))

    delete_event_by_id(event_id)
    flash("Event deleted successfully.")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
