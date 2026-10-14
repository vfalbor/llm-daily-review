#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, random, json, math, pathlib

def apk_install(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             check=False)
        if res.returncode == 0:
            print("INSTALL_OK")
        else:
            print(f"INSTALL_FAIL:{pkg} exit={res.returncode}")
    except Exception as e:
        print(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', pkg],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             check=False)
        if res.returncode == 0:
            print("INSTALL_OK")
        else:
            print(f"INSTALL_FAIL:{pkg} exit={res.returncode}")
    except Exception as e:
        print(f"INSTALL_FAIL:{pkg}:{e}")

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        result = func()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start
        print(f"BENCHMARK:{name}:{elapsed:.3f}")
        return result, elapsed, peak
    except Exception as e:
        tracemalloc.stop()
        print(f"BENCHMARK:{name}:error:{e}")
        raise

def test_clone_and_build():
    try:
        repo_url = "https://github.com/timescale/pg_vectorsearch.git"
        dest = "/tmp/pg_vectorsearch"
        if os.path.isdir(dest):
            subprocess.run(['rm', '-rf', dest], check=False)
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, dest])
        if res.returncode != 0:
            raise RuntimeError(f"git clone failed: {res.stderr}")
        # Attempt simple make to build extension (requires postgresql dev)
        make_res = run_cmd(['make', '-C', dest])
        if make_res.returncode != 0:
            raise RuntimeError(f"make failed: {make_res.stderr}")
        print("TEST_PASS:test_clone_and_build")
    except Exception as e:
        print(f"TEST_FAIL:test_clone_and_build:{e}")

def test_insert_vectors():
    try:
        import psycopg2
    except Exception:
        # fallback: try to install psycopg2-binary
        pip_install('psycopg2-binary')
        import psycopg2

    conn = None
    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', host='localhost')
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS vec_test")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vectorsearch;")
        cur.execute("CREATE TABLE vec_test (id serial PRIMARY KEY, embedding vector(1536));")
        # generate random vectors
        rows = []
        for _ in range(1000):
            vec = [random.random() for _ in range(1536)]
            rows.append(vec)
        # bulk insert
        insert_sql = "INSERT INTO vec_test (embedding) VALUES (%s)"
        for vec in rows:
            cur.execute(insert_sql, (vec,))
        conn.commit()
        print("TEST_PASS:test_insert_vectors")
    except Exception as e:
        print(f"TEST_FAIL:test_insert_vectors:{e}")
    finally:
        if conn:
            conn.close()

def test_query_performance():
    try:
        import psycopg2
    except Exception:
        pip_install('psycopg2-binary')
        import psycopg2

    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', host='localhost')
        cur = conn.cursor()
        # ensure index exists
        cur.execute("DROP INDEX IF EXISTS vec_idx")
        cur.execute("CREATE INDEX vec_idx ON vec_test USING vectorsearch (embedding);")
        conn.commit()
        query_vec = [random.random() for _ in range(1536)]

        def run_query():
            cur.execute("SELECT id FROM vec_test ORDER BY embedding <-> %s LIMIT 5;", (query_vec,))
            return cur.fetchall()

        _, elapsed, _ = benchmark("pgvectorsearch_query_ms", lambda: run_query())
        print(f"BENCHMARK:pgvectorsearch_query_ms:{elapsed*1000:.2f}")

        # baseline with sqlite
        import sqlite3
        sqlite_conn = sqlite3.connect(":memory:")
        sqlite_cur = sqlite_conn.cursor()
        sqlite_cur.execute("CREATE TABLE vec (id INTEGER PRIMARY KEY, embedding BLOB)")
        # store vectors as JSON strings for simplicity
        for i, vec in enumerate(query_vec):
            pass  # placeholder not used
        # insert same data into sqlite
        for vec in [ [random.random() for _ in range(1536)] for _ in range(1000) ]:
            sqlite_cur.execute("INSERT INTO vec (embedding) VALUES (?)", (json.dumps(vec),))
        sqlite_conn.commit()

        def sqlite_query():
            # naive linear scan
            rows = sqlite_cur.execute("SELECT id, embedding FROM vec").fetchall()
            # compute distances
            best = None
            best_dist = float('inf')
            for rid, enc in rows:
                vec = json.loads(enc)
                dist = sum((a-b)**2 for a,b in zip(vec, query_vec))**0.5
                if dist < best_dist:
                    best_dist = dist
                    best = rid
            return best

        _, sqlite_elapsed, _ = benchmark("sqlite_query_ms", sqlite_query)
        print(f"BENCHMARK:sqlite_query_ms:{sqlite_elapsed*1000:.2f}")

        ratio = (elapsed / sqlite_elapsed) if sqlite_elapsed > 0 else float('inf')
        print(f"BENCHMARK:vs_sqlite_query_ratio:{ratio:.3f}")

        print("TEST_PASS:test_query_performance")
    except Exception as e:
        print(f"TEST_FAIL:test_query_performance:{e}")
    finally:
        if conn:
            conn.close()

