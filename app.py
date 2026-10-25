import sqlite3
import random
import os

from flask import Flask, abort, render_template, request, redirect, url_for

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cinema.db")

SEAT_LAYOUT = [
    (1, 18), (2, 18), (3, 18),
    (4, 19), (5, 19), (6, 19), (7, 19), (8, 19),
    (9, 14), (10, 14), (11, 14), (12, 14),
]


def random_taken(movie_id, date, time, share=0.25):
    rng = random.Random(f"{movie_id}-{date}-{time}")
    seats = [f"{row}-{s}" for row, count in SEAT_LAYOUT for s in range(1, count + 1)]
    return [seat for seat in seats if rng.random() < share]

MOVIE_FIELDS = ("title", "genre", "duration", "description", "price", "image", "image_url")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            duration INTEGER,
            description TEXT,
            price REAL NOT NULL,
            image TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            seats TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_url(value):
    return value.startswith(("http://", "https://"))


def read_movie_form():
    form = {key: request.form.get(key, "").strip() for key in MOVIE_FIELDS}
    errors = []

    if not form["title"]:
        errors.append("Назва не може бути порожньою.")

    price = None
    try:
        price = float(form["price"])
        if price <= 0:
            errors.append("Ціна має бути додатним числом.")
    except ValueError:
        errors.append("Ціна має бути числом.")

    duration = None
    if form["duration"]:
        try:
            duration = int(form["duration"])
            if duration <= 0:
                errors.append("Тривалість має бути додатним цілим числом.")
        except ValueError:
            errors.append("Тривалість має бути цілим числом.")

    if form["image_url"] and not is_url(form["image_url"]):
        errors.append("Посилання на зображення має починатися з http:// або https://.")

    values = {
        "title": form["title"],
        "genre": form["genre"],
        "duration": duration,
        "description": form["description"],
        "price": price,
        "image": form["image_url"] or form["image"],
    }
    return form, errors, values


@app.route("/")
def index():
    conn = get_db()
    featured = conn.execute("SELECT * FROM movies ORDER BY id DESC LIMIT 4").fetchall()
    movies_count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    seat_rows = conn.execute("SELECT seats FROM bookings").fetchall()
    conn.close()

    tickets_sold = sum(len(r["seats"].split(",")) for r in seat_rows)
    stats = {"movies": movies_count, "halls": 3, "tickets": tickets_sold}
    return render_template("index.html", featured=featured, stats=stats)

NAV_PAGES = [
    ("index", "Головна"),
    ("about", "Про нас"),
    ("movies", "Фільми"),
    ("gallery", "Галерея"),
    ("add_movie", "Додати фільм"),
    ("contacts", "Контакти"),
    ("booking", "Квитки"),
]


@app.context_processor
def inject_nav():
    idx = next((i for i, (ep, _) in enumerate(NAV_PAGES) if ep == request.endpoint), None)
    prev_page = NAV_PAGES[idx - 1] if idx is not None and idx > 0 else None
    next_page = NAV_PAGES[idx + 1] if idx is not None and idx < len(NAV_PAGES) - 1 else None
    return dict(nav_pages=NAV_PAGES, prev_page=prev_page, next_page=next_page)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/movies")
