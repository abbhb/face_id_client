import base64
import json
import os
import threading
import time

import cv2
import numpy

import face_recognition
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QUrl, pyqtSignal, QThread, QTimer, QDateTime, QProcess
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *

import sys

from examples.face_data_lite import FaceData

face_tip_text = "欢迎您使用人脸签到系统!"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# lunxun update
shared_variable = {
    'all_face_list': [],
    'all_face_ext': {},
}
# 创建一个锁，用于确保在访问共享变量时的线程安全性
shared_variable_lock = threading.Lock()


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


def detect_faces_in_image(type='file_stream', file_stream=None, imgn=None):
    # Load the uploaded image file
    img = []
    if type == 'file_stream':
        img = face_recognition.load_image_file(file_stream)
    elif type == 'img':
        img = imgn
    else:
        img = imgn
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img, model='large')

    face_data = []
    with shared_variable_lock:
        copy_faces = shared_variable["all_face_list"]
        copy_faces_ext = shared_variable["all_face_ext"]
    if len(unknown_face_encodings) > 0:
        face_found = True
        # See if the first face in the uploaded image matches the known face of Obama

        match_results,weizhi = face_recognition.compare_faces(copy_faces, unknown_face_encodings[0], 0.44)

        if match_results is False:
            return {"msg": '未找到人脸', "code": -1, "username": ""}
        zhegeface = copy_faces[weizhi]
        # Return the result as json
        print(zhegeface)
        print(face_data)

        result = {
            "code": 1,
            "msg": '找到脸了',
            "username": copy_faces_ext[tuple(zhegeface)]['username']
        }
        return result

    else:
        return {"msg": 'wufashibie', "code": -1, "username": ""}


