import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np

import face_recognition
from PyQt5.QtCore import QThread, pyqtSignal
from flask import Flask, request, redirect, jsonify

from examples.face_data_lite import FaceData

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image file was uploaded


    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>404 Not Found</title>
    <h1>404 Not Found!</h1>

    '''


@app.route('/new', methods=['GET', 'POST'])
def upload_new_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        user_name = request.form.get('username')
        student_id = request.form.get('student_id')
        face_id = request.form.get('face_id')


        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # The image file seems valid! Detect faces and return the result.
            return jsonify(add_new_faces_in_image(file,user_name,student_id,face_id))

    # If no valid image file was uploaded, show the file upload form:
    return '''
   <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Capture and Crop</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.12/cropper.min.css">
    <style>
        #preview {
            width: 100%;
            height: auto;
            margin-top: 20px;
        }
    </style>
</head>
<body>

         <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input name="username" value="username">
        <input name="student_id" value="student_id">
        <input name="face_id" value="face_id">
        <button type="submit">Upload File</button>
    </form>
</body>
</html>

    '''

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_new_faces_in_image(file_stream,username,student_id,face_id):
    now = datetime.now()
    timestamp = now.timestamp()

    filename = file_stream.filename
    img_path = 'face_image/' + student_id
    directory = Path(img_path)
    directory.mkdir(parents=True, exist_ok=True)
    img_path_save = os.path.join(student_id,username+str(timestamp)+'.'+os.path.splitext(filename)[-1].strip("."))
    file_stream.save(os.path.join(img_path,username+str(timestamp)+'.'+os.path.splitext(filename)[-1].strip(".")))
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)[0]
    face_data = FaceData("face_data.db")

    # write database
    is_exists = face_data.exists_user(str(student_id))
    if is_exists is False:
        face_data.create_user(str(student_id),username)
        face_data.add_face(str(face_id),str(student_id),json.dumps(unknown_face_encodings.tolist()),img_path_save)
    face_data.__del__()

    # Return the result as json
    result = {
        "msg": '添加成功',
        "code": 1
    }
    return result



app.run(host='0.0.0.0', port=15301, debug=True)

