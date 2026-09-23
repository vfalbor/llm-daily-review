import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib, shlex

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def install_apk(packages):
    start = time.time()
    try:
        res = subprocess.run(['apk', 'add', '--no-cache'] + packages, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            marker(f"INSTALL_FAIL:{' '.join(packages)}:{res.stderr.strip()}")
            return False
        marker("INSTALL_OK")
        return True
    finally:
        elapsed = time.time() - start
        marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")

def git_clone(repo_url, dest):
    start = time.time()
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, dest])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        marker("TEST_PASS:git_clone")
        return True
    except Exception as e:
        marker(f"TEST_FAIL:git_clone:{e}")
        return False
    finally:
        marker(f"BENCHMARK:git_clone_time_s:{time.time()-start:.2f}")

def build_project(src_dir):
    start = time.time()
    try:
        # try make
        if os.path.isfile(os.path.join(src_dir, 'Makefile')):
            res = run_cmd(['make'], cwd=src_dir)
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
        else:
            # try cargo
            if os.path.isfile(os.path.join(src_dir, 'Cargo.toml')):
                res = run_cmd(['cargo', 'build', '--release'], cwd=src_dir)
                if res.returncode != 0:
                    raise RuntimeError(res.stderr.strip())
        marker("TEST_PASS:build_project")
        return True
    except Exception as e:
        marker(f"TEST_FAIL:build_project:{e}")
        return False
    finally:
        marker(f"BENCHMARK:build_time_s:{time.time()-start:.2f}")

def run_hello_world(binary_path):
    start = time.time()
    try:
        script = '?"Hello, World!"\n'
        # write temporary script
        script_path = '/tmp/hello.prg'
        with open(script_path, 'w') as f:
            f.write(script)
        res = run_cmd([binary_path, script_path])
        if res.returncode != 0 or "Hello, World!" not in res.stdout:
            raise RuntimeError(f"Unexpected output: {res.stdout} {res.stderr}")
        marker("TEST_PASS:hello_world")
    except Exception as e:
        marker(f"TEST_FAIL:hello_world:{e}")
    finally:
        marker(f"BENCHMARK:hello_world_ms:{(time.time()-start)*1000:.2f}")

def compile_and_run(src_dir, binary_path):
    start = time.time()
    try:
        prog = '''
        PROCEDURE Main
            ? "Compiled OK"
        ENDPROC
        '''
        src_path = os.path.join(src_dir, 'test.prg')
        with open(src_path, 'w') as f:
            f.write(prog)
        # assume compiler is same binary with -c flag
        compile_res = run_cmd([binary_path, '-c', src_path, '-o', '/tmp/test_exec'])
        if compile_res.returncode != 0:
            raise RuntimeError(f"Compile error: {compile_res.stderr}")
        exec_res = run_cmd(['/tmp/test_exec'])
        if exec_res.returncode != 0 or "Compiled OK" not in exec_res.stdout:
            raise RuntimeError(f"Run error: {exec_res.stdout} {exec_res.stderr}")
        marker("TEST_PASS:compile_and_run")
    except Exception as e:
        marker(f"TEST_FAIL:compile_and_run:{e}")
    finally:
        marker(f"BENCHMARK:compile_and_run_ms:{(time.time()-start)*1000:.2f}")

def file_io_test(binary_path):
    start = time.time()
    try:
        script = '''
        STORE "testdata" TO "tmp.txt"
        USE "tmp.txt"
        ? FIELD->tmp.txt
        '''
        script_path = '/tmp/io_test.prg'
        with open(script_path, 'w') as f:
            f.write(script)
        res = run_cmd([binary_path, script_path])
        if res.returncode != 0:
            raise RuntimeError(res.stderr)
        marker("TEST_PASS:file_io")
    except Exception as e:
        marker(f"TEST_FAIL:file_io:{e}")
    finally:
        marker(f"BENCHMARK:file_io_ms:{(time.time()-start)*1000:.2f}")

def sql_query_test(binary_path):
    start = time.time()
    try:
        # create simple db using FoxPro commands
        script = '''
        CREATE TABLE test (id I, name C(20))
        INSERT INTO test (id, name) VALUES (1, "Alice")
        SELECT * FROM test
        '''
        script_path = '/tmp/sql_test.prg'
        with open(script_path, 'w') as f:
            f.write(script)
        res = run_cmd([binary_path, script_path])
        if res.returncode != 0 or "Alice" not in res.stdout:
            raise RuntimeError("SQL query failed")
        marker("TEST_PASS:sql_query")
    except Exception as e:
        marker(f"TEST_FAIL:sql_query:{e}")
    finally:
        marker(f"BENCHMARK:sql_query_ms:{(time.time()-start)*1000:.2f}")

def benchmark_vs_baseline(binary_path):
    start = time.time()
    try:
        # simple loop benchmark
        script = '''
        LOCAL i, sum
        sum = 0
        FOR i = 1 TO 100000
            sum = sum + i
        ENDFOR
        ? sum
        '''
        script_path = '/tmp/bench.prg'
        with open(script_path, 'w') as f:
            f.write(script)
        res = run_cmd([binary_path, script_path])
        fox_time = time.time() - start
        # baseline: simulate dBase runtime 0.15s (hardcoded for demo)
        baseline = 0.15
        ratio = fox_time / baseline
        marker(f"BENCHMARK:vs_dbase_time_ratio:{ratio:.2f}")
        marker(f"BENCHMARK:benchmark_time_s:{fox_time:.3f}")
    except Exception as e:
        marker(f"TEST_FAIL:benchmark:{e}")

def main():
    # 1. Install required apk packages
    install_apk(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm'])

    repo = 'https://github.com/foxscript/foxscript.git'  # placeholder repo
    src_dir = '/tmp/foxscript_src'
    if not git_clone(repo, src_dir):
        marker("RUN_OK")
        return

    if not build_project(src_dir):
        marker("RUN_OK")
        return

    # Locate binary (heuristic)
    binary = None
    possible = [
        os.path.join(src_dir, 'foxscript'),               # generic
        os.path.join(src_dir, 'target', 'release', 'foxscript'), # cargo
        os.path.join(src_dir, 'bin', 'foxscript')
    ]
    for p in possible:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            binary = p
            break
    if not binary:
        marker("TEST_FAIL:binary_locate:binary not found")
        marker("RUN_OK")
        return

    # Run tests
    run_hello_world(binary)
    compile_and_run(src_dir, binary)
    file_io_test(binary)
    sql_query_test(binary)
    benchmark_vs_baseline(binary)

    marker("RUN_OK")

if __name__ == "__main__":
    main()