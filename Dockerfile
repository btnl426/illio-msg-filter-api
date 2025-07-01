# 1. 베이스 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 프로젝트 파일 복사
COPY . /app

# 4. 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    default-jdk \
    build-essential \
    gcc \
    g++ \
    curl \
    make \
    cmake \
    unzip \
    automake \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libcurl4-openssl-dev \
    python3-dev \
    unixodbc \
    unixodbc-dev \
    wget

# 5. Python 패키지 및 gdown 설치
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install mecab-python3 konlpy gdown

# 6. 리소스 다운로드 및 설치 실행
RUN chmod +x setup.sh && ./setup.sh

# 7. Microsoft ODBC 드라이버 설치
RUN apt-get remove -y libodbc2 libodbcinst2 unixodbc-common || true && \
    apt-get update && apt-get install -y gnupg2 && \
    mkdir -p /etc/apt/keyrings && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# 8. FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]