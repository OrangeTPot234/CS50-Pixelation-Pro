import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, insert_picture, extract_pictures 

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///databases.db")

#GALLERY_PHOTOS = []
#USER_PHOTOS = []

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
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
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password is re-entered
        elif not request.form.get("confirmation"):
            return apology("must re-enter password", 400)

        # Ensure password is re-entered correctly
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("please reenter: passwords do not match", 400)

        # Ensure that username does not exist
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) >= 1:
            return apology("username already in use", 400)

        # Temporarily save username and password for entry into database
        input1 = request.form.get("username")
        input2 = generate_password_hash(request.form.get("password"))
        
        # save username and password into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", input1, input2)

        # LOG IN USER: Get user_id and get session_id to log in user
        user = db.execute("SELECT * FROM users WHERE username = ?", input1)
        session["user_id"] = user[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # load page for register
    else:
        return render_template("register.html")








#### GALLERY PAGES ####








@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get info on username and cash remaining
    user_info = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
    username = user_info[0]["username"]

    galleries = db.execute("SELECT * FROM galleries WHERE user_id = ?", session["user_id"])

    top_sites = db.execute("SELECT * from galleries ORDER BY views DESC LIMIT 3")

    if request.form.get("add_gallery"):
        return redirect("/upload")

    # If user does not own any stocks load page with special note
    if not galleries:
        screenload = 0
        return render_template("userpage.html", username=username, screenload=screenload, top_sites=top_sites)

    # load screen and load appropriate variables into HTML
    screenload = 1
    return render_template("userpage.html", username=username, galleries=galleries, screenload=screenload)


@app.route("/newgallery", methods=["GET", "POST"])
@login_required
def newgallery():
    if request.method == "POST":
        f = request.files['photo']
        gallery_title = request.form.get("gallery_title")
        photo_name = request.form.get("photo_name")
        if f.filename == '':
            state = 1
            return render_template("newgallery.html", session=state)
        verify = db.execute("SELECT * from galleries WHERE gallery_name = ? AND user_id = ?", gallery_title, session["user_id"])
        if len(verify) >= 1:
            state = 2
            return render_template("newgallery.html", session=state)
        if photo_name == '':
            state = 3
            return render_template("newgallery.html", session=state)
        db.execute("INSERT INTO galleries (user_id, gallery_name) VALUES (?, ?)", session["user_id"], gallery_title)
        gallery_id = str(db.execute("SELECT gallery_id FROM galleries WHERE user_id = ? AND gallery_name = ?", session["user_id"], gallery_title)[0]['gallery_id'])
        f.save(secure_filename(f.filename))
        insert_picture(f.filename.replace(" ", "_"), photo_name, gallery_id, session["user_id"])
        os.remove(f.filename)
        return redirect("/edit?g=" + gallery_id)
    else:
        return render_template("newgallery.html")


@app.route("/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    if request.method == "GET":
        gallery_id = request.args.get("g")
        gallery_info = db.execute("SELECT * FROM galleries WHERE gallery_id = ?", gallery_id)
        if gallery_info[0]['user_id'] == session["user_id"]:
            return redirect("/edit?g=" + gallery_id)
        counter = gallery_info[0]["views"] + 1
        db.execute("UPDATE galleries SET views = ? WHERE gallery_id = ?", counter, gallery_id) 
        photos = extract_pictures(gallery_id, "gal")
        return render_template("gallery.html", gallery_name=gallery_info[0]['gallery_name'], photo_list=photos)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "GET":
        search = request.args.get("q")
        gallery_info = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id  WHERE gallery_name LIKE ?",'%' + search + '%' )
        if not gallery_info:
            flash("Invalid Search")
            return redirect("/")
        return render_template("search.html", galleries=gallery_info)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "GET":
        gallery_id = request.args.get("g")
        gallery_info = db.execute("SELECT * FROM galleries WHERE gallery_id = ?", gallery_id)
        if gallery_info[0]['user_id'] != session["user_id"]:
            return redirect("/gallery?g=" + gallery_id)
        photos = extract_pictures(gallery_id, "gal")
        return render_template("edit.html", galleries=gallery_info, photos=photos)

@app.route("/upgalnm", methods=["GET", "POST"])
@login_required
def upgalnm():
    if request.method == "POST":
        gallery_name = request.form.get("gallery_name")
        gallery_id = request.form.get("gallery_id")
        if not gallery_name:
            flash('Please provide new gallery title')
            return redirect("/edit?g=" + gallery_id)
        verify = db.execute("SELECT * from galleries WHERE gallery_name = ? AND user_id = ?", gallery_name, session["user_id"])
        if len(verify) >=1:
            flash('Gallery title already in use')
            return redirect("/edit?g=" + gallery_id)
        db.execute("UPDATE galleries SET gallery_name = ? WHERE gallery_id = ?", gallery_name, gallery_id)
        return redirect("/edit?g=" + gallery_id)
    else:
        return redirect("/")

@app.route("/updatephotos", methods=["GET", "POST"])
@login_required
def updatephotos():
    if request.method == "POST":
        photo_name = request.form.get("photo_name")
        photo_id = request.form.get("photo_id")
        gallery_id = request.form.get("gallery_id_2")
        if not photo_name:
            flash('Please provide photo title')
            return redirect("/edit?g=" + gallery_id)
        verify = db.execute("SELECT * from photos WHERE gallery_id = ? AND photo_name = ?", gallery_id, photo_name)
        if len(verify) >=1:
            flash('Photo name already in use in this gallery')
            return redirect("/edit?g=" + gallery_id)
        db.execute("UPDATE photos SET photo_name = ? WHERE photo_id = ?", photo_name, photo_id)
        return redirect("/edit?g=" + gallery_id)
    else: 
        return redirect("/")

@app.route("/deletegal", methods=["GET", "POST"])
@login_required
def deletegal():
    if request.method == "POST":
        gallery_id = request.form.get("gallery_id_3")
        db.execute("DELETE FROM photos WHERE gallery_id = ?", gallery_id)
        db.execute("DELETE FROM galleries WHERE gallery_id = ?", gallery_id)
        return redirect("/")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        gallery_id = request.form.get("gallery_id")
        photo_name = request.form.get("photo_name")
        if not photo_name:
            flash("Please provide new photo name before uploading")
            return redirect("/edit?g="+gallery_id)
        verify = db.execute("SELECT * from photos WHERE gallery_id = ? AND photo_name = ?", gallery_id, photo_name)
        if len(verify) >=1:
            flash('Photo name already in use in this gallery')
            return redirect("/edit?g=" + gallery_id)
        f = request.files['photo']
        if f.filename == '':
            flash('Please provide ".jpeg" file to upload')
            return redirect("/edit?g=" + gallery_id)
        f.save(secure_filename(f.filename))
        insert_picture(f.filename.replace(" ", "_"), photo_name, gallery_id, session["user_id"])
        os.remove(f.filename)
        return redirect("/edit?g="+gallery_id)
    else: 
        return redirect("/")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "GET":
        gallery_id = request.args.get("g")
        user_id = request.args.get("u")
        photo_id = request.args.get("i")
        if int(user_id) == int(session["user_id"]):
            db.execute("DELETE FROM photos WHERE photo_id = ? AND gallery_id = ?", photo_id, gallery_id)
            return redirect("/edit?g=" + gallery_id)
        else:
            return redirect("/gallery?g=" + gallery_id)
    else: 
        return redirect("/")

#### ERROR HANDLING ####



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)