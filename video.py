import cv2
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import os
from PIL import Image, ImageTk

class VideoRecorder:
    def __init__(self, root):
        self.root = root
        self.is_recording = False
        self.cap = cv2.VideoCapture("http://192.168.188.75/8000")  # 0代表默认摄像头

        # 获取摄像头原始分辨率
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.frame = None

        # 设置GUI
        self.setup_gui()

        # 开始视频流
        self.video_stream()

    def setup_gui(self):
        self.root.title("网络摄像头视频流")
        self.root.geometry(f"{int(self.width)}x{int(self.height)}")

        self.video_label = tk.Label(self.root)
        self.video_label.pack()

        self.record_button = tk.Button(self.root, text="录制", command=self.toggle_recording)
        self.record_button.pack()

    def video_stream(self):
        _, self.frame = self.cap.read()
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)
        self.video_label.after(10, self.video_stream)

        if self.is_recording:
            self.record_video()

    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.config(text="录制")
        else:
            self.is_recording = True
            self.record_button.config(text="停止")
            self.record_thread = Thread(target=self.start_recording)
            self.record_thread.start()

    def start_recording(self):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 20.0, (int(self.width), int(self.height)))
        while self.is_recording:
            out.write(self.frame)
        out.release()

    def record_video(self):
        if not self.is_recording:
            return
        # 这里可以添加录制视频的代码

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定退出吗？"):
            self.cap.release()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoRecorder(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()