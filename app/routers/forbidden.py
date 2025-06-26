from fastapi import APIRouter
from app.database import get_connection
from app.filter_utils.forbidden_utils import (
    prepare_forbidden_entry, 
    prepare_forbidden_entries,
    add_to_automaton
)
from app.schemas.forbidden_schema import ForbiddenWord, ForbiddenWordList

router = APIRouter()

@router.post("")
def register_forbidden(data: ForbiddenWord):
    try:
        conn = get_connection()
        existing_words = get_existing_words(conn, [data.word])
        if data.word in existing_words:
            return {
                "message": "이미 등록된 금칙어입니다.",
                "word": data.word
            }

        entry = prepare_forbidden_entry(data.word)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO forbidden_words (word, decomposed_word)
            VALUES (?, ?)
        """, (entry["word"], entry["decomposed_word"]))
        conn.commit()
        
        # 실시간 트라이 등록
        add_to_automaton(entry["word"], entry["decomposed_word"])

        return {"message": "금칙어가 등록되었습니다.", "data": entry}

    except Exception as e:
        return {"error": "DB 오류 발생", "detail": str(e)}

    finally:
        conn.close()


@router.post("/bulk")
def register_forbidden_bulk(data: ForbiddenWordList):
    try:
        conn = get_connection()
        existing_words = get_existing_words(conn, data.words)
        filtered_words = [word for word in data.words if word not in existing_words]
        entries = prepare_forbidden_entries(filtered_words)

        cursor = conn.cursor()
        registered = []
        failed = []

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

        conn.commit()

        return {
            "message": f"{len(registered)}개의 금칙어가 등록되었습니다.",
            "registered": registered,
            "skipped": list(existing_words),
            "failed": failed
        }

    except Exception as e:
        return {"error": "DB 오류 발생", "detail": str(e)}

    finally:
        if conn:
            conn.close()
        
@router.get("")
def get_all_forbidden_words():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT word, decomposed_word, created_at FROM forbidden_words")
        rows = cursor.fetchall()
        result = [
            {
                "word": row[0],
                "decomposed_word": row[1],
                "created_at": row[2]
            }
            for row in rows
        ]
        return {"count": len(result), "data": result}
    except Exception as e:
        return {"error": "DB 조회 중 오류 발생", "detail": str(e)}
    finally:
        conn.close()
        
@router.get("/check/{word}")
def check_forbidden_word(word: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM forbidden_words WHERE word = ?", (word,))
        count = cursor.fetchone()[0]
        return {
            "word": word,
            "is_forbidden": count > 0
        }
    except Exception as e:
        return {"error": "DB 조회 중 오류 발생", "detail": str(e)}
    finally:
        conn.close()


def get_existing_words(conn, words: list[str]) -> set[str]:
    if not words:
        return set()
    placeholders = ','.join('?' for _ in words)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT word FROM forbidden_words
        WHERE word IN ({placeholders})
    """, words)
    return set(row[0] for row in cursor.fetchall())