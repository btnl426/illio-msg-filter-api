#!/bin/bash
set -e  # 오류 발생 시 즉시 종료

echo "📦 리소스 다운로드 및 설치 시작..."

# embedding model 다운로드 및 압축 해제
echo "🔽 jhgan_ko-sbert-multitask.zip 다운로드 중..."
gdown 1uMvdLq-tSyD4lJxorx6JTBRMw4fgFzF9 -O jhgan_ko-sbert-multitask.zip
mkdir -p models/embedding_models
unzip -oq jhgan_ko-sbert-multitask.zip -d models/embedding_models
rm jhgan_ko-sbert-multitask.zip

# sentiment model 다운로드 및 압축 해제
echo "🔽 daekeun-ml_koelectra-small-v3-nsmc.zip 다운로드 중..."
gdown 1EKrM76na8EVjCanmiiJq3vMU5j9UKKp2 -O daekeun_model.zip
mkdir -p models/sentiment_models
unzip -oq daekeun_model.zip -d models/sentiment_models
rm daekeun_model.zip

# macOS 쓰레기 파일 제거
echo "🧹 macOS 잔여 파일 정리 중..."
find models -name '__MACOSX' -type d -exec rm -rf {} +
find models -name '._*' -type f -exec rm -f {} +

# mecab-ko.tar.gz 다운로드
echo "🔽 mecab-ko.tar.gz 다운로드 중..."
gdown 1axkwZqM98WcVyQkZFSCa3hmkUvY8CO8h -O mecab-ko.tar.gz

# mecab-ko-dic.tar.gz 다운로드
echo "🔽 mecab-ko-dic.tar.gz 다운로드 중..."
gdown 1NDNs9pgQnnmRPO2iufUAvDIWXZsczEyq -O mecab-ko-dic.tar.gz

# 설치
echo "⚙️ MeCab 설치 시작"
cd /tmp
tar -xzvf /app/mecab-ko.tar.gz
cd mecab-ko
./configure --build=aarch64-unknown-linux-gnu
make -j"$(nproc)"
make install
cd /app  # 원래 디렉토리로 복귀

# 사전 설치
echo "📚 MeCab 사전 설치 중..."
mkdir -p /usr/local/lib/mecab/dic/
tar -xzvf /app/mecab-ko-dic.tar.gz -C /usr/local/lib/mecab/dic/
ln -sf /usr/local/lib/mecab/dic/mecab-ko-dic /usr/local/lib/mecab/dic/default

echo "🎉 다운로드 및 설치 완료!"