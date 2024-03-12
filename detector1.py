import cv2
import numpy as np
from mag.magclass import MagMotion
from FastFlowNet.flowclass import Flow
from mag.config1 import Config
import base64

class CameraCalibration:
    def __init__(self, camera_matrix, dist_coefficients):
        self.camera_matrix = np.array(camera_matrix)
        self.dist_coefficients = np.array(dist_coefficients)

    def undistort(self, frame):
        return cv2.undistort(frame, self.camera_matrix, self.dist_coefficients)

class Detector:
    def __init__(self, url, camera_matrix, dist_coefficients):
        self.height_factor = 10.7
        self.pixel_factor = 9.5
        self.url = url
        self.cap = cv2.VideoCapture(self.url)
        self.frame = None
        self.prev = None
        self.amplitude_list = []  # 用于存储振幅值的列表
        self.frequency = 0
        self.amplitude = 0
        self.magnified_frame =None
        self.config = Config()
        self.calibrator = CameraCalibration(camera_matrix, dist_coefficients)
        self.mag_motion = MagMotion(self.config)
        self.flow_processor = Flow()

    def set_parameters(self, height_factor, pixel_factor):
        self.height_factor = height_factor
        self.pixel_factor = pixel_factor

    def process_frame(self):
        ret, frame = self.cap.read()
        retry_count = 0
        max_retries = 5

        while not ret and retry_count < max_retries:
            print(f"Failed to read frame, retrying {retry_count + 1}/{max_retries}...")
            self.cap.release()  # 释放当前的视频捕获对象
            self.cap = cv2.VideoCapture(self.url)  # 重新连接视频流
            ret, frame = self.cap.read()  # 再次尝试读取视频帧
            retry_count += 1
            
        if not ret:
            print("Failed to read frame.")
            return False, None, 0,0

        # 运动放大
        self.magnified_frame = self.mag_motion.update_and_magnify(frame)
        if self.magnified_frame is None:
            print("Magnified frame is None.")
            return False, None, None,None
        
        # 光流计算

        #flow = self.flow_processor.calculate_flow(self.magnified_frame)
        if self.prev is not None:  # 确保有前一帧可以用于计算光流
            # 将当前帧和前一帧转换为灰度图
            prev_gray = cv2.cvtColor(self.prev, cv2.COLOR_BGR2GRAY)
            gray = cv2.cvtColor(self.magnified_frame, cv2.COLOR_BGR2GRAY)
            # 计算稠密光流
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            # 更新前一帧
            self.prev = self.magnified_frame.copy()
        else:
            self.prev = self.magnified_frame.copy()
            flow = None
            
        if flow is not None:
            self.flow_processor.update_amplitude_list(flow)
            if len(self.flow_processor.amplitude_list) == self.flow_processor.N:
                self.frequency, self.amplitude = self.flow_processor.calculate_frequency_and_amplitude()
                
                if self.frequency is not None and self.amplitude is not None:
                    print(self.pixel_factor)
                    self.amplitude=self.pixel_factor*self.amplitude
                    print(f"Frequency: {self.frequency}, Amplitude: {self.amplitude}")
                    # self.amplitude_list.append(amplitude)
                    # if len(self.amplitude_list) > 30:
                    #     self.amplitude_list.pop(0)
                    # if self.amplitude_list:
                    #     self.frequency = self.calculate_frequency(self.amplitude_list)
                    # else:
                    #     self.frequency = 0
                else:
                    self.amplitude, self.frequency = 0, 0
                    print("no flow")
        else:
            self.amplitude, self.frequency = 0, 0
            print("not flow")
        # 返回运动放大后的视频帧和振幅和频率
        return True, self.magnified_frame, self.frequency,self.amplitude

    def get_latest_data(self):
        if self.magnified_frame is None:
            # 返回错误值的元组，而不是 None
            return None, 0.0, 0.0
        else:
            # 将图像转换为 base64 编码的字符串
            _, buffer = cv2.imencode('.jpg', self.magnified_frame)
            pic_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 确保振幅和频率是基本数据类型
            amplitude = float(self.amplitude) if self.amplitude is not None else 0.0
            frequency = float(self.frequency) if self.frequency is not None else 0.0
            
            return pic_base64, amplitude, frequency

# 如果需要，可以在这里添加 CameraCalibration 类的定义

# 使用示例
if __name__ == "__main__":
    # 定义相机内参和畸变系数
    camera_matrix = [[800, 0, 640], [0, 800, 360], [0, 0, 1]]
    dist_coefficients = [0.1, 0.01, 0, 0, 0]

    # RTSP视频流地址
    rtsp_url = "rtsp://admin:password01!@192.168.188.21:554/Streaming/Channels/601"

    # 创建Detector实例
    detector = Detector(rtsp_url, camera_matrix, dist_coefficients)

    # 设置参数（如果有必要）
    detector.set_parameters(height_factor=10.7, pixel_factor=9.5)

    # 循环处理视频帧
    while True:
        success,magnified_frame, frequency,amplitude = detector.process_frame()
        if not success:
            break
        print(detector.get_latest_data())
        # 展示放大后的视频帧
        cv2.imshow('Magnified Frame', magnified_frame)

        # 按 'q' 键退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    detector.cap.release()