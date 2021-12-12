import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, insert_picture, extract_pictures, extract_profile_pic

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
            flash("must provide username")
            return redirect("/register")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            return redirect("/register")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            return redirect("/register")

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
            flash("must provide username")
            return redirect("/register")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            return redirect("/register")

        # Ensure password is re-entered
        elif not request.form.get("confirmation"):
            flash("must re-enter password")
            return redirect("/register")

        # Ensure password is re-entered correctly
        elif request.form.get("confirmation") != request.form.get("password"):
            flash("please re-enter: passwords do not match")
            return redirect("/register")

        # Ensure that username does not exist
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) >= 1:
            flash("username already in use")
            return redirect("/register")

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

### GALLERY PAGES ###

@app.route("/")
@login_required
def index():
    """ Show user page and the galleries created by user """

    # Get info on username and cash remaining
    user_info = db.execute("SELECT * FROM users WHERE user_id = ?", session["user_id"])
    username = user_info[0]["username"]

    # Retrieve galleries created by logged in user
    galleries = db.execute("SELECT * FROM galleries WHERE user_id = ?", session["user_id"])

    # Retrieve most visited galleries to go with search bar
    top_sites = db.execute("SELECT * from galleries JOIN users ON users.user_id = galleries.user_id ORDER BY views DESC LIMIT 3")

    # If "add gallery" button is pressed, redirect to create new gallery
    if request.form.get("add_gallery"):
        return redirect("/upload")

    # If user does not have any galleries yet load page with special note
    if not galleries:
        screenload = 0
        return render_template("userpage.html", username=username, screenload=screenload, top_sites=top_sites)

    # load screen and load appropriate variables into HTML
    screenload = 1
    return render_template("userpage.html", username=username, galleries=galleries, screenload=screenload, top_sites=top_sites)


@app.route("/newgallery", methods=["GET", "POST"])
@login_required
def newgallery():
    """ Create new gallery by proving name and file """

    if request.method == "POST":
        # Retrieve data from form: photofile, gallery name, and photo name
        f = request.files['photo']
        gallery_title = request.form.get("gallery_title")
        photo_name = request.form.get("photo_name")

        # If no file is provided, provide error message and reload page
        if f.filename == '':
            state = 1
            return render_template("newgallery.html", session=state)

        # Determine user has not used gallery name before:
        verify = db.execute("SELECT * from galleries WHERE gallery_name = ? AND user_id = ?", gallery_title, session["user_id"])
        # If user has used gallery name, provide error message and reload page
        if len(verify) >= 1:
            state = 2
            return render_template("newgallery.html", session=state)

        # If no photo name provided, provide error message and reload page
        if photo_name == '':
            state = 3
            return render_template("newgallery.html", session=state)

        # Insert gallery into gallery database
        db.execute("INSERT INTO galleries (user_id, gallery_name) VALUES (?, ?)", session["user_id"], gallery_title)

        # Retrieve Gallery_ID from newly created gallery
        gallery_id = str(db.execute("SELECT gallery_id FROM galleries WHERE user_id = ? AND gallery_name = ?", session["user_id"], gallery_title)[0]['gallery_id'])

        # Upload provided photo to database
        # Temporarily save photo on server/codespace
        f.save(secure_filename(f.filename))
        # Insert photo into database
        insert_picture(f.filename.replace(" ", "_"), photo_name, gallery_id, session["user_id"])
        # Remove saved photo from server/codespace
        os.remove(f.filename)
        # Load edit page for newly created gallery for user
        return redirect("/edit?g=" + gallery_id)

    # Otherwise, load page
    else:
        return render_template("newgallery.html")


