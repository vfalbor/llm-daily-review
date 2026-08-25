import subprocess, sys, time, os, json, traceback, tracemalloc, shutil
from pathlib import Path

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(packages):
    try:
        res = run_cmd(['apk', 'add', '--no-cache'] + packages, check=False)
        if res and res.returncode == 0:
            print("INSTALL_OK")
        else:
            reason = (res.stderr.strip() if res else "unknown error")
            print(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def pip_install(pkg):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
        if res and res.returncode == 0:
            return True
        return False
    except Exception:
        return False

def npm_install():
    try:
        res = run_cmd(['npm', 'install'])
        return res and res.returncode == 0
    except Exception:
        return False

def print_test_pass(name):
    print(f"TEST_PASS:{name}")

def print_test_fail(name, reason):
    print(f"TEST_FAIL:{name}:{reason}")

def print_test_skip(name, reason):
    print(f"TEST_SKIP:{name}:{reason}")

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def main():
    start_total = time.time()
    # 1. Install system deps
    install_apk(['git', 'python3', 'python3-dev', 'py3-pip', 'nodejs', 'npm', 'bash', 'curl'])
    # 2. Clone repo
    repo_url = "https://github.com/murerkinn/bookshelf.git"
    workdir = Path("/tmp/bookshelf")
    try:
        if workdir.exists():
            shutil.rmtree(workdir)
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(workdir)])
        if res and res.returncode == 0:
            print_test_pass("clone_repo")
        else:
            raise RuntimeError(res.stderr if res else "git clone failed")
    except Exception as e:
        print_test_fail("clone_repo", str(e))
        print("RUN_OK")
        return

    os.chdir(workdir)

    # 3. Install python dependencies
    py_deps_installed = False
    try:
        # try pip install from requirements if exists
        req_file = workdir / "requirements.txt"
        if req_file.is_file():
            py_deps_installed = pip_install("-r")
            # pip install -r requirements.txt
            if not py_deps_installed:
                raise RuntimeError("pip install -r failed")
        else:
            # fallback to editable install
            py_deps_installed = pip_install("-e .")
            if not py_deps_installed:
                raise RuntimeError("pip install -e . failed")
        print_test_pass("python_deps")
    except Exception as e:
        print_test_fail("python_deps", str(e))

    # 4. Install node deps
    try:
        if (workdir / "package.json").is_file():
            if npm_install():
                print_test_pass("npm_deps")
            else:
                raise RuntimeError("npm install failed")
        else:
            print_test_skip("npm_deps", "no package.json")
    except Exception as e:
        print_test_fail("npm_deps", str(e))

    # 5. Start service (docker-compose)
    try:
        compose_file = workdir / "docker-compose.yml"
        if compose_file.is_file():
            up_start = time.time()
            res = run_cmd(['docker-compose', 'up', '-d'])
            up_end = time.time()
            if res and res.returncode == 0:
                benchmark("service_start_time_s", round(up_end - up_start, 2))
                print_test_pass("service_start")
                # wait a bit for health
                time.sleep(5)
            else:
                raise RuntimeError(res.stderr if res else "docker-compose up failed")
        else:
            # try python -m uvicorn if app is pure python
            raise RuntimeError("docker-compose.yml not found")
    except Exception as e:
        print_test_fail("service_start", str(e))

    # Helper to make HTTP calls
    def http_get(path):
        import requests
        url = f"http://127.0.0.1:8000{path}"
        return requests.get(url, timeout=10)

    # 6. Health check
    try:
        t0 = time.time()
        r = http_get("/health")
        t1 = time.time()
        benchmark("health_check_ms", int((t1 - t0) * 1000))
        if r.status_code == 200:
            print_test_pass("health_check")
        else:
            raise RuntimeError(f"status {r.status_code}")
    except Exception as e:
        print_test_fail("health_check", str(e))

    # 7. Upload test book (simulate object storage with local file)
    try:
        import requests
        book_path = workdir / "test_book.pdf"
        book_path.write_bytes(b"%PDF-1.4 test ebook content")
        files = {'file': ('test_book.pdf', open(book_path, 'rb'), 'application/pdf')}
        t0 = time.time()
        r = requests.post("http://127.0.0.1:8000/api/books", files=files)
        t1 = time.time()
        benchmark("upload_book_ms", int((t1 - t0) * 1000))
        if r.status_code in (200, 201):
            print_test_pass("upload_book")
            book_id = r.json().get('id')
        else:
            raise RuntimeError(f"upload failed {r.status_code}")
    except Exception as e:
        print_test_fail("upload_book", str(e))
        book_id = None

    # 8. Verify appears in list
    try:
        if book_id is None:
            raise RuntimeError("no book_id from upload")
        t0 = time.time()
        r = requests.get("http://127.0.0.1:8000/api/books")
        t1 = time.time()
        benchmark("list_books_ms", int((t1 - t0) * 1000))
        if r.status_code == 200 and any(str(book_id) == str(item.get('id')) for item in r.json()):
            print_test_pass("list_contains_uploaded")
        else:
            raise RuntimeError("uploaded book not in list")
    except Exception as e:
        print_test_fail("list_contains_uploaded", str(e))

    # 9. Search query
    try:
        query = "test_book"
        t0 = time.time()
        r = requests.get(f"http://127.0.0.1:8000/api/books/search?q={query}")
        t1 = time.time()
        benchmark("search_query_ms", int((t1 - t0) * 1000))
        if r.status_code == 200:
            results = r.json()
            if isinstance(results, list) and len(results) > 0:
                print_test_pass("search_query")
                benchmark("search_result_count", len(results))
            else:
                raise RuntimeError("no results")
        else:
            raise RuntimeError(f"status {r.status_code}")
    except Exception as e:
        print_test_fail("search_query", str(e))

    # 10. Benchmark vs baseline (Calibre Server mock ratio)
    try:
        # mock baseline of 120ms for listing
        baseline_ms = 120
        my_ms = float(next((line for line in sys.stdout.getvalue().splitlines() if line.startswith("BENCHMARK:list_books_ms")), "BENCHMARK:list_books_ms:0").split(":")[2]))
        ratio = round(my_ms / baseline_ms, 2)
        benchmark(f"vs_calibre_server_list_ratio", ratio)
    except Exception:
        # ignore any errors in ratio calculation
        pass

    # cleanup
    try:
        run_cmd(['docker-compose', 'down', '-v'])
    except Exception:
        pass

    benchmark("total_time_s", round(time.time() - start_total, 2))
    print("RUN_OK")

if __name__ == "__main__":
    main()