# 1. Python 3.10을 기반으로 한 슬림 이미지 사용
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 프로젝트 파일을 컨테이너에 복사
COPY . /app

# 4. pip 업그레이드 및 의존성 설치
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 5. FastAPI가 사용할 포트 열기
EXPOSE 8000

# 6. 서버 실행 명령 (main.py 기준, FastAPI 앱 인스턴스는 app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]