class MainPanel(QWidget):
    def __init__(self):
        super(MainPanel, self).__init__()

        # 获取显示器分辨率
        self.desktop = QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.screenheight = self.screenRect.height()
        self.screenwidth = self.screenRect.width()

        print("Screen height {}".format(self.screenheight))
        print("Screen width {}".format(self.screenwidth))

        self.height = int(self.screenheight * 0.7)
        self.width = int(self.screenwidth * 0.7)

        self.resize(self.width, self.height)

        # self.resize(800, 600)
        # mainPanel_layout = QHBoxLayout()
        self.mainPanel_layout = QGridLayout()
        # 预览四个边都预留20pixs的边界
        self.mainPanel_layout.setContentsMargins(20, 20, 20, 20)
        # 网格之间设置10pixs的间隔
        self.mainPanel_layout.setSpacing(10)
        self.button_layout = QGridLayout()
        self.mainPanel_layout.addLayout(self.button_layout, 0, 1)


        # must init after
        self.init_button_ui()
        self.init_user_info_ui()

        self.one = onePanel()
        self.two = twoPanel()
        self.three = initDataPanel()
        self.successFaceWidget = successFaceWidget()
        self.qls = QStackedLayout()
        self.qls.setGeometry(QtCore.QRect(0, 0, 500, 600))

        self.qls.addWidget(self.one)
        self.qls.addWidget(self.two)
        self.qls.addWidget(self.three)
        self.qls.addWidget(self.successFaceWidget)

        self.mainPanel_layout.addLayout(self.qls, 0, 0)

        self.setLayout(self.mainPanel_layout)
        # init
        self.qls.setCurrentIndex(2)

        self.initDataWorkerThread = initDataWorkerThread()
        self.initDataWorkerThread.init_jindu_signal.connect(self.updateInitJindu)
        self.initDataWorkerThread.start()
        # 识别进程在数据初始化进度为100%时再启动
        self.captureThread = CaptureWorkerThread()
        self.captureThread.update_shibie_signal.connect(self.updateImage)
        self.captureThread.update_video_frame_signal.connect(self.updateFrameUser)
        self.captureThread.success_qiandao.connect(self.updateSuccessFace)
        # 热更新人脸识别线程
        self.update_face_data = UpdataFaceDataThread()
        #flask service thread
        self.flask_process = QProcess(self)
        self.flask_process.readyReadStandardOutput.connect(self.read_output)
        self.flask_process.start('python', ['flask_server.py'])
        # 注册设备到consul，并注册ip和端口，和设备id

    def read_output(self):
        output = self.flask_process.readAllStandardOutput().data().decode()
        if 'Running on' in output:
            print(output)
        else:
            print("-----------------")
            print(output)

    # def read_output(self):
    #     output = self.flask_process.readAllStandardOutput().data().decode()
    #     if 'Running on' in output:
    #         QMessageBox.information(self, 'Flask启动成功', output)
    def init_button_ui(self):
        self.button_layout.setContentsMargins(20, 20, 20, 20)
        # 网格之间设置10pixs的间隔
        self.button_layout.setSpacing(10)
        select_Panel1_button = QPushButton("panel1")
        select_Panel2_button = QPushButton("panel2")
        select_Panel3_button = QPushButton("panel3")
        select_Panel4_button = QPushButton("panel4")
        self.qlabel = QLabel()
        self.qlabel.setStyleSheet("QLabel{background:white;}"
                                      "QLabel{color:block;font-size:20px;font-weight:bold;font-family:宋体;}"
                                      )
        # 动态显示时间在label上
        self.qlabel.setText(face_tip_text)

        # 创建一个定时器
        self.succcess_timer = QTimer(self)
        self.succcess_timer.timeout.connect(self.success_executeAfterDelay)
        self.succcess_timer.setSingleShot(True)  # 设置为单次触发

        # qlabel.setMinimumSize(self.width * 0.1, self.height)
        # self.button_layout.addWidget(select_Panel1_button,4, 0)
        # self.button_layout.addWidget(select_Panel2_button, 5, 0)
        # self.button_layout.addWidget(select_Panel3_button, 6, 0)
        # self.button_layout.addWidget(select_Panel4_button, 7, 0)
        self.button_layout.addWidget(self.qlabel, 4, 0)
        select_Panel1_button.clicked.connect(lambda: self.buttonIsClicked(select_Panel1_button))
        select_Panel2_button.clicked.connect(lambda: self.buttonIsClicked(select_Panel2_button))
        select_Panel3_button.clicked.connect(lambda: self.buttonIsClicked(select_Panel3_button))
        select_Panel4_button.clicked.connect(lambda: self.buttonIsClicked(select_Panel4_button))

        self.init_time_ui()

    def init_time_ui(self):
        self.time_label = QLabel(self)
        self.time_label.setFixedWidth(300)
        self.time_label.move(90, 80)
        self.time_label.setStyleSheet("QLabel{background:white;}"
                                      "QLabel{color:rgb(300,300,300,120);font-size:20px;font-weight:bold;font-family:宋体;}"
                                      )
        # 动态显示时间在label上
        timer = QTimer(self)

        timer.timeout.connect(self.update_time_v)

        timer.start(1000)
        self.button_layout.addWidget(self.time_label, 0, 0)

    def init_user_info_ui(self):

        self.user_info_web_view = QWebEngineView()
        channel = QWebChannel()

        self.user_info_web_view.page().setWebChannel(channel)

        self.user_info_web_view.load(QUrl("file:///home/qc/PycharmProjects/face_id/examples/search.html"))
        # self.user_info_web_view.setStyleSheet("QLabel{background:white;}"
        #                                       "QLabel{color:rgb(300,300,300,120);font-size:20px;font-weight:bold;font-family:宋体;}"
        #                                       )


        self.user_info_web_view.setFixedWidth(300)
        self.user_info_web_view.setFixedHeight(300)


        # self.user_info_web_view.show()


        self.button_layout.addWidget(self.user_info_web_view,1,0,3,1)

    def success_executeAfterDelay(self):
        self.qlabel.setStyleSheet("QLabel{background:white;}"
                                  "QLabel{color:block;font-size:20px;font-weight:bold;font-family:宋体;}"
                                  )
        self.qlabel.setText(face_tip_text)

    def update_time_v(self):
        datetime = QDateTime.currentDateTime()
        text = datetime.toString()
        self.time_label.setText("     " + text)

    def buttonIsClicked(self, button):
        dic = {
            "panel1": 0,
            "panel2": 1,
            "panel3": 2,
            "panel4": 3,
        }
        index = dic[button.text()]
        self.qls.setCurrentIndex(index)

    def updateInitJindu(self, jindu: int):
        self.qls.setCurrentIndex(2)

        self.three.updateJindu(jindu)

        if jindu == 100:
            self.initDataWorkerThread.quit()
            self.qls.setCurrentIndex(0)

            self.captureThread.start()
            self.update_face_data.start()

    def updateFrameUser(self, base64: str):
        # self.qls.setCurrentIndex(0)
        # self.one.updateFrame(base64)
        # self.update_user_face()
        self.user_info_web_view.page().runJavaScript("showframe('" + base64 + "')")
    # def update_user_face(self,base64:str):



    def updateImage(self, base64: str):
        self.user_info_web_view.page().runJavaScript("showframe('" + base64 + "')")

        # self.two.update(base64)
        # self.qls.setCurrentIndex(1)

    def updateSuccessFace(self,status,yunbase64:str,username):
        self.succcess_timer.stop()
        if status:
            self.qlabel.setStyleSheet("QLabel{background:white;}"
                                      "QLabel{color:green;font-size:20px;font-weight:bold;font-family:宋体;}"
                                      )
            self.qlabel.setText("["+username+"]签到成功！")
            self.user_info_web_view.page().runJavaScript("success('" + yunbase64 + "')")
        else:
            self.user_info_web_view.page().runJavaScript("error_s()")
            self.qlabel.setStyleSheet("QLabel{background:white;}"
                                      "QLabel{color:red;font-size:20px;font-weight:bold;font-family:宋体;}"
                                      )
            self.qlabel.setText("签到失败，请重试！")


        self.succcess_timer.start(3000)
        pass


