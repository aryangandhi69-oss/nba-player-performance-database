import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

if len(sys.argv) < 2:
    print("Usage: python run_query.py sql/filename.sql")
    sys.exit(1)

sql_file_path = sys.argv[1]

with open(sql_file_path, "r") as f:
    query = f.read()

with engine.connect() as conn:
    result = conn.execute(text(query))
    for row in result:
        print(row)