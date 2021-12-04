from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
 
app = Flask(__name__)

@app.route('/form')
def form():
    screenload = 0
    return render_template('form.html', screenload=screenload)
 
@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        screenload = 1
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return render_template('form.html', screenload=screenload)
 
app.run(host='localhost', port=5000)