class onePanel(QWidget):
    def __init__(self):
        super(onePanel, self).__init__()
        self.setStyleSheet('''QWidget{background-color:#66CCFF;}''')

        self.onePanel_layout = QHBoxLayout()

        self.webview = QWebEngineView()

        self.webview.load(QUrl("https://webvpn.beihua.edu.cn"))

        # self.qlabel = QLabel("wait!!!!!!!!!!!!!!!!!")
        self.onePanel_layout.addWidget(self.webview)
        self.setLayout(self.onePanel_layout)

    def updateFrame(self, base64):
        # height, width, channel = frame.shape
        # bytesPerLine = 3 * width
        # qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        # pixmap = QPixmap.fromImage(qImg)
        # self.qlabel.setPixmap(pixmap)

        self.webview.page().runJavaScript("showframe('" + base64 + "')")


class twoPanel(QWidget):
    def __init__(self):
        super(twoPanel, self).__init__()
        self.setStyleSheet('''QWidget{background-color:#66ffcc;}''')

        twoPanel_layout = QHBoxLayout()
        self.webview = QWebEngineView()

        twoPanel_layout.addWidget(self.webview)
        self.webview.load(QUrl("file:///home/qc/PycharmProjects/face_id/examples/search.html"))
        self.setLayout(twoPanel_layout)

    def update(self, base64: str):
        # print(base64)
        self.webview.page().runJavaScript("document.getElementById('needImage').src = '" + base64 + "'")
        pass


class successFaceWidget(QWidget):
    def __init__(self):
        super(successFaceWidget, self).__init__()
        self.setStyleSheet('''QWidget{background-color:#66ffcc;}''')

        successFace_layout = QHBoxLayout()
        self.webview = QWebEngineView()

        successFace_layout.addWidget(self.webview)
        self.webview.load(QUrl("file:///home/qc/PycharmProjects/face_id/examples/search.html"))
        self.setLayout(successFace_layout)

    def update(self, base64: str):
        # print(base64)
        self.webview.page().runJavaScript("document.getElementById('needImage').src = '" + base64 + "'")
        pass


# init data time show
class initDataPanel(QWidget):
    def __init__(self):
        super(initDataPanel, self).__init__()
        # self.setStyleSheet('''QWidget{background-color:#ee0000;}''')

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar()

        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        # threePanel_layout = QHBoxLayout()
        self.qlabel = QLabel("init ...")

        self.verticalLayout.addWidget(self.qlabel)
        self.verticalLayout.addWidget(self.progressBar)
        self.statusbar = QtWidgets.QStatusBar()
        self.statusbar.setObjectName("statusbar")
        self.verticalLayout.addWidget(self.statusbar)
        # threePanel_layout = QHBoxLayout()
        # self.qlabel = QLabel("init ...")
        # threePanel_layout.addWidget(self.qlabel)

        self.setLayout(self.verticalLayout)

    def updateJindu(self, jindu: int):
        print(jindu)
        # self.qlabel.setText("init "+str(jindu)+"%")
        self.progressBar.setProperty("value", jindu)
        pass


