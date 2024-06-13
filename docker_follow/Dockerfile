FROM python:3.8-slim

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# 필요한 Python 패키지 설치
RUN pip install selenium

# 스크립트를 실행하는 명령 설정
CMD ["tail", "-f", "/dev/null"]
#CMD ["python", "/instahelp_web/docker_follow/follow_index.py"]