import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView


class Printer(QObject):
    # pyqtSlot, 中文网络上大多称其为槽；其作用是接收网页发起的信号
    @pyqtSlot(str, result=str)
    def testTxt(self, content):
        print("输出文本:", content)
        return content


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 新增一个浏览器引擎
    browser = QWebEngineView()
    browser.setWindowTitle("My window")
    browser.resize(1000,600)
    # 增加一个通信中需要用到的频道
    channel = QWebChannel()
    # 通信过程中需要使用到的功能类
    printer = Printer()
    # 将功能类注册到频道中，注册名可以任意，但将在网页中作为标识
    channel.registerObject("printer", printer)
    # 在浏览器中设置该频道
    browser.page().setWebChannel(channel)
    # 内置的网页地址，此处采用的是本地的；远程同样可以使用
    url_string = "file:///home/qc/PycharmProjects/face_id/examples/search.html"
    browser.load(QUrl(url_string))
    browser.show()
    sys.exit(app.exec_())