class CaptureWorkerThread(QThread):
    # 定义一个带有参数的信号
    update_video_frame_signal = pyqtSignal(object)
    update_shibie_signal = pyqtSignal(str)
    success_qiandao = pyqtSignal(bool,str,str)

    def __init__(self):
        super().__init__()
        self.finishdata = True
        # 打开摄像头
        self.capture = cv2.VideoCapture(0)
        # 跳帧进行人脸
        self.frame_count = 0
        self.face_detection_interval = 5  # 每5帧执行一次人脸检测
        # 后台运行人脸检测模型
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def run(self):
        while True:
            if self.finishdata is False:
                print("init-cv2-data")
                continue
            #
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 帧计数器加1
                self.frame_count += 1
                # 检测人脸
                if self.frame_count % self.face_detection_interval == 0:
                    self.frame_count = 0
                    faces = self.face_cascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                    if len(faces) > 0:

                        # 找到最大的人脸
                        max_face = max(faces, key=lambda face: face[2] * face[3])

                        # 绘制矩形框标出最大的人脸位置
                        x, y, w, h = max_face
                        height, width, channel = frame.shape
                        if w * h > width * height * 0.24:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            # 裁剪出相应的人脸图像
                            face_image = frame[y:y + h, x:x + w]

                            # 绘制环形的背景图片
                            # self.draw_background_image()
                            # self.win.update_frame_video(frame)

                            # shibie
                            # self.win.updateImage()
                            _, buffer = cv2.imencode('.jpg', face_image)
                            face_image_base64 = base64.b64encode(buffer).decode('utf-8')
                            self.update_shibie_signal.emit('data:image/jpg;base64,' + face_image_base64)
                            # cv2.imwrite("tempimage.jpg", cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))

                            # 调用主线程的槽函数，以确保与Qt的事件循环协同工作
                            # self.win.update_ui_with_result()
                            jsons = detect_faces_in_image(type='img', imgn=np.array(face_image))
                            print(jsons["username"])
                            # 识别成功，进入双头像展示和右侧栏个人信息展示3s
                            if jsons["username"]:
                                self.success_qiandao.emit(True,'data:image/jpg;base64,' + face_image_base64,jsons["username"])
                            else:
                                self.success_qiandao.emit(False,'data:image/jpg;base64,' + face_image_base64,jsons["username"])

                            import time
                            time.sleep(2.3)

                            continue
                _, buffer = cv2.imencode('.jpg', frame)
                face_video_base64 = base64.b64encode(buffer).decode('utf-8')
                self.update_video_frame_signal.emit('data:image/jpg;base64,' + face_video_base64)


# init Data
class initDataWorkerThread(QThread):
    # 定义一个带有参数的信号
    init_jindu_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        dangqianjindu = 1
        self.init_jindu_signal.emit(dangqianjindu)
        all_face_list = []
        all_face_ext = {}
        face_data = FaceData("face_data.db")
        all_users_rows = face_data.list_all_user()
        user_info_map = {}
        for user in all_users_rows:
            user_info_map[user[0]] = {"username":user[1]}

        all_users_face_rows = face_data.list_all_user_face()
        # jindu + 1
        dangqianjindu += 5
        self.init_jindu_signal.emit(dangqianjindu)
        item_jindu = 50/len(all_users_face_rows)
        for user_face in all_users_face_rows:

            # jindu + item_jindu
            dangqianjindu += item_jindu
            self.init_jindu_signal.emit(dangqianjindu)
            # user_face is face
            try:
                face_data_ = numpy.array(json.loads(user_face[2]))
            except Exception as e:
                img = face_recognition.load_image_file(os.path.join('face_image',user_face["img"]))
                unknown_face_encodings = face_recognition.face_encodings(img)[0]
                face_data_ = unknown_face_encodings
            all_face_list.append(face_data_)
            all_face_ext[tuple(face_data_)] = {
                'username': user_info_map[user_face[1]]["username"],
                'student_id': user_face[1],
                'face_id': user_face[0],
                'img': user_face[3]
            }

            # print(image)
        with shared_variable_lock:
            shared_variable["all_face_list"] = all_face_list
            shared_variable["all_face_ext"] = all_face_ext
        self.init_jindu_signal.emit(99)
        # finish,100% jiu shi wan cheng le
        face_data.__del__()
        self.init_jindu_signal.emit(100)


class UpdataFaceDataThread(QThread):
    # 定义一个带有参数的信号

    def __init__(self):
        super().__init__()


    def run(self):
        while True:
            time.sleep(20)
            print("20s update")
            # every 10 min update face data once
            all_face_list = []
            all_face_ext = {}
            face_data = FaceData("face_data.db")
            all_users_rows = face_data.list_all_user()
            user_info_map = {}
            for user in all_users_rows:
                user_info_map[user[0]] = {"username": user[1]}

            all_users_face_rows = face_data.list_all_user_face()
            for user_face in all_users_face_rows:
                # user_face is face
                try:
                    face_data_ = numpy.array(json.loads(user_face[2]))
                except Exception as e:
                    img = face_recognition.load_image_file(os.path.join('face_image', user_face["img"]))
                    unknown_face_encodings = face_recognition.face_encodings(img)[0]
                    face_data_ = unknown_face_encodings
                all_face_list.append(face_data_)
                all_face_ext[tuple(face_data_)] = {
                    'username': user_info_map[user_face[1]]["username"],
                    'student_id': user_face[1],
                    'face_id': user_face[0],
                    'img': user_face[3]
                }

                # print(image)
            with shared_variable_lock:
                shared_variable["all_face_list"] = all_face_list
                shared_variable["all_face_ext"] = all_face_ext



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainPanel()
    main.show()
    sys.exit(app.exec_())
