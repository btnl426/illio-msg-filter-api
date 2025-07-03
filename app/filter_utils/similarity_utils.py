# ✅ filter_utils/similarity_utils.py
import numpy as np
import torch
import time
import os

from app.database import db_session
from db_models.similarity import SensitiveWord, UserSensitiveWord

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
    created = False

    with db_session() as session:
        # 1. 단어 존재 확인
        existing_word = session.query(SensitiveWord).filter_by(
            word=sentence,
            model_name=model.name_or_path  # 혹은 고정된 model_name 값
        ).first()

        if existing_word:
            word_id = existing_word.word_id
        else:
            embedding = get_sentence_embedding(model, tokenizer, sentence)
            new_word = SensitiveWord(
                word=sentence,
                embedding=embedding.tobytes(),
                model_name=model.name_or_path  # 혹은 고정 문자열
            )
            session.add(new_word)
            session.flush()  # word_id 가져오기 위해 flush
            word_id = new_word.word_id
            created = True

        # 2. 관계 테이블 중복 확인 및 삽입
        exists = session.query(UserSensitiveWord).filter_by(
            user_id=user_id,
            word_id=word_id
        ).first()

        if not exists:
            link = UserSensitiveWord(user_id=user_id, word_id=word_id)
            session.add(link)

        return {
            "word_id": word_id,
            "created": created
        }
        
def get_sensitive_words_by_user(user_id: str) -> list[str]:
    with db_session() as session:
        results = (
            session.query(SensitiveWord.word)
            .join(UserSensitiveWord, SensitiveWord.word_id == UserSensitiveWord.word_id)
            .filter(UserSensitiveWord.user_id == user_id)
            .all()
        )
        words = [row[0] for row in results]
        return {
            "words": words,
            "count": len(words)
        }

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
    with db_session() as session:  # SQLAlchemy 세션 사용
        start_time = time.time()

        # 1. 사용자 민감 단어 조회
        results = (
            session.query(SensitiveWord.word, SensitiveWord.embedding)
            .join(UserSensitiveWord, SensitiveWord.word_id == UserSensitiveWord.word_id)
            .filter(UserSensitiveWord.user_id == user_id)
            .all()
        )
        if not results:
            return None

        # 2. 단어 리스트, 임베딩 파싱
        words = [row[0] for row in results]
        embeddings = [np.frombuffer(row[1], dtype=np.float32) for row in results]

        # 3. 입력 메시지 임베딩
        message_embedding = get_sentence_embedding(model, tokenizer, message).reshape(1, -1)

        # 4. 유사도 계산
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
    with db_session() as session:
        try:
            # 1. 민감 단어 조회
            word_obj = session.query(SensitiveWord).filter_by(word=sentence).first()
            if not word_obj:
                return {"deleted": False, "reason": "not_found"}

            word_id = word_obj.word_id

            # 2. 관계 삭제
            link = session.query(UserSensitiveWord).filter_by(user_id=user_id, word_id=word_id).first()
            if not link:
                return {"deleted": False, "reason": "not_registered"}

            session.delete(link)
            session.commit()  # 커밋해야 rowcount 반영됨

            # 3. 다른 유저가 사용하는지 확인
            count = session.query(UserSensitiveWord).filter_by(word_id=word_id).count()
            if count == 0:
                session.delete(word_obj)
                session.commit()

            return {"deleted": True, "word": sentence}

        except Exception as e:
            session.rollback()
            return {"deleted": False, "reason": str(e)}
        
        
        
def remove_all_user_sensitive_words(user_id: str) -> dict:
    with db_session() as session:
        try:
            # 1. 유저가 등록한 모든 링크 조회
            links = session.query(UserSensitiveWord).filter_by(user_id=user_id).all()
            if not links:
                return {"deleted": False, "reason": "no_words"}

            deleted_words = []

            for link in links:
                word_id = link.word_id
                word_obj = session.query(SensitiveWord).filter_by(word_id=word_id).first()

                # 링크 삭제
                session.delete(link)

                # 단어가 다른 유저에게 사용되는지 확인
                remaining_links = session.query(UserSensitiveWord).filter_by(word_id=word_id).count()
                if remaining_links == 0 and word_obj:
                    session.delete(word_obj)

                if word_obj:
                    deleted_words.append(word_obj.word)

            session.commit()
            return {
                "deleted": True, 
                "words": deleted_words,
                "count": len(deleted_words)
            }

        except Exception as e:
            session.rollback()
            return {"deleted": False, "reason": str(e)}