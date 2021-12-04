from flask import Flask,render_template,request, url_for
from werkzeug.utils import secure_filename
from cs50 import SQL

app = Flask(__name__)
db = SQL("sqlite:///phototest.db")

def insert_picture(picture_file):
    with open(picture_file, 'rb') as input_file:
        blob = input_file.read()
        db.execute("INSERT INTO photos (gallery_id, photo_name, photo_file) VALUES (?, ?, ?)", 1, "photo", blob)

def extract_picture(picture_id):
    photo_data = db.execute("SELECT photo_file, photo_name FROM photos WHERE photo_id = ?", picture_id)    
    blob = photo_data[0]['photo_file']
    f = photo_data[0]['photo_name']
    filename = f + '.jpg'
    with open(filename, 'wb') as output_file:
        output_file.write(blob)

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
        picture = extract_picture(1)
        return render_template('form.html', screenload=screenload, picture=picture)
 
app.run(host='localhost', port=5000)