from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "/Files"

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
        return render_template('form.html', screenload=screenload)
 
app.run(host='localhost', port=5000)