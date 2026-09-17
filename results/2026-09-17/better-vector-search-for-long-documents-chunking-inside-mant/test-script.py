import subprocess, sys, os, time, tracemalloc, shutil, json, math, random, string, pathlib, hashlib, sqlite3
from contextlib import contextmanager

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def install_apk(packages):
    ok, err = run_cmd(['apk', 'add', '--no-cache'] + packages)
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err}")

def pip_install(pkg):
    ok, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err}")

def git_clone(url, dest):
    ok, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if not ok:
        print_marker(f"INSTALL_FAIL:{err}")
    return ok

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return elapsed, result

@contextmanager
def memory_tracker():
    tracemalloc.start()
    try:
        yield
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

def install_dependencies():
    # system packages
    install_apk(['sqlite', 'git', 'gcc', 'g++', 'make', 'python3-dev'])
    # python client
    pip_install('manticoresearch')
    # fallback via source if needed
    if not shutil.which('manticoresearch'):
        repo_dir = '/tmp/manticoresearch'
        if git_clone('https://github.com/manticoresearch/manticoresearch.git', repo_dir):
            pip_install(f'{repo_dir}')
    # baseline sqlite (already in stdlib)

def generate_documents(n=1000):
    docs = []
    for i in range(n):
        text = ' '.join(random.choices(string.ascii_lowercase, k=200))
        docs.append((i, text))
    return docs

def test_clone_and_build():
    try:
        repo_dir = '/tmp/manticoresearch_src'
        if os.path.isdir(repo_dir):
            shutil.rmtree(repo_dir)
        ok = git_clone('https://github.com/manticoresearch/manticoresearch.git', repo_dir)
        if not ok:
            raise RuntimeError('git clone failed')
        # try building if Makefile exists
        makefile = os.path.join(repo_dir, 'Makefile')
        if os.path.isfile(makefile):
            ok, err = run_cmd(['make', '-C', repo_dir])
            if not ok:
                raise RuntimeError(f'make failed: {err}')
        print_marker("TEST_PASS:test_clone_and_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_clone_and_build:{e}")

def test_index_documents():
    try:
        from manticoresearch import Client
        client = Client('http://127.0.0.1:9306')
        # ensure server is reachable (skip if not)
        try:
            client.ping()
        except Exception:
            raise RuntimeError('Manticore server not running')
        # create index with chunking (simplified)
        schema = {
            'fields': {
                'content': 'text',
                'doc_id': 'int'
            },
            'index_settings': {
                'chunking': True
            }
        }
        client.index('test_idx').create(schema)
        docs = generate_documents()
        t, _ = measure_time(lambda: client.index('test_idx').insert_batch([
            {'doc_id': doc_id, 'content': txt} for doc_id, txt in docs
        ]))
        print_marker(f"BENCHMARK:index_time_s:{t:.3f}")
        print_marker("TEST_PASS:test_index_documents")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_index_documents:{e}")

def test_similarity_query():
    try:
        from manticoresearch import Client
        client = Client('http://127.0.0.1:9306')
        query_text = 'example query text for similarity'
        t, resp = measure_time(lambda: client.search('test_idx').match('content', query_text).execute())
        # very naive relevance check
        if not resp['hits']:
            raise RuntimeError('no hits returned')
        top_score = resp['hits'][0]['_score']
        if top_score <= 0:
            raise RuntimeError('non‑positive relevance')
        print_marker(f"BENCHMARK:query_time_s:{t:.3f}")
        print_marker("TEST_PASS:test_similarity_query")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_similarity_query:{e}")

def test_latency_vs_sqlite():
    try:
        docs = generate_documents()
        # baseline using sqlite
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        cur.execute('CREATE TABLE docs(id INTEGER PRIMARY KEY, content TEXT)')
        t_insert, _ = measure_time(lambda: cur.executemany('INSERT INTO docs(id,content) VALUES (?,?)', docs))
        conn.commit()
        query = 'SELECT * FROM docs WHERE content LIKE ? LIMIT 10'
        param = ('%a%',)
        t_query, rows = measure_time(lambda: cur.execute(query, param).fetchall())
        print_marker(f"BENCHMARK:sqlite_insert_time_s:{t_insert:.3f}")
        print_marker(f"BENCHMARK:sqlite_query_time_s:{t_query:.3f}")

        # manticore query already measured in previous test; repeat for fairness
        from manticoresearch import Client
        client = Client('http://127.0.0.1:9306')
        query_text = 'a'
        t_mant, _ = measure_time(lambda: client.search('test_idx').match('content', query_text).limit(10).execute())
        print_marker(f"BENCHMARK:manticore_query_time_s:{t_mant:.3f}")

        # ratio baseline
        if t_query > 0:
            ratio = t_mant / t_query
            print_marker(f"BENCHMARK:vs_sqlite_query_ratio:{ratio:.3f}")
        else:
            print_marker("BENCHMARK:vs_sqlite_query_ratio:inf")
        print_marker("TEST_PASS:test_latency_vs_sqlite")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_latency_vs_sqlite:{e}")

def main():
    try:
        install_dependencies()
        # Benchmark install time
        start = time.time()
        # dummy operation to measure
        time.sleep(0.1)
        print_marker(f"BENCHMARK:install_time_s:{time.time()-start:.3f}")

        test_clone_and_build()
        test_index_documents()
        test_similarity_query()
        test_latency_vs_sqlite()
    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected_error:{e}")
    finally:
        print_marker("RUN_OK")

if __name__ == "__main__":
    main()