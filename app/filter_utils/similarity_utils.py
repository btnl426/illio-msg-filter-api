# ✅ filter_utils/similarity_utils.py
import numpy as np
import torch
import time

from datetime import datetime
from app.database import get_connection
from scipy.spatial.distance import cdist
from transformers import AutoTokenizer, AutoModel


# 사전 로딩
MODEL_PATH = "models/embedding_models/jhgan_ko-sbert-multitask"
# 모델 경로에서 이름만 추출
model_name = MODEL_PATH.split("/")[-1]

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModel.from_pretrained(MODEL_PATH)

def get_sentence_embedding(model, tokenizer, sentence):
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.squeeze().numpy()

def insert_sensitive_word(user_id: str, sentence: str):
    embedding = get_sentence_embedding(model, tokenizer, sentence)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. sensitive_words 테이블에 단어 존재 여부 확인
        cursor.execute(
            "SELECT word_id FROM sensitive_words WHERE word = ? AND model_name = ?",
            (sentence, model_name)
        )
        row = cursor.fetchone()
        
        if row:
            word_id = row.word_id
        else:
            # 2. 없으면 새로 등록
            cursor.execute("""
                INSERT INTO sensitive_words (word, embedding, model_name)
                OUTPUT INSERTED.word_id
                VALUES (?, ?, ?)
            """, (sentence, embedding.tobytes(), model_name))

            row = cursor.fetchone()
            if row and row[0] is not None:
                word_id = int(row[0])
                # print("✅ 새로 등록된 word_id:", word_id)
            else:
                print("❌ word_id를 가져오지 못했습니다")

            conn.commit()

        # 3. user_sensitive_words에 (user_id, word_id) 삽입 시도 (중복 확인)
        cursor.execute("""
            SELECT 1 FROM user_sensitive_words WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        relation = cursor.fetchone()

        if not relation:
            cursor.execute("""
                INSERT INTO user_sensitive_words (user_id, word_id)
                VALUES (?, ?)
            """, (user_id, word_id))
            conn.commit()

        return {"status": "success", "word_id": word_id}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()
        
def get_sensitive_words_by_user(user_id: str) -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT sw.word
            FROM sensitive_words sw
            JOIN user_sensitive_words usw ON sw.word_id = usw.word_id
            WHERE usw.user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        return [row.word for row in rows]
    
    finally:
        conn.close()


def check_message_similarity(user_id: str, message: str, threshold: float = 0.8):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        start_time = time.time()

        # 1. 민감 단어와 embedding 동시 조회
        cursor.execute("""
            SELECT sw.word, sw.embedding
            FROM sensitive_words sw
            JOIN user_sensitive_words usw ON sw.word_id = usw.word_id
            WHERE usw.user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        if not rows:
            return {"status": "no_sensitive_words", "match": False}

        words = []
        embeddings = []
        for word, emb in rows:
            words.append(word)
            embeddings.append(np.frombuffer(emb, dtype=np.float32))

        # 2. 메시지 임베딩
        message_embedding = get_sentence_embedding(model, tokenizer, message).reshape(1, -1)

        # 3. 유사도 계산
        similarities = 1 - cdist(message_embedding, embeddings, metric='cosine')[0]
        max_index = int(np.argmax(similarities))
        max_similarity = float(similarities[max_index])
        most_similar_word = words[max_index]

        elapsed = time.time() - start_time

        return {
            "status": "checked",
            "max_similarity": max_similarity,
            "most_similar_word": most_similar_word,
            "threshold": float(threshold),
            "match": max_similarity >= threshold,
            "inference_time": round(elapsed, 4)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()
        

def remove_user_sensitive_word(user_id: str, sentence: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 해당 단어의 word_id 조회
        cursor.execute("""
            SELECT word_id FROM sensitive_words WHERE word = ?
        """, (sentence,))
        row = cursor.fetchone()
        if not row:
            return False

        word_id = row[0]

        # 1. user_sensitive_words에서 연결 삭제
        cursor.execute("""
            DELETE FROM user_sensitive_words
            WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        deleted = cursor.rowcount > 0

        if deleted:
            # 2. 해당 word_id를 참조하는 다른 유저가 있는지 확인
            cursor.execute("""
                SELECT COUNT(*) FROM user_sensitive_words WHERE word_id = ?
            """, (word_id,))
            count = cursor.fetchone()[0]

            # 3. 없으면 민감 단어 테이블에서 삭제
            if count == 0:
                cursor.execute("""
                    DELETE FROM sensitive_words WHERE word_id = ?
                """, (word_id,))

        conn.commit()
        return deleted

    except Exception as e:
        conn.rollback()
        print("❌ 삭제 중 에러:", e)
        return False

    finally:
        conn.close()