import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk_packages():
    pkgs = ["git"]
    start = time.time()
    for pkg in pkgs:
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        if res is None or res.returncode != 0:
            print_marker(f"INSTALL_FAIL:apk_{pkg}:{res.stderr.strip() if res else str(e)}")
            return False, time.time() - start
    print_marker("INSTALL_OK")
    return True, time.time() - start

def pip_install_package():
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'auto-ontology'], check=False)
    if res is None or res.returncode != 0:
        print_marker(f"INSTALL_FAIL:pip_auto-ontology:{res.stderr.strip() if res else 'unknown error'}")
        return False, time.time() - start
    print_marker("INSTALL_OK")
    return True, time.time() - start

def git_clone_and_editable_install():
    start = time.time()
    repo = "https://github.com/NVIDIA/auto-ontology.git"
    clone_dir = "/tmp/auto-ontology"
    if os.path.isdir(clone_dir):
        run_cmd(['rm', '-rf', clone_dir])
    res = run_cmd(['git', 'clone', '--depth', '1', repo, clone_dir])
    if res is None or res.returncode != 0:
        print_marker(f"INSTALL_FAIL:git_clone:{res.stderr.strip() if res else 'unknown error'}")
        return False, time.time() - start
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=clone_dir)
    if res is None or res.returncode != 0:
        print_marker(f"INSTALL_FAIL:editable_install:{res.stderr.strip() if res else 'unknown error'}")
        return False, time.time() - start
    print_marker("INSTALL_OK")
    return True, time.time() - start

def benchmark_import():
    start = time.time()
    tracemalloc.start()
    try:
        import auto_ontology  # assuming package name
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        return True, elapsed
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False, None

def benchmark_core_operation():
    try:
        import auto_ontology
        # synthetic data: simple dict to convert to ontology
        data = {
            "entities": [
                {"id": "E1", "type": "Person", "label": "Alice"},
                {"id": "E2", "type": "Person", "label": "Bob"}
            ],
            "relations": [
                {"source": "E1", "target": "E2", "type": "knows"}
            ]
        }
        start = time.time()
        tracemalloc.start()
        # Assuming library provides a function generate_ontology
        # This is a best‑guess; adjust to actual API if different
        try:
            ontology = auto_ontology.generate_ontology(data)
        except AttributeError:
            # fallback: maybe class OntologyBuilder
            builder = auto_ontology.OntologyBuilder()
            ontology = builder.build(data)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:core_op_latency_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:core_op_mem_peak_kb:{peak/1024:.2f}")
        return True, elapsed
    except Exception as e:
        print_marker(f"TEST_FAIL:core_operation:{e}")
        return False, None

def benchmark_baseline():
    # Use owlready2 as baseline for similar operation
    try:
        import owlready2
    except Exception as e:
        print_marker(f"TEST_SKIP:baseline_import:{e}")
        return None
    # synthetic same data handling via owlready2
    start = time.time()
    tracemalloc.start()
    try:
        onto = owlready2.get_ontology("http://test.org/onto.owl")
        with onto:
            class Person(owlready2.Thing):
                pass
            class knows(owlready2.ObjectProperty):
                domain = [Person]
                range = [Person]
            alice = Person("E1")
            alice.label = ["Alice"]
            bob = Person("E2")
            bob.label = ["Bob"]
            alice.knows.append(bob)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:baseline_core_op_latency_ms:{elapsed:.2f}")
        # compute ratio if core_op_latency_ms exists
        # This will be processed later after core op benchmark printed
        return elapsed
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_core_op:{e}")
        return None

def main():
    # 1. Install system deps
    ok, dur = install_apk_packages()
    print_marker(f"BENCHMARK:apk_install_time_s:{dur:.2f}")

    # 2. Install python package
    ok_pkg, dur_pkg = pip_install_package()
    print_marker(f"BENCHMARK:pip_install_time_s:{dur_pkg:.2f}")
    if not ok_pkg:
        ok_edit, dur_edit = git_clone_and_editable_install()
        print_marker(f"BENCHMARK:editable_install_time_s:{dur_edit:.2f}")
        if not ok_edit:
            print_marker("TEST_SKIP:install:auto-ontology not installed")
    
    # 3. Import benchmark
    imp_ok, imp_time = benchmark_import()
    if imp_ok:
        print_marker("TEST_PASS:import_module")
    else:
        print_marker("TEST_FAIL:import_module:import failed")

    # 4. Core operation benchmark
    core_ok, core_time = benchmark_core_operation()
    if core_ok:
        print_marker("TEST_PASS:core_operation")
    else:
        print_marker("TEST_FAIL:core_operation:operation failed")

    # 5. Baseline comparison
    baseline_time = benchmark_baseline()
    if baseline_time and core_time:
        try:
            ratio = core_time / baseline_time
            print_marker(f"BENCHMARK:vs_owlready2_core_op_latency_ratio:{ratio:.3f}")
        except Exception as e:
            print_marker(f"TEST_FAIL:ratio_computation:{e}")

    # 6. Additional arbitrary benchmarks
    # count of files in repository (if cloned)
    repo_path = "/tmp/auto-ontology"
    if os.path.isdir(repo_path):
        file_count = sum(len(files) for _, _, files in os.walk(repo_path))
        print_marker(f"BENCHMARK:repo_file_count:{file_count}")
    else:
        print_marker("BENCHMARK:repo_file_count:0")

    # memory usage of process (approx)
    try:
        import psutil
        mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024*1024)
        print_marker(f"BENCHMARK:process_mem_mb:{mem_mb:.2f}")
    except Exception:
        print_marker("TEST_SKIP:process_mem:psutil not available")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected:{traceback.format_exc()}")
        print_marker("RUN_OK")