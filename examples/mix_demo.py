import cv2

def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0)

    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("Error: 无法打开摄像头.")
        return

    # 读取摄像头画面并显示
    while True:
        ret, frame = cap.read()

        if ret:
            # 在窗口中显示摄像头画面
            cv2.imshow('Camera', frame)

        # 按下 'q' 键退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 关闭摄像头
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
