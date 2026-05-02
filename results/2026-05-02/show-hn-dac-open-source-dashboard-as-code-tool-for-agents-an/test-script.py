import subprocess
import time
import tracemalloc
import numpy as np
import pandas as pd
from dac import Dashboard

def install_dac():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'dac'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/bruin-data/dac.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './dac'], check=False, cwd='./dac')
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_import_time():
    try:
        tracemalloc.start()
        start_time = time.time()
        from dac import Dashboard
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:import_memory_mb:{peak / 10**6:.2f}')
        print(f'TEST_PASS:import_time')
    except Exception as e:
        print(f'TEST_FAIL:import_time:{str(e)}')

def test_create_dashboard():
    try:
        db = Dashboard()
        db.create_dashboard('test_dashboard')
        print(f'TEST_PASS:create_dashboard')
    except Exception as e:
        print(f'TEST_FAIL:create_dashboard:{str(e)}')

def test_insert_rows():
    try:
        db = Dashboard()
        data = np.random.rand(100, 2)
        df = pd.DataFrame(data, columns=['column1', 'column2'])
        start_time = time.time()
        db.insert_rows(df, 'test_dashboard')
        end_time = time.time()
        print(f'BENCHMARK:insert_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'TEST_PASS:insert_rows')
    except Exception as e:
        print(f'TEST_FAIL:insert_rows:{str(e)}')

def test_render_latency():
    try:
        db = Dashboard()
        start_time = time.time()
        db.render('test_dashboard')
        end_time = time.time()
        print(f'BENCHMARK:render_latency_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'TEST_PASS:render_latency')
    except Exception as e:
        print(f'TEST_FAIL:render_latency:{str(e)}')

def test_query_latency():
    try:
        db = Dashboard()
        start_time = time.time()
        db.query('SELECT * FROM test_dashboard WHERE column1 > 0.5', 'test_dashboard')
        end_time = time.time()
        print(f'BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'TEST_PASS:query_latency')
    except Exception as e:
        print(f'TEST_FAIL:query_latency:{str(e)}')

def test_grafana_baseline():
    try:
        import grafana
        db = Dashboard()
        start_time = time.time()
        db.render('test_dashboard')
        end_time = time.time()
        dac_latency = (end_time - start_time) * 1000
        start_time = time.time()
        grafana.render('test_dashboard')
        end_time = time.time()
        grafana_latency = (end_time - start_time) * 1000
        ratio = dac_latency / grafana_latency
        print(f'BENCHMARK:vs_grafana_render_ratio:{ratio:.2f}')
        print(f'TEST_PASS:grafana_baseline')
    except Exception as e:
        print(f'TEST_FAIL:grafana_baseline:{str(e)}')

install_dac()
test_import_time()
test_create_dashboard()
test_insert_rows()
test_render_latency()
test_query_latency()
test_grafana_baseline()
print('RUN_OK')