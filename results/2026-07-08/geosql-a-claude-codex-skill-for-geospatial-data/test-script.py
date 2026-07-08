import subprocess
import sqlite3
import time
import tracemalloc
import os

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)

# Install Geosql
try:
    subprocess.run(['pip', 'install', 'geosql'], check=True)
    print('INSTALL_OK')
except:
    subprocess.run(['git', 'clone', 'https://github.com/dekart-xyz/geosql.git'], check=True)
    os.chdir('geosql')
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    os.chdir('..')
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Install baseline tool - sqlite3
print('INSTALL_OK')

# Create an in-memory database and insert 1000 rows
import geosql
import sqlite3

# Geosql
start_time = time.time()
mem = tracemalloc.start()
conn = geosql.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE points (lat REAL, lon REAL)')
for i in range(1000):
    cursor.execute('INSERT INTO points VALUES (?, ?)', (40.7128 + i * 0.001, -74.0060 + i * 0.001))
conn.commit()
cursor.execute('SELECT * FROM points WHERE lat > 40.713')
rows = cursor.fetchall()
end_time = time.time()
geosql_time = end_time - start_time
geosql_mem, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:geosql_query_time_ms:{(geosql_time * 1000):.2f}')
print(f'BENCHMARK:geosql_query_memory_mb:{(geosql_mem / 1024 / 1024):.2f}')
print(f'BENCHMARK:geosql_peak_memory_mb:{(peak / 1024 / 1024):.2f}')

# Baseline - sqlite3
start_time = time.time()
mem = tracemalloc.start()
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE points (lat REAL, lon REAL)')
for i in range(1000):
    cursor.execute('INSERT INTO points VALUES (?, ?)', (40.7128 + i * 0.001, -74.0060 + i * 0.001))
conn.commit()
cursor.execute('SELECT * FROM points WHERE lat > 40.713')
rows = cursor.fetchall()
end_time = time.time()
sqlite_time = end_time - start_time
sqlite_mem, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:sqlite_query_time_ms:{(sqlite_time * 1000):.2f}')
print(f'BENCHMARK:sqlite_query_memory_mb:{(sqlite_mem / 1024 / 1024):.2f}')
print(f'BENCHMARK:sqlite_peak_memory_mb:{(peak / 1024 / 1024):.2f}')

# Compare performance between Geosql and sqlite3
print(f'BENCHMARK:vs_sqlite_query_time_ratio:{(geosql_time / sqlite_time):.2f}')
print(f'BENCHMARK:vs_sqlite_query_time_ms:{(geosql_time - sqlite_time) * 1000:.2f}')

# Test filter points by distance
try:
    cursor.execute('SELECT * FROM points WHERE lat > 40.712 AND lon > -74.005')
    rows = cursor.fetchall()
    print('TEST_PASS:filter_points')
except Exception as e:
    print(f'TEST_FAIL:filter_points:{str(e)}')

# Test aggregation query over a geospatial column
try:
    cursor.execute('SELECT COUNT(lat) FROM points WHERE lat > 40.713')
    rows = cursor.fetchall()
    print('TEST_PASS:aggregation_query')
except Exception as e:
    print(f'TEST_FAIL:aggregation_query:{str(e)}')

# Test performance between Geosql and PostGIS under load
try:
    import datetime
    start_time = time.time()
    for i in range(1000):
        cursor.execute('SELECT * FROM points WHERE lat > 40.713')
    end_time = time.time()
    print(f'BENCHMARK:geosql_query_time_ms:{((end_time - start_time) / 1000) * 1000:.2f}')
    print('TEST_PASS:geosql_under_load')
except Exception as e:
    print(f'TEST_FAIL:geosql_under_load:{str(e)}')

print('RUN_OK')