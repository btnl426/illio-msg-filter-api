# 1. 베이스 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 프로젝트 파일 복사
COPY . /app

# 4. 시스템 패키지 설치
# ✅ konlpy는 JVM(Java)을 필요로 하므로 openjdk-11-jdk 추가
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

# 5. MeCab 본체 설치 (압축 파일 이용)
RUN cd /opt && \
    tar -xzvf /app/mecab-ko.tar.gz && \
    cd mecab-ko && \
    ./configure --build=aarch64-unknown-linux-gnu && \
    make && \
    make install

# 6. MeCab-Ko-Dic 설치
RUN mkdir -p /usr/local/lib/mecab/dic/ && \
    tar -xzvf /app/mecab-ko-dic.tar.gz -C /usr/local/lib/mecab/dic/ && \
    ln -s /usr/local/lib/mecab/dic/mecab-ko-dic /usr/local/lib/mecab/dic/default

# 7. Python 패키지 설치
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install mecab-python3 konlpy

# Microsoft ODBC 드라이버 설치 (충돌 방지 포함)
RUN apt-get remove -y libodbc2 libodbcinst2 unixodbc-common || true && \
    apt-get update && apt-get install -y gnupg2 && \
    mkdir -p /etc/apt/keyrings && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# 8. FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]