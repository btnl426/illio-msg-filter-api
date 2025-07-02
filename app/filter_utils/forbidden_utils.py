# app/filter_utils/forbidden_utils.py

import hgtk
import time
import ahocorasick
from app.database import db_session
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
    """금칙어 테이블에서 이미 등록된 단어 조회"""
    if not words:
        return set()

    with db_session() as conn:
        cursor = conn.cursor()
        placeholders = ','.join('?' for _ in words)
        cursor.execute(f"""
            SELECT word FROM forbidden_words
            WHERE word IN ({placeholders})
        """, words)
        return set(row[0] for row in cursor.fetchall())


def register_forbidden_word(word: str) -> dict:
    """금칙어 등록 함수 (단일)"""
    existing_words = get_existing_words([word])
    if word in existing_words:
        return {"created": False, "word": word}

    entry = prepare_forbidden_entry(word)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO forbidden_words (word, decomposed_word)
            VALUES (?, ?)
        """, (entry["word"], entry["decomposed_word"]))

        # 커밋은 db_session 내부에서 자동 수행
        add_to_automaton(entry["word"], entry["decomposed_word"])

        return {
            "created": True,
            "word": word,
            "decomposed_word": entry["decomposed_word"]
        }
        

def insert_bulk_forbidden_words(words: list[str]) -> dict:
    """
    여러 금칙어를 DB에 일괄 등록하고 트라이에 반영
    """
    existing_words = get_existing_words(words)
    filtered_words = [word for word in words if word not in existing_words]
    entries = prepare_forbidden_entries(filtered_words)

    registered = []
    failed = []

    with db_session() as conn:
        cursor = conn.cursor()
        for entry in entries:
            try:
                cursor.execute("""
                    INSERT INTO forbidden_words (word, decomposed_word)
                    VALUES (?, ?)
                """, (entry["word"], entry["decomposed_word"]))
                add_to_automaton(entry["word"], entry["decomposed_word"])
                registered.append(entry["word"])
            except Exception as e:
                print(f"❌ '{entry['word']}' 등록 실패: {e}")
                failed.append(entry["word"])
                continue

    return {
        "registered": registered,
        "skipped": list(existing_words),
        "failed": failed
    }


def load_automaton_from_db() -> ahocorasick.Automaton | None:
    """DB에서 금칙어 로딩하여 트라이 생성"""
    automaton = ahocorasick.Automaton()
    inserted_words = set()
    unique_original_words = set()  # 실제 등록된 원형 단어만 따로 저장

    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word, decomposed_word FROM forbidden_words")
            rows = cursor.fetchall()

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
        state.forbidden_automaton = automaton  # ✅ 전역 상태에 직접 할당

        print(f"✅ 원형 {len(unique_original_words)}개, 자모 {len(inserted_words - unique_original_words)}개 등록 완료")
        return automaton

    except Exception as e:
        print(f"[❌ ERROR] 금칙어 불러오기 실패: {e}")
        return None


def add_to_automaton(word: str, decomposed: str):
    """금칙어 단일 등록 시 트라이에 반영"""
    if not state.forbidden_automaton:
        state.forbidden_automaton = ahocorasick.Automaton()

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
    return [token for token, pos in tokens if not pos.startswith('J') and pos.startswith(ALLOWED_POS_PREFIXES)]

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
    decomposed = decompose_text(message)

    tokens = extract_meaningful_tokens(message)
    token_set = set(tokens)
    ngram_set = generate_ngrams(tokens)
    meaningful_tokens = token_set | ngram_set  # 단어 + ngram 병합
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
    for _, (word, mode) in automaton.iter(decomposed):
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
    금칙어 전체 조회
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word, decomposed_word, created_at FROM forbidden_words")
        rows = cursor.fetchall()
        return [
            {
                "word": row[0],
                "decomposed_word": row[1],
                "created_at": row[2]
            }
            for row in rows
        ]
        
def is_forbidden_word(word: str) -> bool:
    """
    특정 단어가 금칙어 테이블에 존재하는지 여부 반환
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM forbidden_words WHERE word = ?", (word,))
        count = cursor.fetchone()[0]
        return count > 0
    
    
def delete_forbidden_word(word: str) -> bool:
    """
    특정 금칙어를 DB에서 삭제
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forbidden_words WHERE word = ?", (word,))
            return cursor.rowcount > 0  # 삭제된 행이 있으면 True
    except Exception as e:
        print("❌ 삭제 에러:", e)
        return False
        