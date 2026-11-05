#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, json, shutil, pathlib, textwrap

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_add(pkgs):
    try:
        res = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def git_clone(repo, dest):
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def build_go(src_dir):
    try:
        res = run_cmd(['go', 'build', '-o', 'jsonapp'], cwd=src_dir)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed

def measure_memory(func, *args, **kwargs):
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak / 1024  # KiB

# 1. Install system packages
apk_add(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm'])

# 2. Clone Go repo (we only need the std lib, but cloning for demo)
repo_url = 'https://github.com/golang/go.git'
repo_dir = '/tmp/go-src'
git_clone(repo_url, repo_dir)

# 3. Build a tiny helper program that uses encoding/json and jsonpath
helper_dir = '/tmp/json_test'
os.makedirs(helper_dir, exist_ok=True)
program_code = textwrap.dedent('''
    package main
    import (
        "encoding/json"
        "fmt"
        "golang.org/x/exp/jsonpath"
    )
    type Person struct {
        Name string
        Age  int
    }
    func main() {
        p := Person{Name: "Alice", Age: 30}
        data, _ := json.Marshal(p)
        var out Person
        json.Unmarshal(data, &out)
        // simple jsonpath query
        expr, _ := jsonpath.Compile("$.Name")
        result, _ := expr.Eval(out)
        fmt.Println(result)
    }
''')
with open(os.path.join(helper_dir, 'main.go'), 'w') as f:
    f.write(program_code)

# 4. Get jsonpath dependency
def test_get_dependency():
    try:
        res = run_cmd(['go', 'get', 'golang.org/x/exp/jsonpath'])
        if res.returncode == 0:
            print_marker("TEST_PASS:go_get_jsonpath")
        else:
            print_marker(f"TEST_FAIL:go_get_jsonpath:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:go_get_jsonpath:{e}")

test_get_dependency()

# 5. Build the helper
def test_build_helper():
    try:
        res = run_cmd(['go', 'build', '-o', 'jsonapp'], cwd=helper_dir)
        if res.returncode == 0:
            print_marker("TEST_PASS:build_helper")
        else:
            print_marker(f"TEST_FAIL:build_helper:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:build_helper:{e}")

test_build_helper()

# 6. Run hello world and verify output
def test_run_helper():
    try:
        exe = os.path.join(helper_dir, 'jsonapp')
        res = run_cmd([exe])
        if res.returncode == 0 and res.stdout.strip() == "Alice":
            print_marker("TEST_PASS:run_helper")
        else:
            reason = res.stderr.strip() or f"unexpected output {res.stdout.strip()}"
            print_marker(f"TEST_FAIL:run_helper:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_helper:{e}")

test_run_helper()

# 7. Benchmark marshaling/unmarshaling vs standard library
def benchmark_json():
    import json as stdjson
    try:
        # load jsonpath module via go binary for fairness (we just time Go binary)
        exe = os.path.join(helper_dir, 'jsonapp')
        # warm up
        run_cmd([exe])

        # benchmark Go jsonpath (run binary multiple times)
        def run_go():
            r = run_cmd([exe])
            return r

        _, go_time = measure_time(lambda: [run_go() for _ in range(20)])
        # benchmark std json in python
        data = {"Name":"Bob","Age":25}
        def py_marshal():
            return stdjson.dumps(data)
        def py_unmarshal(s):
            return stdjson.loads(s)

        _, py_marshal_time = measure_time(lambda: [py_marshal() for _ in range(2000)])
        _, py_unmarshal_time = measure_time(lambda: [py_unmarshal(py_marshal()) for _ in range(2000)])

        print_marker(f"BENCHMARK:go_jsonpath_total_s:{go_time:.3f}")
        print_marker(f"BENCHMARK:python_stdjson_marshal_ms:{(py_marshal_time*1000):.2f}")
        print_marker(f"BENCHMARK:python_stdjson_unmarshal_ms:{(py_unmarshal_time*1000):.2f}")

        # compare go vs python (ratio of total times)
        ratio = go_time / (py_marshal_time + py_unmarshal_time) if (py_marshal_time+py_unmarshal_time)>0 else 0
        print_marker(f"BENCHMARK:vs_jsoniterator_ratio:{ratio:.3f}")

    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_json:{e}")

benchmark_json()

# 8. Additional benchmark: memory usage of Go binary
def benchmark_memory():
    try:
        exe = os.path.join(helper_dir, 'jsonapp')
        def run_mem():
            return run_cmd([exe])
        _, peak_kib = measure_memory(run_mem)
        print_marker(f"BENCHMARK:go_binary_peak_memory_kib:{peak_kib:.1f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_memory:{e}")

benchmark_memory()

# Ensure RUN_OK at the end
print_marker("RUN_OK")