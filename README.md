![image](https://github.com/user-attachments/assets/d341576e-e0a5-4b96-bf59-750b181c4a52)


🗂️ 테이블 생성 스크립트 (MSSQL)

-- 민감 단어 테이블

CREATE TABLE sensitive_words (
    word_id INT IDENTITY(1,1) PRIMARY KEY,
    word NVARCHAR(255) NOT NULL,
    embedding VARBINARY(MAX) NOT NULL,
    model_name NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);

-- 사용자별 민감 단어 연결 테이블

CREATE TABLE user_sensitive_words (
    user_id NVARCHAR(100) NOT NULL,
    word_id INT NOT NULL,
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (word_id) REFERENCES sensitive_words(word_id) ON DELETE CASCADE
);

-- 금칙어 테이블

CREATE TABLE forbidden_words (
    id INT IDENTITY(1,1) PRIMARY KEY,
    word NVARCHAR(255) NOT NULL,
    decomposed_word NVARCHAR(255) NULL,
    created_at DATETIME DEFAULT GETDATE()
);


⸻

💬 참고사항
	•	embedding은 float32 numpy array를 .tobytes()로 변환하여 저장하는 구조입니다.
	•	user_sensitive_words는 민감 단어 사용 유저를 매핑하며, 단어와 연결이 끊어진 경우 sensitive_words도 삭제 처리 가능하게 ON DELETE CASCADE 옵션을 포함했습니다.
	•	forbidden_words의 decomposed_word는 자모 분리 처리를 위한 컬럼입니다.
