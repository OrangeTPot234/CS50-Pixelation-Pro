import os
import requests
import urllib.parse
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps
# Reference Websites: https://stackoverflow.com/questions/51301395/how-to-store-a-jpg-in-an-sqlite-database-with-python
# https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
# https://www.askpython.com/python-modules/flask/flask-file-uploading 
# http://www.numericalexpert.com/blog/sqlite_blob_time/ 

GALLERY_PHOTOS = []

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

db = SQL("sqlite:///databases.db")

def insert_picture(picture_file, photo_name, gallery_id, user_id):
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file, user_id) VALUES (?, ?, ?, ?)", gallery_id, photo_name, blob, user_id)

def extract_pictures(search_id, query_type):
    gallery_photos = []
    if query_type == "gal":
        photo_info = db.execute("SELECT * FROM photos WHERE gallery_id = ?", search_id)
    elif query_type == "user":
        photo_info = db.execute("SELECT * FROM photos WHERE user_id = ?", search_id)
    else:
        return NONE
    for i in range(len(photo_info)):
        photo_names = {}
        blob = photo_info[i]['photo_file']
        f = photo_info[i]['photo_name']
        filename = 'static/' + f + '.jpg'
        tf = open(filename, 'wb')
        tf.write(blob)
        photo_names["name"] = f
        photo_names["path"] = filename
        photo_names["photo_id"] = photo_info[i]['photo_id']
        gallery_photos.append(photo_names)
    return gallery_photos