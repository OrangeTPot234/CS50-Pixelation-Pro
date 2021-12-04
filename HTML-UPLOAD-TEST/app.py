from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
from cs50 import SQL
import sqlite3

app = Flask(__name__)
db = SQL("sqlite:///databases.db")

def insert_picture(picture_file):
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        #base=os.path.basename(picture_file)
        #afile, ext = os.path.splitext(base)
        #sql = '''INSERT INTO PICTURES
        #(PICTURE, TYPE, FILE_NAME)
        #VALUES(?, ?, ?);'''
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file) VALUES (?, ?, ?)", 1, "photo", blob)
        #db.execute(sql,[sqlite3.Binary(ablob), ext, afile]) 

@app.route('/')
def form():
    screenload = 0
    return render_template('form.html', screenload=screenload)
 
@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        screenload = 1
        print("If statement worked")
        f = request.files['file']
        f.save(secure_filename(f.filename))
        print("f.save worked")
        insert_picture(f.filename.replace(" ", "_"))
        print("Insert Picture Worked")
        return render_template('form.html', screenload=screenload)
 
app.run(host='localhost', port=5000)