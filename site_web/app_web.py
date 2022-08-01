import os
from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename
app_web = Flask(__name__)

app_web.config['UPLOAD_EXTENSIONS'] = ['.gw']
app_web.config['UPLOAD_PATH'] = 'uploads'

@app_web.route('/')
def index():
    return render_template('index.html')

@app_web.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app_web.config['UPLOAD_EXTENSIONS']:
            abort(400)
        uploaded_file.save(os.path.join(app_web.config['UPLOAD_PATH'], filename))
    return redirect(url_for('index'))


if __name__ == "__main__":
    app_web.run(debug=True, port=5001)