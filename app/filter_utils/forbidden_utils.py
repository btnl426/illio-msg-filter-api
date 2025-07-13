# app/filter_utils/forbidden_utils.py

import hgtk
import time
import ahocorasick
from app.database import db_session
from db_models.forbidden import ForbiddenWord
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import app.state as state

from konlpy.tag import Mecab
# mecab = Mecab()
mecab = Mecab(dicpath="/opt/homebrew/Cellar/mecab-ko-dic/2.1.1-20180720/lib/mecab/dic/mecab-ko-dic")

exclude_for_jamo = set()

def decompose_text(text: str) -> str:
    return hgtk.text.decompose(text).replace('ᴥ', '')

def prepare_forbidden_entry(word: str) -> dict:
    decomposed = decompose_text(word)
    return {"word": word, "decomposed_word": decomposed}

def prepare_forbidden_entries(words: list[str]) -> list[dict]:
    return [{"word": word, "decomposed_word": decompose_text(word)} for word in words]


def get_existing_words(words: list[str]) -> set[str]:
    """금칙어 테이블에서 이미 등록된 단어 조회 (ORM 방식)"""
    if not words:
        return set()

    with db_session() as session:
        result = session.query(ForbiddenWord.word).filter(ForbiddenWord.word.in_(words)).all()
        return {
            str(row[0]).strip()
            for row in result
            if isinstance(row[0], str) and row[0].strip()
        }


def register_forbidden_word(word: str) -> dict:
    """금칙어 등록 함수 (단일) - ORM 방식"""
    existing_words = get_existing_words([word])
    if word in existing_words:
        return {"created": False, "word": word}

    decomposed = decompose_text(word)

    with db_session() as session:
        # ORM 객체 생성 및 추가
        new_entry = ForbiddenWord(word=word, decomposed_word=decomposed)
        session.add(new_entry)

        # 트라이 반영
        add_to_automaton(word, decomposed)

        return {
            "created": True,
            "word": word,
            "decomposed_word": decomposed
        }
        

def insert_bulk_forbidden_words(words: list[str]) -> dict:
    """
    여러 금칙어를 DB에 일괄 등록하고 트라이에 반영 (ORM 방식)
    - 중복 단어는 등록하지 않고 skipped로 안내
    - 에러 발생한 단어는 failed로 기록
    """
    # 1. 입력 정리: 공백 제거 + 중복 제거 + 빈 값 제거
    cleaned_words = list(set(w.strip() for w in words if w.strip()))

    if not cleaned_words:
        return {
            "registered": [],
            "skipped": [],
            "failed": [],
            "message": "⚠️ 등록할 유효한 단어가 없습니다."
        }

    # 2. 기존에 DB에 등록된 단어 조회
    existing_words = set(get_existing_words(cleaned_words))
    filtered_words = [w for w in cleaned_words if w not in existing_words]
    registered = []
    skipped = list(existing_words) 
    failed = []

    with db_session() as session:
        for word in filtered_words:
            try:
                decomposed = decompose_text(word)
                entry = ForbiddenWord(word=word, decomposed_word=decomposed)
                session.add(entry)
                session.flush()  # 중복 에러 조기 감지

                add_to_automaton(word, decomposed)
                registered.append(word)

            except IntegrityError:
                print(f"⚠️ 중복으로 스킵된 단어: '{word}'")
                if isinstance(word, str) and word.strip():  # ✅ 유효한 문자열일 때만 추가
                    skipped.append(word)
                session.rollback()

            except Exception as e:
                print(f"❌ '{word}' 등록 실패: {e}")
                failed.append(word)
                session.rollback()
                
    # 4. skipped 정리
    skipped = [w for w in skipped if isinstance(w, str) and w.strip()]

    # 3. 안내 메시지 설정
    if registered and not failed:
        message = f"✅ {len(registered)}개 등록 완료, {len(skipped)}개는 이미 등록됨"
    elif registered and failed:
        message = f"⚠️ {len(registered)}개 등록, {len(skipped)}개는 이미 등록, {len(failed)}개 실패"
    elif not registered and skipped:
        message = f"ℹ️ 모두 이미 등록된 단어입니다 ({len(skipped)}개)"
    else:
        message = "❌ 등록에 실패했습니다."

    return {
        "registered": registered,
        "skipped": skipped,
        "failed": failed,
        "message": message
    }


def load_automaton_from_db() -> ahocorasick.Automaton | None:
    """DB에서 금칙어 로딩하여 트라이 생성 (ORM 방식)"""
    automaton = ahocorasick.Automaton()
    inserted_words = set()
    unique_original_words = set()

    try:
        with db_session() as session:
            # ✅ 세션 내에서 필요한 데이터만 추출해서 복사해둠
            rows = session.query(ForbiddenWord.word, ForbiddenWord.decomposed_word).all()

        if not rows:
            print("⚠️ [주의] 금칙어가 DB에 등록되어 있지 않습니다.")
            return None

        for word, decomposed in rows:
            if word and word not in inserted_words:
                automaton.add_word(word, (word, "original"))
                inserted_words.add(word)
                unique_original_words.add(word)

            if decomposed and word not in exclude_for_jamo:
                jamo = decomposed.replace(" ", "")
                if len(jamo) >= 3 and jamo not in inserted_words:
                    automaton.add_word(jamo, (word, "decomposed"))
                    inserted_words.add(jamo)

        automaton.make_automaton()
        state.forbidden_automaton = automaton

        print(f"✅ 원형 {len(unique_original_words)}개, 자모 {len(inserted_words - unique_original_words)}개 등록 완료")

        return automaton

    except Exception as e:
        print(f"[❌ ERROR] 금칙어 불러오기 실패: {e}")
        return None


