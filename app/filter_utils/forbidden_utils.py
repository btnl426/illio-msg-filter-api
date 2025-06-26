# app/filter_utils/forbidden_utils.py

import hgtk
import ahocorasick
from app.database import get_connection
import app.state as state

exclude_for_jamo = set()

def decompose_text(text: str) -> str:
    return hgtk.text.decompose(text).replace('ᴥ', '')

def prepare_forbidden_entry(word: str) -> dict:
    decomposed = decompose_text(word)
    return {"word": word, "decomposed_word": decomposed}

def prepare_forbidden_entries(words: list[str]) -> list[dict]:
    return [{"word": word, "decomposed_word": decompose_text(word)} for word in words]

def load_automaton_from_db() -> ahocorasick.Automaton | None:
    """DB에서 금칙어 로딩하여 트라이 생성"""
    automaton = ahocorasick.Automaton()
    inserted_words = set()
    unique_original_words = set()   # 실제 등록된 원형 단어만 따로 저장

    conn = None

    try:
        conn = get_connection()
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

        # print(f"✅ 총 {len(unique_original_words)}개의 금칙어가 등록되었습니다.")
        print(f"✅ 원형 {len(unique_original_words)}개, 자모 {len(inserted_words - unique_original_words)}개 등록 완료")
        return automaton

    except Exception as e:
        print(f"[❌ ERROR] 금칙어 불러오기 실패: {e}")
        return None

    finally:
        if conn:
            conn.close()


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
