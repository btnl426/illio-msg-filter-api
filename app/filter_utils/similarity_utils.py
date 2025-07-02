# ✅ filter_utils/similarity_utils.py
import numpy as np
import torch
import time
import os

from datetime import datetime
from app.database import get_connection, db_session
from scipy.spatial.distance import cdist
from transformers import AutoTokenizer, AutoModel


# 사전 로딩
embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH")

# 모델 경로에서 이름만 추출
model_name = embedding_model_path.split("/")[-1]

tokenizer = AutoTokenizer.from_pretrained(embedding_model_path)
model = AutoModel.from_pretrained(embedding_model_path)

def get_sentence_embedding(model, tokenizer, sentence):
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.squeeze().numpy()

def insert_sensitive_word(user_id: str, sentence: str):
    created = False  # 👉 새로 생성 여부 플래그

    with db_session() as conn:
        cursor = conn.cursor()

        # 1. 단어 존재 확인
        cursor.execute(
            "SELECT word_id FROM sensitive_words WHERE word = ? AND model_name = ?",
            (sentence, model_name)
        )
        row = cursor.fetchone()

        if row:
            word_id = row.word_id
        else:
            embedding = get_sentence_embedding(model, tokenizer, sentence)
            # 2. 없으면 등록
            cursor.execute("""
                INSERT INTO sensitive_words (word, embedding, model_name)
                OUTPUT INSERTED.word_id
                VALUES (?, ?, ?)
            """, (sentence, embedding.tobytes(), model_name))
            row = cursor.fetchone()
            if not row or row[0] is None:
                raise Exception("❌ word_id를 가져오지 못했습니다")
            word_id = int(row[0])
            created = True

        # 3. 관계 테이블 중복 확인 및 삽입
        cursor.execute("""
            SELECT 1 FROM user_sensitive_words WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO user_sensitive_words (user_id, word_id)
                VALUES (?, ?)
            """, (user_id, word_id))

        return {
            "word_id": word_id,
            "created": created
        }
        
def get_sensitive_words_by_user(user_id: str) -> list[str]:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sw.word
            FROM sensitive_words sw
            JOIN user_sensitive_words usw ON sw.word_id = usw.word_id
            WHERE usw.user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        return [row.word for row in rows]

def compute_similarity(message_embedding: np.ndarray, embeddings: list[np.ndarray]) -> tuple[float, int]:
    """
    메시지 임베딩과 민감 단어 임베딩들 간의 유사도 계산
    - cosine 유사도 기준
    - 가장 높은 유사도와 해당 인덱스 반환
    """
    similarities = 1 - cdist(message_embedding, embeddings, metric='cosine')[0]
    max_index = int(np.argmax(similarities))
    max_similarity = float(similarities[max_index])
    return max_similarity, max_index

def check_message_similarity(user_id: str, message: str, threshold: float):
    with db_session() as conn:
        cursor = conn.cursor()
        start_time = time.time()

        # 1. 사용자 민감 단어 조회
        cursor.execute("""
            SELECT sw.word, sw.embedding
            FROM sensitive_words sw
            JOIN user_sensitive_words usw ON sw.word_id = usw.word_id
            WHERE usw.user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        if not rows:
            return None

        # 2. 단어 리스트, 임베딩 파싱
        words = [row.word for row in rows]
        embeddings = [np.frombuffer(row.embedding, dtype=np.float32) for row in rows]

        # 3. 입력 메시지 임베딩
        message_embedding = get_sentence_embedding(model, tokenizer, message).reshape(1, -1)

        # 4. 유사도 계산 → 별도 함수 사용
        max_similarity, max_index = compute_similarity(message_embedding, embeddings)
        most_similar_word = words[max_index]
        elapsed = time.time() - start_time

        return {
            "max_similarity": max_similarity,
            "most_similar_word": most_similar_word,
            "threshold": float(threshold),
            "match": max_similarity >= threshold,
            "inference_time": round(elapsed, 4)
        }
        
def remove_user_sensitive_word(user_id: str, sentence: str) -> dict:
    with db_session() as conn:
        cursor = conn.cursor()

        try:
            # word_id 조회
            cursor.execute("SELECT word_id FROM sensitive_words WHERE word = ?", (sentence,))
            row = cursor.fetchone()
            if not row:
                return {"deleted": False, "reason": "not_found"}

            word_id = row[0]

            # 관계 삭제
            cursor.execute("""
                DELETE FROM user_sensitive_words
                WHERE user_id = ? AND word_id = ?
            """, (user_id, word_id))
            deleted = cursor.rowcount > 0

            if deleted:
                # 다른 유저가 쓰는지 확인하고 없으면 삭제
                cursor.execute("SELECT COUNT(*) FROM user_sensitive_words WHERE word_id = ?", (word_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM sensitive_words WHERE word_id = ?", (word_id,))

            return {"deleted": deleted, "word": sentence}

        except Exception as e:
            return {"deleted": False, "reason": str(e)}