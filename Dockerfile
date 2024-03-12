# 使用NVIDIA L4T ML基础镜像
FROM nvcr.io/nvidia/l4t-ml:r32.6.1-py3

#设置工作目录
WORKDIR /usr/src/app

RUN wget -O /etc/apt/sources.list https://repo.huaweicloud.com/repository/conf/Ubuntu-Ports-bionic.list && apt-get update
#安装Node.js
RUN apt-get update && apt-get install -y nodejs npm

#检查Node.js 和 npm 的安装
RUN node -v && npm -v

#复制Python依赖文件
COPY requirements.txt .

#安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#复制应用程序文件
COPY . .

#设置启动命令
CMD [ "python3", "./app.py" ]