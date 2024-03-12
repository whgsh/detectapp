from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
from detector import Detector
import os
from datetime import datetime
import base64
import time
app = Flask(__name__)

detector = None  # 初始化 detector 为 None

@app.route('/')
def index():
    # 首页，提供链接到配置页面
    return render_template('index1.html')

def save_local_file(file):
    try:
        filename = file.filename
        # 确保文件保存在 static 目录下的 uploads 文件夹中
        file_path = os.path.join('static', 'uploads', filename)
        file.save(file_path)
        return os.path.join('uploads', filename)  # 返回相对于 static 文件夹的路径
    except Exception as e:
        print(e)
        return None

def validate_camera_matrix(matrix):
    # 检查是否为二维列表且每一行列表长度为3
    if not isinstance(matrix, list) or not all(isinstance(row, list) and len(row) == 3 for row in matrix):
        return False
    # 检查每个元素是否为数字
    for row in matrix:
        if not all(isinstance(item, (int, float)) for item in row):
            return False
    return True

def validate_camera_extrinsic(extrinsic):
    # 检查是否为长度为5的列表
    if not isinstance(extrinsic, list) or len(extrinsic) != 5:
        return False
    if not all(isinstance(item, float) for item in extrinsic):
        return False
    return True


@app.route('/configure', methods=['GET', 'POST'])
def configure():
    global detector
    # 确保 uploads 文件夹存在
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file_path = None  # 在这里初始化 file_path

    if request.method == 'POST':
        camera_matrix_string = request.form['camera_matrix']
        camera_matrix = parse_camera_matrix_o(camera_matrix_string)
        print(camera_matrix)
        if not validate_camera_matrix(camera_matrix):
            return "Error: camera_matrix is not valid", 400

        # Parse the camera extrinsic parameters
        camera_extrinsic_string = request.form['camera_extrinsic']
        camera_extrinsic = parse_camera_matrix(camera_extrinsic_string)
        print(camera_extrinsic)
        if not validate_camera_extrinsic(camera_extrinsic):
            return "Error: camera_extrinsic is not valid", 400

        url = None
        # 检查是否有文件被上传
        if 'local_video' in request.files:
            file = request.files['local_video']
            if file.filename != '':
                file_path = save_local_file(file)
                if file_path is None:
                    return "Error saving file", 500
                # 构建用于访问上传文件的 URL
                url = url_for('static', filename=file_path)

        # 如果没有上传文件，则尝试获取其他表单字段
        if url is None:
            url = request.form.get('url')
        
        height_factor = float(request.form.get('height_factor'))
        pixel_factor = float(request.form.get('pixel_factor'))

        # 使用用户提供的参数创建 Detector 实例
        if file_path:  # 确保 file_path 已经被定义
            video_path = os.path.join(app.root_path, 'static', file_path)
            detector = Detector(video_path,camera_matrix,camera_extrinsic)
        else:
            detector = Detector(url,camera_matrix,camera_extrinsic)  # 如果没有文件路径，使用 URL
        detector.set_parameters(height_factor, pixel_factor)
        
        # 重定向到显示页面
        return redirect(url_for('display'))
    else:
        # GET 请求时，也需要传递可能存在的文件URL
        return render_template('con.html', file_url=None)
    
def parse_camera_matrix_o(input_string):
    # 去除字符串中的空格和中括号
    input_string = input_string.replace(' ', '').replace('[', '').replace(']', '')
    # 按照逗号分割字符串
    elements = input_string.split(',')
    # 将分割后的字符串转换为浮点数，并按照每3个一组分割成子列表
    matrix = [list(map(float, elements[i:i+3])) for i in range(0, len(elements), 3)]
    return matrix

def parse_camera_matrix(input_string):
    matrix = None
    rows = input_string.strip().split('\n')  # Split the string into rows
    for row in rows:
        # Remove any brackets and extra spaces, then split by comma
        elements = row.replace('[', '').replace(']', '').strip().split(',')
        # Convert each element to float and append to the matrix
        row_values = []
        for element in elements:
            element = element.strip()
            if element:  # Check if the element is not an empty string
                row_values.append(float(element))
        #
    return row_values



@app.route('/display')
def display():
    if detector is None:
        return "Detector is not configured. Please configure it first.", 400
    magnified_frame, amplitude, frequency = detector.get_latest_data()
    print(amplitude,frequency)
    frame_b64 = ''
    if magnified_frame is None or magnified_frame.size == 0:
        # 可以选择返回一个默认的占位图像
        print('no pic')

    else:
        frame_b64 = magnified_frame
    return render_template('display1.html', frame_b64=frame_b64, amplitude=amplitude, frequency=frequency)

def write_data_to_file(amplitude, frequency):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    with open('data.txt', 'a') as file:  # 'a' 模式表示追加数据
        file.write(f"{current_time}, {amplitude} mm, {frequency} Hz\n")

def gen_original_frames():
    # 打开视频捕获设备
    global detector
    cap = cv2.VideoCapture(detector.url)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(width,height)
    skip_frames = 2  # 跳过的帧数
    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.5)  # 暂停0.1秒后重试
            continue
        # 编码视频帧为 JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # 使用生成器返回帧
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # 跳过指定数量的帧
        time.sleep(0.1)
        
    cap.release()

def gen_frames():
    # 生成视频流的帧
    global detector
    while True:
        start_time = time.time()
        success, magnified_frame,frequency,amplitude, = detector.process_frame()
        end_time = time.time()
        if not success:
            break
        write_data_to_file(amplitude, frequency)
        ret, buffer = cv2.imencode('.jpg', magnified_frame)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Processing time for one frame: {elapsed_time:.2f} seconds")
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/original_video_feed')
def original_video_feed():
    # 视频流路由
    if detector is None or not detector.cap.isOpened():
        return "Detector is not configured or video source not opened.", 400
    return Response(gen_original_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed')
def video_feed():
    # 视频流路由
    if detector is None:
        return "Detector is not configured.", 400
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/data')
def data():
    # 提供振幅和频率数据
    if detector is None:
        return {'error': 'Detector not initialized'}, 400
    pic_base64, amplitude, frequency = detector.get_latest_data()
    return { 'amplitude': amplitude, 'frequency': frequency}

if __name__ == '__main__':
    app.run(debug=True)
