-- 📁 DB 생성
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'safe_msg_pj_db')
BEGIN
    CREATE DATABASE safe_msg_pj_db;
END
GO

-- 📌 DB 사용 설정
USE safe_msg_pj_db;
GO

-- 🧠 민감 단어 테이블
CREATE TABLE sensitive_words (
    word_id INT IDENTITY(1,1) PRIMARY KEY,
    word NVARCHAR(255) NOT NULL,
    embedding VARBINARY(MAX) NOT NULL,
    model_name NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- 👥 사용자별 민감 단어 매핑 테이블
CREATE TABLE user_sensitive_words (
    user_id NVARCHAR(100) NOT NULL,
    word_id INT NOT NULL,
    PRIMARY KEY (user_id, word_id),
    FOREIGN KEY (word_id) REFERENCES sensitive_words(word_id) ON DELETE CASCADE
);
GO

-- ⛔ 금칙어 테이블
CREATE TABLE forbidden_words (
    id INT IDENTITY(1,1) PRIMARY KEY,
    word NVARCHAR(255) NOT NULL,
    decomposed_word NVARCHAR(255) NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO