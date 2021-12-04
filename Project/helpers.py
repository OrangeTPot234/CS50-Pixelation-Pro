import os
import requests
import urllib.parse
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps
# Reference Websites: https://stackoverflow.com/questions/51301395/how-to-store-a-jpg-in-an-sqlite-database-with-python
# https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
# https://www.askpython.com/python-modules/flask/flask-file-uploading 

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

def insert_picture(picture_file, photo_name, gallery_id):
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file) VALUES (?, ?, ?)", gallery_id, photo_name, blob)