필요 테이블 생성문

CREATE TABLE user_sensitive_words (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    word_id INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE()

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_word FOREIGN KEY (word_id) REFERENCES sensitive_words(word_id),
    CONSTRAINT uq_user_word UNIQUE (user_id, word_id)  -- 사용자별 중복 방지
);

CREATE TABLE sensitive_words (
    word_id INT IDENTITY(1,1) PRIMARY KEY,
    word NVARCHAR(100) NOT NULL UNIQUE,
    embedding VARBINARY(MAX),
    model_name NVARCHAR(100),
    category NVARCHAR(50),
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE forbidden_decomposed_word (
    id INT PRIMARY KEY IDENTITY(1,1),
    origin_id INT NOT NULL,
    decomposed_word NVARCHAR(300) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (origin_id) REFERENCES forbidden_origin_word(id) ON DELETE CASCADE
);
