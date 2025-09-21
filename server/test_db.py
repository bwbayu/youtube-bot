from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://root:12345678@localhost:5433/botjudol"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).fetchone()
        print("Connected! PostgreSQL version:", version[0])
except Exception as e:
    print("Connection failed:", e)
