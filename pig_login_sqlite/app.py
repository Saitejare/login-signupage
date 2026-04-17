from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "secret_key"

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('sqlitecloud://'):
        import sqlitecloud
        return sqlitecloud.connect(db_url)
    else:
        return sqlite3.connect('users.db')

# Create database
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

    # Add columns if they don't exist (for migration)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN mobile TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

# Joke list
jokes = [
    "Hey {}, you're hogging all the fun today!",
    "Why did the pig become an actor? Because he was a real ham!",
    "Hey {}, stay pig-tastic today!",
    "Why don't pigs use phones? Too many ham calls!",
    "Hey {}, you're oink-tastic!"
]

# Signup
@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        mobile = request.form["mobile"]
        nickname = request.form["nickname"]
        email = request.form["email"]

        if len(password) != 6 or not password.isdigit():
            return render_template("signup.html", error="Password must be exactly 6 digits.")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users (username,password,mobile,nickname,email) VALUES (?,?,?,?,?)",
                (username,password,mobile,nickname,email)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Username already exists!")

        finally:
            conn.close()

        return redirect("/")

    return render_template("signup.html")


# Login
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/welcome")
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# Welcome Page
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


@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)