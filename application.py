from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///MM.db")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

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

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any existing logged in user
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #return apology("TODO")
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password and confirm password matches
        elif request.form.get("password") != request.form.get("password2"):
            return apology("passwords do not match", 403)

        # Query database to ensure username does not already exist
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 0:
            return apology("username already exists", 403)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():
    # Access users watchlist to provide to HTML file
    watchlist = db.execute("SELECT movie_id, title, rating, url_id FROM watchlist WHERE user_id = :user",
                            user = session["user_id"])

    return render_template("index.html", watchlist = watchlist)


@app.route("/addmovie", methods=["GET", "POST"])
@login_required
def addmovie():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Create variables to easily access form data
        url = request.form.get("movie_url")
        rating = request.form.get("rating")

        # Extract movie id from the provided URL
        movie_id = url.split("/title/tt")[1].split("/")[0]

        # Check if movie already in watchlist
        movie_check = db.execute("SELECT * FROM watchlist WHERE movie_id = :movie_id AND user_id = :user", movie_id = movie_id, user = session["user_id"])

        # If movie not already added, add movie id, name and rating into watchlist for that user
        if not movie_check:
            movie_name = db.execute("INSERT INTO watchlist (user_id, movie_id, rating, title, url_id) VALUES (:user_id, :movie_id, :rating, :title, :url_id)",
                                    user_id = session["user_id"],
                                    movie_id = movie_id,
                                    rating = rating,
                                    title = db.execute("SELECT title FROM movies WHERE id = :movie_id", movie_id = movie_id)[0]['title'],
                                    url_id = str(movie_id).zfill(10) # Pads movie_id's below 10 char with zeros to give correct format to be inserted into IMDB link
                                    )

        else:
            return render_template("alreadyaddedmovie.html")

    # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addmovie.html")



@app.route("/mutuals", methods=["GET", "POST"])
@login_required
def mutuals():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Access user id of submitted username
        user2 = db.execute("SELECT id FROM users WHERE username = :username",
                        username = request.form.get("username"))[0]['id']

        if not user2:
            return apology("Username does not exist")


        # Access users mutual watchlist to provide to HTML file and order by average rating
        matchlist = db.execute("SELECT movie_id, title, AVG(rating) AS rating, url_id FROM watchlist WHERE user_id = :user OR user_id = :user2 GROUP BY movie_id HAVING COUNT(*) >1 ORDER BY rating DESC",
                            user = session["user_id"],
                            user2 = user2)

        if not matchlist:
            return render_template("no_matches.html", user_to_match = user2)

        return render_template("mutuals.html", matchlist = matchlist)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("searchuser.html")


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    # Obtain row of data to delete
    movie_to_delete = id

    # Delete movie from watchlist
    db.execute("DELETE FROM watchlist WHERE user_id = :user AND movie_id = :movie_id",
                user = session["user_id"],
                movie_id = movie_to_delete)


    return redirect("/")


@app.route("/update_rating/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Obtain movie to update and users new submitted rating
        movie_to_update = id
        new_rating = request.form.get("new_rating")

        if not new_rating:
            return apology("rating error")

        # Update rating for that movie in watchlist db
        db.execute("UPDATE watchlist SET rating = :new_rating WHERE user_id = :user AND movie_id = :movie_id",
                    new_rating = new_rating,
                    user = session["user_id"],
                    movie_id = movie_to_update)


        return redirect("/")

    else:
        return redirect("/")


# Listen for errors
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

for code in default_exceptions:
    app.errorhandler(code)(errorhandler)