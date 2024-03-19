# This is a _very simple_ example of a web service that recognizes faces in uploaded images.
# Upload an image file and it will check if the image contains a picture of Barack Obama.
# The result is returned as json. For example:
#
# $ curl -XPOST -F "file=@obama2.jpg" http://127.0.0.1:5001
#
# Returns:
#
# {
#  "face_found_in_image": true,
#  "is_picture_of_obama": true
# }
#
# This example is based on the Flask file upload example: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

# NOTE: This example requires flask to be installed! You can install it with pip:
# $ pip3 install flask
import os
import face_recognition
from flask import Flask, jsonify, request, redirect

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

all_face_list = []#预存人脸信息列表
all_face_ext = {}#人脸跟信息绑定





def get_filename_without_extension(file_path):
    file_name_with_extension = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    return file_name_without_extension

def list_image_files(directory):
    image_files = []
    # 遍历目录中的所有文件和子目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 拼接文件的绝对路径
            file_path = os.path.join(root, file)
            image_files.append(file_path)
    return image_files



app = Flask(__name__)

image_files = list_image_files('./face_image')
for image in image_files:
    img = face_recognition.load_image_file(image)
    unknown_face_encodings = face_recognition.face_encodings(img)[0]
    file_name_without_extension = get_filename_without_extension(image)
    if file_name_without_extension == '':
        continue
    all_face_list.append(unknown_face_encodings)
    all_face_ext[tuple(unknown_face_encodings)] = {
        'username':file_name_without_extension
    }
    # print(image)



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # print(all_face_ext)
            # print(all_face_list)
            # The image file seems valid! Detect faces and return the result.
            return detect_faces_in_image(file)

    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>Is this a picture of Obama?</title>
    <h1>Upload a picture and see if it's a picture of Obama!</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    '''


@app.route('/new', methods=['GET', 'POST'])
def upload_new_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        user_name = request.form.get('username')


        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # The image file seems valid! Detect faces and return the result.
            return add_new_faces_in_image(file,user_name)

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
        <button type="submit">Upload File</button>
    </form>
</body>
</html>

    '''



def detect_faces_in_image(file_stream):
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)

    face_found = False
    is_obama = False
    face_data = []
    zhegeface = []
    copy_faces = all_face_list
    if len(unknown_face_encodings) > 0:
        face_found = True
        # See if the first face in the uploaded image matches the known face of Obama
        match_results = face_recognition.compare_faces(copy_faces, unknown_face_encodings[0],0.6)
        print(match_results)
        i = 0
        for matches in match_results:
            if matches:
               face_data.append(i)
            i+=1

        if len(face_data)>1:
            return jsonify({"msg":'多个人脸，请重试！'})
        if len(face_data)<1:
            return jsonify({"msg":'未找到人脸'})
        zhegeface = copy_faces[face_data[0]]

    print('找到人脸')

    print(zhegeface)
    # Return the result as json
    result = {
        "msg": '找到脸了',
        "username":all_face_ext[tuple(zhegeface)]['username']
    }
    return jsonify(result)


def add_new_faces_in_image(file_stream,username):


    filename = file_stream.filename
    file_stream.save(os.path.join('face_image', username+'.'+os.path.splitext(filename)[-1].strip(".")))
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)[0]
    all_face_list.append(unknown_face_encodings)
    all_face_ext[tuple(unknown_face_encodings)] = {username:username}


    # Return the result as json
    result = {
        "msg": '添加成功',
        "code": 1
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
