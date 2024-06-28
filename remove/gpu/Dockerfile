# CUDA와 cuDNN이 포함된 베이스 이미지
FROM nvidia/cuda:11.2.2-cudnn8-devel-ubuntu20.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libdb5.3-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    tk-dev \
    libffi-dev \
    libnss3-dev \
    libedit-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 3.10 소스 다운로드 및 빌드
RUN wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz \
    && tar -xf Python-3.10.0.tgz \
    && cd Python-3.10.0 \
    && ./configure --enable-optimizations \
    && make -j$(nproc) \
    && make altinstall \
    && cd .. \
    && rm -rf Python-3.10.0 Python-3.10.0.tgz

# 심볼릭 링크 설정
RUN ln -s /usr/local/bin/python3.10 /usr/local/bin/python3 \
    && ln -s /usr/local/bin/pip3.10 /usr/local/bin/pip3

# Google Chrome 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chromedriver 복사 및 압축 해제
COPY chromedriver_linux /usr/local/bin/
RUN chmod +x /usr/local/bin/chromedriver_linux

# 필요한 Python 패키지 설치
RUN pip3 install selenium

# 스크립트를 컨테이너로 복사
COPY index.py /index.py

# 스크립트를 실행하는 명령 설정
CMD ["sh", "-c", "python3 /index.py & tail -f /dev/null"]
