import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=mssql;"
    "DATABASE=safe_msg_pj_db;"
    "UID=sa;"
    "PWD=Illio1234!"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ DB 연결 성공!")
    conn.close()
except Exception as e:
    print("❌ DB 연결 실패:", e)