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
    """ Insert photo into photos database """
    # open provided file and read binary data into variable
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        # upload data into photos database with corresponding user_id, gallery_id, and photo name info
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file, user_id) VALUES (?, ?, ?, ?)", gallery_id, photo_name, blob, user_id)

def extract_pictures(search_id, query_type):
    # create empty list
    gallery_photos = []
    # If getting photos for gallery, search photos database by gallery_id
    if query_type == "gal":
        photo_info = db.execute("SELECT * FROM photos WHERE gallery_id = ?", search_id)
    # If getting photos for user, search photos database by user_id
    elif query_type == "user":
        photo_info = db.execute("SELECT * FROM photos WHERE user_id = ?", search_id)
    # If query type not provided return none and leave function
    else:
        return NONE
    # extract and save photo data for each image and save into list:
    for i in range(len(photo_info)):
        # create empty dictionary
        photo_names = {}
        # save file data as blob
        blob = photo_info[i]['photo_file']
        # give file name that corresponds to photo name
        f = photo_info[i]['photo_name']
        # define file path for the photos
        filename = 'static/photos/' + f + '.jpg'
        # open file and write in image data
        tf = open(filename, 'wb')
        tf.write(blob)
        # add photo name, filepath, and photo_id to list 
        photo_names["name"] = f
        photo_names["path"] = filename
        photo_names["photo_id"] = photo_info[i]['photo_id']
        gallery_photos.append(photo_names)
    # return list of filenames to be used/references
    return gallery_photos

def extract_profile_pic(profile_pic):
    """ extract profile pic """
    # Save provided binary data from database as blob
    blob = profile_pic
    # Save name of file as profile.jpg
    f = 'profile.jpg'
    # Define file path for photo
    filename = 'static/photos/' + f
    # open and write into file the binary file data
    tf = open(filename, 'wb')
    tf.write(blob)
    # return filename to be used
    return filename