def add_to_automaton(word: str, decomposed: str):
    """금칙어 단일 등록 시 트라이에 반영"""
    if not state.forbidden_automaton:
        state.forbidden_automaton = ahocorasick.Automaton()
    
    if not state.forbidden_automaton.kind:
        state.forbidden_automaton.make_automaton()

    # 원형 단어 등록
    if word not in state.forbidden_automaton:
        state.forbidden_automaton.add_word(word, (word, "original"))
        print(f"✅ [추가] '{word}' → 원형 금칙어 등록 완료")
    else:
        print(f"⚠️ [중복] '{word}' → 이미 원형 등록됨")

    # 자모 단어 등록
    jamo = decomposed.replace(" ", "")
    if word not in exclude_for_jamo and len(jamo) >= 3:
        if jamo == word:
            print(f"⚠️ [생략] '{jamo}' → 원형과 자모가 같음 (등록 생략)")
        elif jamo not in state.forbidden_automaton:
            state.forbidden_automaton.add_word(jamo, (word, "decomposed"))
            print(f"✅ [추가] '{jamo}' → 자모 금칙어 등록 완료")
        else:
            print(f"⚠️ [중복] '{jamo}' → 이미 자모 등록됨")

    # 꼭 다시 빌드해야 함 (ahocorasick는 build 이후에만 탐색 가능)
    state.forbidden_automaton.make_automaton()

ALLOWED_POS_PREFIXES = ('N', 'V', 'M', 'VA', 'XR', 'IC')  # 명사, 동사, 부사, 형용사, 어근, 감탄사

def extract_meaningful_tokens(message: str) -> list[str]:
    tokens = mecab.pos(message)
    return [token for token, pos in tokens if not pos.startswith('J') and any(pos.startswith(prefix) for prefix in ALLOWED_POS_PREFIXES)]

def generate_ngrams(tokens: list[str], n_range=(2, 3)) -> set[str]:
    ngram_set = set()
    for n in range(n_range[0], n_range[1]+1):
        for i in range(len(tokens) - n + 1):
            ngram = ''.join(tokens[i:i+n])
            ngram_set.add(ngram)
    return ngram_set

def check_forbidden_message(message: str) -> dict:
    """메시지 한 개에 대해 금칙어 포함 여부 검사 (형태소 기반 단어만 검사)"""
    start_time = time.time()
    automaton = state.forbidden_automaton
    # decomposed = decompose_text(message)

    tokens = extract_meaningful_tokens(message)
    token_set = set(tokens)
    meaningful_tokens = token_set
    # meaningful_tokens = token_set | ngram_set  # 단어 + ngram 병합
    # print(f"✅ 형태소 분석 결과: {meaningful_tokens}")

    # 1차: 원형 검사
    for _, (word, mode) in automaton.iter(message):
        if mode == "original" and word in meaningful_tokens:
            elapsed = time.time() - start_time
            return {
                "message": message,
                "result": "🚫 금칙어 포함",
                "detected_words": [word],
                "method": "원형",
                "inference_time": round(elapsed, 4)
            }

    # 2차: 자모 검사
    # for _, (word, mode) in automaton.iter(decomposed):
    for _, (word, mode) in automaton.iter(message):
        if mode == "decomposed" and word in meaningful_tokens:
            elapsed = time.time() - start_time
            return {
                "message": message,
                "result": "🚫 금칙어 포함",
                "detected_words": [word],
                "method": "자모",
                "inference_time": round(elapsed, 4)
            }

    # 통과
    elapsed = time.time() - start_time
    return {
        "message": message,
        "result": "✅ 통과",
        "detected_words": [],
        "method": "-",
        "inference_time": round(elapsed, 4)
    }


def get_all_forbidden_words() -> list[dict]:
    """
    금칙어 전체 조회 (ORM)
    """
    with db_session() as session:
        words = session.query(ForbiddenWord).all()
        return [
            {
                "word": word.word,
                "decomposed_word": word.decomposed_word,
                "created_at": word.created_at
            }
            for word in words
        ]
        
def is_forbidden_word(word: str) -> bool:
    """
    특정 단어가 금칙어 테이블에 존재하는지 여부 반환 (ORM)
    """
    with db_session() as session:
        exists = session.query(ForbiddenWord).filter(ForbiddenWord.word == word).first()
        return exists is not None
    
    
def delete_forbidden_word(word: str) -> bool:
    """
    특정 금칙어를 DB에서 삭제 (ORM)
    """
    try:
        with db_session() as session:
            target = session.query(ForbiddenWord).filter(ForbiddenWord.word == word).first()
            if target:
                session.delete(target)
                session.commit()
                return True
            return False
    except Exception as e:
        print("❌ 삭제 에러:", e)
        return False


def delete_forbidden_words_by_date(date_str: str) -> int:
    """
    특정 날짜에 등록된 금칙어들을 DB에서 삭제
    :param date_str: YYYY-MM-DD 형식의 문자열
    :return: 삭제된 금칙어 개수
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        next_date = date + timedelta(days=1)

        with db_session() as session:
            targets = session.query(ForbiddenWord).filter(
                ForbiddenWord.created_at >= date,
                ForbiddenWord.created_at < next_date
            ).all()

            deleted_count = len(targets)

            for word in targets:
                session.delete(word)
            session.commit()

            return deleted_count
    except Exception as e:
        print("❌ 날짜 삭제 에러:", e)
        return -1  # 에러 시 -1 반환