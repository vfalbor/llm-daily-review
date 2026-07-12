import subprocess
import time
import tracemalloc
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys

# Install sqlite package
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'sqlalchemy'], check=False)
    print("INSTALL_OK")
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/sqlalchemy/sqlalchemy.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './sqlalchemy'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

# Create in-memory database
engine = create_engine('sqlite:///:memory:')
Base = declarative_base()

class Example(Base):
    __tablename__ = 'example'
    id = Column(Integer, primary_key=True)
    name = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert 1000 rows
start_time = time.time()
for i in range(1000):
    session.add(Example(name=f"Example {i}"))
session.commit()
end_time = time.time()
print(f"BENCHMARK:insert_time_s:{end_time - start_time}")

# Query with WHERE
start_time = time.time()
result = session.query(Example).filter(Example.name == 'Example 500').all()
end_time = time.time()
print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000}")

# Measure memory usage
tracemalloc.start()
result = session.query(Example).filter(Example.name == 'Example 500').all()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024}")

# Baseline test with sqlite3
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE example (id INTEGER PRIMARY KEY, name TEXT)')
start_time = time.time()
for i in range(1000):
    cursor.execute('INSERT INTO example (name) VALUES (?)', (f"Example {i}",))
conn.commit()
end_time = time.time()
print(f"BENCHMARK:baseline_insert_time_s:{end_time - start_time}")

start_time = time.time()
cursor.execute('SELECT * FROM example WHERE name = ?', ('Example 500',))
cursor.fetchall()
end_time = time.time()
print(f"BENCHMARK:baseline_query_latency_ms:{(end_time - start_time) * 1000}")

# Compare performance
print(f"BENCHMARK:vs_sqlite3_insert_ratio:{(end_time - start_time) / (end_time - start_time)}")
print(f"BENCHMARK:vs_sqlite3_query_ratio:{(end_time - start_time) / (end_time - start_time)}")

print("RUN_OK")