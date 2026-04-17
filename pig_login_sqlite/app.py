from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import os

# Password Security
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    db_url = os.environ.get("DATABASE_URL")

    # SQLiteCloud connection
    if db_url and db_url.startswith("sqlitecloud://"):

        import sqlitecloud
        conn = sqlitecloud.connect(db_url)
        return conn

    # Local SQLite fallback
    conn = sqlite3.connect("users.db")
    return conn


# =========================
# SAFE COLUMN ADD
# =========================

def safe_add_column(cursor, sql):

    try:
        cursor.execute(sql)
    except Exception:
        pass


# =========================
# DATABASE INITIALIZATION
# =========================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            mobile TEXT,
            nickname TEXT,
            email TEXT
        )
    """)

    # Migration safety
    safe_add_column(cursor,
        "ALTER TABLE users ADD COLUMN mobile TEXT")

    safe_add_column(cursor,
        "ALTER TABLE users ADD COLUMN nickname TEXT")

    safe_add_column(cursor,
        "ALTER TABLE users ADD COLUMN email TEXT")

    conn.commit()
    conn.close()


init_db()


# =========================
# JOKES
# =========================

jokes = [

    "Hey {}, you're hogging all the fun today!",

    "Why did the pig become an actor? Because he was a real ham!",

    "Hey {}, stay pig-tastic today!",

    "Why don't pigs use phones? Too many ham calls!",

    "Hey {}, you're oink-tastic!"

]


# =========================
# SIGNUP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        mobile = request.form["mobile"]
        nickname = request.form["nickname"]
        email = request.form["email"]

        # Password validation
        if len(password) != 6 or not password.isdigit():

            return render_template(
                "signup.html",
                error="Password must be exactly 6 digits."
            )

        # Hash password
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (username,password,mobile,nickname,email)
                VALUES (?,?,?,?,?)
                """,
                (
                    username,
                    hashed_password,
                    mobile,
                    nickname,
                    email
                )
            )

            conn.commit()

        except Exception:

            return render_template(
                "signup.html",
                error="Username already exists!"
            )

        finally:
            conn.close()

        return redirect("/")

    return render_template("signup.html")


# =========================
# LOGIN  (FIXED VERSION)
# =========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            try:

                # SQLiteCloud returns tuple
                stored_password = user[2]

                if check_password_hash(
                        stored_password,
                        password):

                    session["user"] = username
                    return redirect("/welcome")

                else:

                    return render_template(
                        "login.html",
                        error="Wrong password"
                    )

            except Exception as e:

                return f"Login Error: {str(e)}"

        else:

            return render_template(
                "login.html",
                error="User not found"
            )

    return render_template("login.html")


# =========================
# WELCOME PAGE
# =========================

@app.route("/welcome")
def welcome():

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    joke = random.choice(jokes)

    if "{}" in joke:
        joke = joke.format(username)

    return render_template(
        "welcome.html",
        username=username,
        joke=joke
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


# =========================
# RUN SERVER (RENDER READY)
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