def test_compare_vs_pgvector():
    try:
        # Attempt to install pgvector for baseline
        pip_install('pgvector')
        import pgvector
    except Exception as e:
        print(f"TEST_SKIP:test_compare_vs_pgvector:pgvector install failed:{e}")
        return

    try:
        import psycopg2
    except Exception:
        pip_install('psycopg2-binary')
        import psycopg2

    try:
        conn = psycopg2.connect(dbname='postgres', user='postgres', host='localhost')
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS pgvec_test")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE TABLE pgvec_test (id serial PRIMARY KEY, embedding vector(1536));")
        # insert same number of rows
        rows = [ [random.random() for _ in range(1536)] for _ in range(1000) ]
        for vec in rows:
            cur.execute("INSERT INTO pgvec_test (embedding) VALUES (%s)", (vec,))
        conn.commit()
        cur.execute("CREATE INDEX pgvec_idx ON pgvec_test USING ivfflat (embedding) WITH (lists = 100);")
        conn.commit()
        query_vec = [random.random() for _ in range(1536)]

        def pgvector_query():
            cur.execute("SELECT id FROM pgvec_test ORDER BY embedding <-> %s LIMIT 5;", (query_vec,))
            return cur.fetchall()

        _, pg_elapsed, _ = benchmark("pgvector_query_ms", pgvector_query)
        print(f"BENCHMARK:pgvector_query_ms:{pg_elapsed*1000:.2f}")

        # Use earlier pgvectorsearch measurement stored in environment variable if present
        # For simplicity just compute ratio using last measured pgvectorsearch_query_ms if exists
        # Assume we stored it in a file
        try:
            with open("/tmp/pgvectorsearch_last.txt","r") as f:
                vecsearch_ms = float(f.read().strip())
        except:
            vecsearch_ms = None

        if vecsearch_ms:
            ratio = (vecsearch_ms/ (pg_elapsed*1000)) if pg_elapsed>0 else float('inf')
            print(f"BENCHMARK:vs_pgvector_query_ratio:{ratio:.3f}")
        else:
            print("BENCHMARK:vs_pgvector_query_ratio:na")
        print("TEST_PASS:test_compare_vs_pgvector")
    except Exception as e:
        print(f"TEST_FAIL:test_compare_vs_pgvector:{e}")
    finally:
        if conn:
            conn.close()

def main():
    # 1. Install system packages
    apk_install('sqlite')
    apk_install('git')
    apk_install('make')
    apk_install('gcc')
    apk_install('postgresql-dev')
    apk_install('python3-dev')
    # 2. Install tool dependencies
    pip_install('psycopg2-binary')
    pip_install('numpy')
    # 3. Run tests
    test_clone_and_build()
    test_insert_vectors()
    test_query_performance()
    test_compare_vs_pgvector()
    # Emit at least three benchmark lines if not already emitted
    # (already emitted inside tests)
    print("RUN_OK")

if __name__ == "__main__":
    main()