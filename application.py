import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

from auxiliary import login_required, lookup, commafy

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Custom filter
app.jinja_env.filters["commafy"] = commafy

# Hashing method used in werkzeug.security.generate_password_hash
HASHING_METHOD = "sha256"

@app.route("/", methods=["GET"])
@login_required
def index():
    """Display search for books"""
    response = db.execute("SELECT fullname FROM users WHERE id = :id", {"id": session["user_id"]}).fetchone()
    name = response.fullname
    return render_template("search.html", name=name)


@app.route("/search", methods=["POST"])
@login_required
def search():
    """Conduct search for books and display results"""
    searchtext = request.form.get("searchtext")
    if len(searchtext) < 4:
        flash("Search text is too short")
        return redirect("/")
    query = "%" + searchtext + "%"
    isbn_rows = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn", {"isbn": query}).fetchall()
    author_rows = db.execute("SELECT * FROM books WHERE title ILIKE :title", {"title": query}).fetchall()
    title_rows = db.execute("SELECT * FROM books WHERE author ILIKE :author", {"author": query}).fetchall()

    books = []
    for book in isbn_rows:
        books.append(book)
    for book in author_rows:
        books.append(book)
    for book in title_rows:
        books.append(book)
    
    count = len(books)
    
    return render_template("matchingbooks.html", books=books, count=count)

@app.route("/displaybook/<int:book_id>")
@login_required
def displaybook(book_id):
    """Display details about a book and reviews"""

    # Make sure book exists
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if not book:
        return render_template("error.html", message="Book not found")
    
    # Get all reviews and user names
    reviews = db.execute("SELECT review, score, fullname, username FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    review_count = len(reviews)
    
    # Craft url for book cover
    cover_url = "http://covers.openlibrary.org/b/isbn/" + book.isbn + "-L.jpg"

    goodreads = lookup(book.isbn)
    
    return render_template("displaybook.html", book=book, reviews=reviews, review_count=review_count, cover_url=cover_url, goodreads=goodreads)

@app.route("/addreview/<int:book_id>", methods=["POST"])
@login_required
def addreview(book_id):
    """Add the user's book rating and review"""

    review = request.form.get("myreview")
    score = request.form.get("myscore")

    if not review or not score:
        flash("Invalid review -- not added")
        return redirect("/")

    score = int(score)
    if score < 1 or score > 5:
        flash("Invalid review -- not added")
        return redirect("/")

    if len(review) < 4:
        flash("Review too short -- not added")
        return redirect("/")

    # check if user already submitted a reviw
    prev_review = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchone()

    if prev_review:
        flash("Review already exists -- not added")
        return redirect("/")
    
    db.execute("INSERT INTO reviews (review, score, book_id, user_id) VALUES (:review, :score, :book_id, :user_id)", {"review": review, "score": score, "book_id": book_id, "user_id": session["user_id"]})
    db.commit()
    
    flash("Review successfully added")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""

    # User reached route via POST 
    if request.method == "POST":

        # Ensure username was submitted
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        password = request.form.get("password")
        passagain = request.form.get("passagain")

        if username == "":
            flash("Please provide a username")
            return redirect("/register")

        # Ensure password was submitted
        elif password == "":
            flash("Please provide a password")
            return redirect("/register")

        # Ensure passagain was the same as password
        elif password != passagain:
            flash("Password fields don't match")
            return redirect("/register")

        username = username.lower()

        # if no fullname, username is fullname
        if not fullname:
            fullname = username

        # Check whether username in use by querying database
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()

        if len(rows) > 0:
            flash("Username not available")
            return redirect("/register")
            
        # Calc password hash
        hash = generate_password_hash(password, HASHING_METHOD)

        # insert new user into database
        try: 
            result = db.execute("INSERT INTO users (fullname, username, hash) VALUES(:fullname, :username, :hash) returning id", {"fullname": fullname, "username": username, "hash": hash})
            db.commit()
            # set id to last insertion autosequence id
            id = result.first()[0]
        except exc.SQLAlchemyError:
            id = None

        if id == None:
            flash("Error adding user")
            return redirect("/register")

        # Remember which user has logged in
        session["user_id"] = id

        # Redirect user to home page
        flash("Registration successful")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Allow user to log in"""

    # clear out any old user_id in session
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Please provide a username")
            return render_template("login.html")  # go back to login
        elif not password:
            flash("Please enter a password")
            return render_template("login.html")   # go back to login
    
        # make usernames case insensitive
        username = username.lower()

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username or password")
            return render_template("login.html")
            
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/api/<isbn>")
def bookinfo(isbn):
    """Respond to API request at this URL"""

    # Make sure book exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    # book not found 
    if not book:
        abort(404)

    # Get aggregate review info from reviews table
    review_info = db.execute("SELECT COUNT(review) AS review_count, AVG(score) as average_score FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone()

    if not review_info:
        abort(404)

    # prepare response
    response = {}
    response["title"] = book.title
    response["author"] = book.author
    response["year"] = book.year
    response["isbn"] = isbn
    response["review_count"] = review_info.review_count
    response["average_score"] = review_info.average_score
    return jsonify(response)