@app.route("/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    """ Load gallery page to view pictures and creations """

    # Used get request to users can more easily search website galleries
    if request.method == "GET":
        # Obtain GET request information and retrieve gallery information from database
        gallery_id = request.args.get("g")
        gallery_info = db.execute("SELECT * FROM galleries WHERE gallery_id = ?", gallery_id)

        # If user created gallery being viewed, redirect to edit page instead
        if gallery_info[0]['user_id'] == session["user_id"]:
            return redirect("/edit?g=" + gallery_id)

        # else, load page and increase views count by one
        counter = gallery_info[0]["views"] + 1
        db.execute("UPDATE galleries SET views = ? WHERE gallery_id = ?", counter, gallery_id)

        # Extract photos from database
        photos = extract_pictures(gallery_id, "gal")

        # Retrieve comments from database
        comments = db.execute("SELECT * FROM comments WHERE gallery_id = ? ORDER BY timestamp", gallery_id)

        # Retrieve most visited galleries to go with search bar
        top_sites = db.execute("SELECT * from galleries JOIN users ON users.user_id = galleries.user_id ORDER BY views DESC LIMIT 3")

        # Retreive name and bio information about artist from database:
        profile_data = db.execute("SELECT * from users WHERE user_id = ?", gallery_info[0]["user_id"])
        # If bio and picture are not already uploaded, load page without these:
        if not profile_data[0]["profile_info"]:
            # If no comments are on page yet, load page without comments table
            if len(comments) <= 0:
                return render_template("gallery.html", gallery_name=gallery_info[0]['gallery_name'], photo_list=photos, state=0, gallery_id=gallery_id, top_sites=top_sites, gallery_creator=profile_data[0]["username"])
            # Otherwise load page with comments
            return render_template("gallery.html", gallery_name=gallery_info[0]['gallery_name'], photo_list=photos, state=1, comments=comments, gallery_id=gallery_id, top_sites=top_sites, gallery_creator=profile_data[0]["username"])

        # Extract profile photo and save bio to variable
        profile_pic = extract_profile_pic(profile_data[0]["profile_pic"])
        profile_info = profile_data[0]["profile_info"]

        # If no comments are on page yet, load page without comments table but with bio/profile pic
        if len(comments) <= 0:
                return render_template("gallery.html", gallery_name=gallery_info[0]['gallery_name'], photo_list=photos, state=0, gallery_id=gallery_id, top_sites=top_sites, profile_pic=profile_pic, profile_info=profile_info, gallery_creator=profile_data[0]["username"], profile_check = 1)
        # Otherwise load page with comments and bio/profile pic
        return render_template("gallery.html", gallery_name=gallery_info[0]['gallery_name'], photo_list=photos, state=1, comments=comments, gallery_id=gallery_id, top_sites=top_sites, profile_pic=profile_pic, profile_info=profile_info, gallery_creator=profile_data[0]["username"], profile_check = 1)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """ Load search results from query """

    if request.method == "GET":
        # Get information from GET request and determine type of get request
        # get request from searching for galleries
        search = request.args.get("q")
        # GET request from searching works by specific artist
        artist = request.args.get("a")
        # Query databse for top searched galleries to load on page/with search bar
        top_sites = db.execute("SELECT * from galleries JOIN users ON users.user_id = galleries.user_id ORDER BY views DESC LIMIT 3")

        # If user tries to force a GET request with both artist and gallery query through URL:
        if artist and search:
            # search database for galleries based on gallery names and artist name
            gallery_info = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id WHERE gallery_name LIKE ?",'%' + search + '%' )
            artist_search = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id WHERE username LIKE ?",'%' + artist + '%' )
            # Concatonate list of galleries from artist search
            for i in artist_search:
                gallery_info.append(i)
            # return search page with all queries
            return render_template("search.html", galleries=gallery_info,top_sites=top_sites)

        # If GET request is for gallery search only:
        if search:
            # Querey database for galleries that contain search query characters
            gallery_info = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id WHERE gallery_name LIKE ?",'%' + search + '%' )
            # If not galleries with such a name, return error and redirect
            if not gallery_info:
                flash("No galleries with this name")
                return redirect("/")
            # Load search page with search results
            return render_template("search.html", galleries=gallery_info, top_sites=top_sites)

         # If GET request is for searching works by a particular artist only:
        if artist:
            gallery_info = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id WHERE username LIKE ?",'%' + artist + '%' )
            if not gallery_info:
                flash("Invalid Search")
                return redirect("/")
            # Load search page with search results
            return render_template("search.html", galleries=gallery_info,top_sites=top_sites)

        # Return error if other type of GET quest is attempted
        else:
            flash("Invalid Search")
            return redirect("/")

    # Use POST request from "Search All Galleries" Button to load all galleries saved on website
    # Use Post request so that all get request possibilities can be used by users without diluting galleries that may have names
    # related to "all" or "galleries"
    if request.method == "POST":
        # Query databse for top searched galleries to load on page/with search bar
        top_sites = db.execute("SELECT * from galleries JOIN users ON users.user_id = galleries.user_id ORDER BY views DESC LIMIT 3")
        # Retrieve all galleries from database and load on search page
        gallery_info = db.execute("SELECT * FROM galleries JOIN users ON users.user_id = galleries.user_id ORDER BY views DESC")
        return render_template("search.html", galleries=gallery_info, top_sites=top_sites)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """ Show edit page to edit galleries by user """

    # Use GET request to easily and uniquely got to each gallery edit page
    if request.method == "GET":
        # Obtain gallery_ID from get request and retrieve gallery info from database
        gallery_id = request.args.get("g")
        gallery_info = db.execute("SELECT * FROM galleries WHERE gallery_id = ?", gallery_id)

        # If user attempting to access edit page is not creator, redirect to gallery page
        if gallery_info[0]['user_id'] != session["user_id"]:
            return redirect("/gallery?g=" + gallery_id)

        # Extract photos from database to load on edit page
        photos = extract_pictures(gallery_id, "gal")

        # Retrieve comments from database
        comments = db.execute("SELECT * FROM comments WHERE gallery_id = ? ORDER BY timestamp", gallery_id)

        # If no comments, load page without comments section
        if len(comments) <= 0:
            return render_template("edit.html", galleries=gallery_info, photos=photos)

        # Otherwise load page with comments section
        return render_template("edit.html", galleries=gallery_info, photos=photos, state=1, comments=comments)

### Gallery/Edit Update Features ###

@app.route("/upgalnm", methods=["GET", "POST"])
@login_required
def upgalnm():
    """ redirect link to change gallery name """

    if request.method == "POST":
        # retrieve info from form:
        gallery_name = request.form.get("gallery_name")
        gallery_id = request.form.get("gallery_id")

        # If no name provided for gallery, flash error and reload
        if not gallery_name or gallery_name == " ":
            flash('Please provide new gallery title')
            return redirect("/edit?g=" + gallery_id)

        # Ensure gallery name not previosuly used by user
        verify = db.execute("SELECT * from galleries WHERE gallery_name = ? AND user_id = ?", gallery_name, session["user_id"])
        # if gallery name already used by user, flash error and reload page
        if len(verify) >=1:
            flash('Gallery title already in use')
            return redirect("/edit?g=" + gallery_id)

        # Update galleries database with new name
        db.execute("UPDATE galleries SET gallery_name = ? WHERE gallery_id = ?", gallery_name, gallery_id)
        return redirect("/edit?g=" + gallery_id)
    else:
        return redirect("/")


@app.route("/updatephotos", methods=["GET", "POST"])
@login_required
def updatephotos():
    """ Update photo name """
    if request.method == "POST":
        # Pass values from form submission
        photo_name = request.form.get("photo_name")
        photo_id = request.form.get("photo_id")
        gallery_id = request.form.get("gallery_id_2")

        # if photo name is not provided, flash error and reload page
        if not photo_name or photo_name == " ":
            flash('Please provide photo title')
            return redirect("/edit?g=" + gallery_id)

        # if photo name is already used in gallery, flash error and reload page
        verify = db.execute("SELECT * from photos WHERE gallery_id = ? AND photo_name = ?", gallery_id, photo_name)
        if len(verify) >=1:
            flash('Photo name already in use in this gallery')
            return redirect("/edit?g=" + gallery_id)

        # Update photo name and reload edit page
        db.execute("UPDATE photos SET photo_name = ? WHERE photo_id = ?", photo_name, photo_id)
        return redirect("/edit?g=" + gallery_id)
    else:
        return redirect("/")


@app.route("/deletegal", methods=["GET", "POST"])
@login_required
def deletegal():
    """ Delete gallery feature """
    # Use POST request to initiate gallery deletion
    if request.method == "POST":
        # Pass gallery_id from form
        gallery_id = request.form.get("gallery_id")
        # Delete all photos from photos database that belong to gallery
        db.execute("DELETE FROM photos WHERE gallery_id = ?", gallery_id)
        # Delete gallery from gallery database
        db.execute("DELETE FROM galleries WHERE gallery_id = ?", gallery_id)
        # Redirect
        return redirect("/")


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """ Upload new photo to gallery """

    if request.method == "POST":
        # Pass information from table
        gallery_id = request.form.get("gallery_id")
        photo_name = request.form.get("photo_name")
        f = request.files['photo']

        # If photo name is not provided flash error and reload
        if not photo_name or photo_name == " ":
            flash("Please provide new photo name before uploading")
            return redirect("/edit?g="+gallery_id)

        # If photo name already used in gallery, flash error and reload
        verify = db.execute("SELECT * from photos WHERE gallery_id = ? AND photo_name = ?", gallery_id, photo_name)
        if len(verify) >=1:
            flash('Photo name already in use in this gallery')
            return redirect("/edit?g=" + gallery_id)

        # If file not provided, flash error and reload
        if f.filename == '':
            flash('Please provide ".jpeg" file to upload')
            return redirect("/edit?g=" + gallery_id)

        # Save file and insert into database
        f.save(secure_filename(f.filename))
        insert_picture(f.filename.replace(" ", "_"), photo_name, gallery_id, session["user_id"])
        os.remove(f.filename)

        # Provide confirmation that photo uploaded and reload page
        flash("Photo Successfully Uploaded")
        return redirect("/edit?g="+gallery_id)
    else:
        return redirect("/")

@app.route("/uploadprofile", methods=["GET", "POST"])
@login_required
def uploadprofile():
    """ Upload profile picture and bio """
    if request.method == "POST":

        # Get user_id
        user_id = session["user_id"]

        # Pass profile info from form
        profile_info = request.form.get("profile_info")
        f = request.files['profile_pic']

        # If profile_pic fiel not provided, flash error and reload
        if f.filename == '':
            flash('Please provide ".jpeg" file to upload')
            return redirect("/")

        # If bio not provided, flash error and reload
        if not profile_info or profile_info == " ":
            flash("Please provide profile info")
            return redirect("/")

        # Otherwise save file, upload it to database
        # Temporarily save photo on codespace
        f.save(secure_filename(f.filename))
        # Open saved file, save file as blob, and upload into users database
        with open(f.filename.replace(" ", "_"), 'rb') as input_file:
            blob = input_file.read()
            db.execute("UPDATE users SET profile_pic = ?, profile_info = ? WHERE user_id = ?", blob, profile_info, user_id)
        # delete from codespace
        os.remove(f.filename)

        # Flash confirmation and reload
        flash("Profile Info Uploaded")
        return redirect("/")
    else:
        return redirect("/")

@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    """ Submit comment to gallery page """
    if request.method == "POST":
        # Pass values from form:
        gallery_id = request.form.get("gallery_id")
        comment = request.form.get("comment")

        # If no comment provided, flash error and reload page
        if not comment:
            flash("Invalid Comment Entry")
            return redirect("/edit?g="+gallery_id)

        # Otherwise insert comment into comment table
        db.execute("INSERT INTO comments (comment, gallery_id) VALUES (?, ?)", comment, gallery_id)
        return redirect("/edit?g="+gallery_id)
    else:
        return redirect("/")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """ Delete photo from gallery """

    if request.method == "POST":
        # Retrieve data from form
        gallery_id = request.form.get("gallery_id_2")
        photo_id = request.form.get("photo_id")
        # detlete photo from photos database
        db.execute("DELETE FROM photos WHERE photo_id = ? AND gallery_id = ?", photo_id, gallery_id)
        # redirect back to page
        return redirect("/edit?g=" + gallery_id)
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