from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
from cs50 import SQL

app = Flask(__name__)
db = SQL("sqlite:///phototest.db")

def insert_picture(picture_file):
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file) VALUES (?, ?, ?)", 1, "photo", blob)

def extract_picture(picture_id):
    db.execute("SELECT photo, photo_name FROM photos WHERE photo_id = ?", picture_id)    
    sql = "SELECT PICTURE, TYPE, FILE_NAME FROM PICTURES WHERE id = :id"
    param = {'id': picture_id}
    cursor.execute(sql, param)
    ablob, ext, afile = cursor.fetchone()
    filename = afile + ext
    with open(filename, 'wb') as output_file:
        output_file.write(ablob)
    return filename


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