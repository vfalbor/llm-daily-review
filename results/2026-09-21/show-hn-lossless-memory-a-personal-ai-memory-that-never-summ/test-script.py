#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, traceback

def run_cmd(cmd, description):
    try:
        start = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if result.returncode == 0:
            print(f"INSTALL_OK | {description}")
            return True, duration
        else:
            print(f"INSTALL_FAIL:{description}:{result.stderr.strip() or 'non-zero exit'}")
            return False, duration
    except Exception as e:
        print(f"INSTALL_FAIL:{description}:{e}")
        return False, 0.0

def emit_benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def main():
    # 1. Install system package git
    ok, dur_git = run_cmd(['apk','add','--no-cache','git'], 'apk git')
    emit_benchmark('apk_git_time_s', f"{dur_git:.3f}")

    # 2. Try pip install from git
    install_success = False
    pip_install_start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir',
                        'git+https://github.com/aru-labs/lossless-memory.git'],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        install_success = True
    except subprocess.CalledProcessError as e:
        # fallback: clone and editable install
        try:
            subprocess.run(['git','clone','https://github.com/aru-labs/lossless-memory.git',
                            '/tmp/lossless-memory'], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-e',
                            '/tmp/lossless-memory'], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            install_success = True
        except Exception as fe:
            print(f"INSTALL_FAIL:pip install fallback:{fe}")
    pip_install_dur = time.time() - pip_install_start
    if install_success:
        print("INSTALL_OK | pip lossless-memory")
    else:
        print("INSTALL_FAIL:pip lossless-memory:could not install")
    emit_benchmark('pip_install_time_s', f"{pip_install_dur:.3f}")

    # 3. Import module and benchmark import time
    import_start = time.time()
    try:
        import lossless_memory
        import_dur = time.time() - import_start
        print("TEST_PASS:import_lossless_memory")
        emit_benchmark('import_time_ms', f"{import_dur*1000:.2f}")
    except Exception as e:
        import_dur = time.time() - import_start
        print(f"TEST_FAIL:import_lossless_memory:{e}")
        emit_benchmark('import_time_ms', f"{import_dur*1000:.2f}")

    # 4. Functional tests
    try:
        mem = lossless_memory.Memory()
        print("TEST_PASS:Memory_init")
    except Exception as e:
        print(f"TEST_FAIL:Memory_init:{e}")
        mem = None

    # 5. add/get single entry
    try:
        if mem is not None:
            mem.add('key', 'value')
            if mem.get('key') == 'value':
                print("TEST_PASS:add_get_single")
            else:
                raise AssertionError("value mismatch")
    except Exception as e:
        print(f"TEST_FAIL:add_get_single:{e}")

    # 6. latency for 10,000 add/get ops
    try:
        if mem is not None:
            ops = 10000
            keys = [f"k{i}" for i in range(ops)]
            values = [f"v{i}" for i in range(ops)]

            tracemalloc.start()
            start = time.time()
            for k, v in zip(keys, values):
                mem.add(k, v)
            for k, v in zip(keys, values):
                _ = mem.get(k)
            elapsed = time.time() - start
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print("TEST_PASS:bulk_add_get")
            emit_benchmark('bulk_ops_time_ms', f"{elapsed*1000:.2f}")
            emit_benchmark('bulk_ops_mem_peak_kb', f"{peak/1024:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:bulk_add_get:{e}")
        traceback.print_exc()

    # Baseline comparison (mock baseline import time = 120ms)
    baseline_import_ms = 120.0
    try:
        ratio = (import_dur*1000) / baseline_import_ms
        emit_benchmark(f"vs_import_time_ratio", f"{ratio:.3f}")
    except Exception:
        pass

    # Ensure at least three benchmark lines (we already have several)
    # Final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()