def movies():
    q = request.args.get("q", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()

    max_price = None
    if max_price_raw:
        try:
            max_price = float(max_price_raw)
        except ValueError:
            max_price = None

    conn = get_db()
    if max_price is not None:
        rows = conn.execute(
            "SELECT * FROM movies WHERE price <= ?", (max_price,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM movies").fetchall()
    conn.close()

    if q:
        movie_list = [m for m in rows if q.lower() in m["title"].lower()]
    else:
        movie_list = list(rows)

    searched = bool(q) or max_price is not None
    return render_template(
        "movies.html",
        movies=movie_list,
        q=q,
        max_price=max_price_raw,
        searched=searched,
    )


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    if request.method == "GET":
        return render_template("add_movie.html", errors=[], form={})

    form, errors, values = read_movie_form()
    if errors:
        return render_template("add_movie.html", errors=errors, form=form)

    conn = get_db()
    conn.execute(
        "INSERT INTO movies (title, genre, duration, description, price, image) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            values["title"],
            values["genre"],
            values["duration"],
            values["description"],
            values["price"],
            values["image"],
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("movies"))


@app.route("/edit_movie/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    conn = get_db()
    movie = conn.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()

    if movie is None:
        conn.close()
        abort(404)

    if request.method == "GET":
        conn.close()
        current_image = movie["image"] or ""
        form = {
            "title": movie["title"],
            "genre": movie["genre"] or "",
            "duration": movie["duration"] or "",
            "description": movie["description"] or "",
            "price": movie["price"],
            "image": "" if is_url(current_image) else current_image,
            "image_url": current_image if is_url(current_image) else "",
        }
        return render_template("edit_movie.html", movie=movie, errors=[], form=form)

    form, errors, values = read_movie_form()
    if errors:
        conn.close()
        return render_template("edit_movie.html", movie=movie, errors=errors, form=form)

    conn.execute(
        "UPDATE movies SET title = ?, genre = ?, duration = ?, description = ?, "
        "price = ?, image = ? WHERE id = ?",
        (
            values["title"],
            values["genre"],
            values["duration"],
            values["description"],
            values["price"],
            values["image"],
            movie_id,
        ),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("movies"))


@app.route("/delete_movie/<int:movie_id>", methods=["POST"])
def delete_movie(movie_id):
    conn = get_db()
    conn.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("movies"))


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/booking", methods=["GET", "POST"])
def booking():
    conn = get_db()
    movies = conn.execute("SELECT id, title FROM movies ORDER BY title").fetchall()

    movie_id = request.values.get("movie", type=int)
    date = request.values.get("date", "").strip()
    time = request.values.get("time", "").strip()

    def load_taken(mid, d, t):
        taken_list = []
        if mid and d and t:
            taken_list.extend(random_taken(mid, d, t))
            rows = conn.execute(
                "SELECT seats FROM bookings WHERE movie_id = ? AND date = ? AND time = ?",
                (mid, d, t),
            ).fetchall()
            for r in rows:
                taken_list.extend(r["seats"].split(","))
        return taken_list
    
    errors = []
    success = None

    if request.method == "POST":
        seats = [s for s in request.form.get("seats", "").split(",") if s]
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        total = request.form.get("total", type=float) or 0

        if not movie_id:
            errors.append("Оберіть фільм.")
        if not date:
            errors.append("Оберіть дату.")
        if not time:
            errors.append("Оберіть час сеансу.")
        if not seats:
            errors.append("Оберіть хоча б одне місце.")
        if not name:
            errors.append("Вкажіть ім'я.")
        if not phone:
            errors.append("Вкажіть телефон.")

        if not errors:
            already = set(load_taken(movie_id, date, time))
            if any(s in already for s in seats):
                errors.append("Деякі місця вже зайняті. Оберіть інші.")

        if not errors:
            conn.execute(
                "INSERT INTO bookings (movie_id, date, time, seats, name, phone, total) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (movie_id, date, time, ",".join(seats), name, phone, total),
            )
            conn.commit()
            movie_title = conn.execute(
                "SELECT title FROM movies WHERE id = ?", (movie_id,)
            ).fetchone()["title"]
            success = {
                "movie": movie_title,
                "date": date,
                "time": time,
                "seats": ", ".join(seats),
                "name": name,
                "total": total,
            }

    taken = load_taken(movie_id, date, time)
    conn.close()
    return render_template(
        "booking.html",
        movies=movies,
        taken=taken,
        errors=errors,
        success=success,
        movie_id=movie_id,
        date=date,
        time=time,
    )

@app.route("/bookings")
def bookings_list():
    conn = get_db()
    rows = conn.execute("""
        SELECT b.id, b.date, b.time, b.seats, b.name, b.phone, b.total,
               b.created_at, m.title AS movie_title
        FROM bookings b
        LEFT JOIN movies m ON m.id = b.movie_id
        ORDER BY b.created_at DESC, b.id DESC
    """).fetchall()
    conn.close()

    total_sum = sum(r["total"] for r in rows)
    tickets = sum(len(r["seats"].split(",")) for r in rows)
    return render_template("bookings.html", bookings=rows, total_sum=total_sum, tickets=tickets)

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)