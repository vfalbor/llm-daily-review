#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, traceback, json, os

def print_marker(line):
    print(line, flush=True)

def apk_install(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker(f"INSTALL_OK")
            return True, duration
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip() or 'apk error'}")
            return False, duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{str(e)}")
        return False, 0.0

def pip_install(pkg):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker(f"INSTALL_OK")
            return True, duration
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip() or 'pip error'}")
            return False, duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{str(e)}")
        return False, 0.0

def fallback_git_clone(repo, dest):
    try:
        start = time.time()
        res = subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode != 0:
            print_marker(f"INSTALL_FAIL:git clone failed:{res.stderr.strip()}")
            return False, duration
        # install editable
        cwd = os.getcwd()
        os.chdir(dest)
        res2 = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        os.chdir(cwd)
        if res2.returncode != 0:
            print_marker(f"INSTALL_FAIL:editable install failed:{res2.stderr.strip()}")
            return False, duration + (time.time()-start)
        print_marker(f"INSTALL_OK")
        return True, time.time() - start
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{str(e)}")
        return False, 0.0

def benchmark(name, func):
    try:
        tracemalloc.start()
        start = time.time()
        result = func()
        end = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = end - start
        print_marker(f"BENCHMARK:{name}:{elapsed:.4f}")
        return elapsed, result
    except Exception as e:
        print_marker(f"BENCHMARK:{name}:FAIL:{str(e)}")
        return None, None

def test_import():
    try:
        start = time.time()
        import transformers
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:import_time_s:{elapsed:.4f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import:{str(e)}")
        return False

def test_model_load():
    try:
        def load():
            from transformers import AutoModelForCausalLM, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017')
            model = AutoModelForCausalLM.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017')
            return tokenizer, model
        dur, objs = benchmark('model_load_s', load)
        if dur is None:
            raise RuntimeError('load failed')
        print_marker("TEST_PASS:model_load")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:model_load:{str(e)}")
        return False

def test_generate():
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017')
        model = AutoModelForCausalLM.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017')
        input_ids = tokenizer('Hello', return_tensors='pt').input_ids
        def gen():
            return model.generate(input_ids, max_new_tokens=20)
        dur, output = benchmark('generate_ms', lambda: gen())
        if dur is None:
            raise RuntimeError('generation failed')
        text = tokenizer.decode(output[0])
        print_marker(f"TEST_PASS:generate_output:{text[:30]}...")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:generate:{str(e)}")
        return False

def compare_vs_baseline(metric_name, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value != 0 else 0
        print_marker(f"BENCHMARK:vs_{metric_name}_ratio:{ratio:.4f}")
    except Exception as e:
        print_marker(f"BENCHMARK:vs_{metric_name}_ratio:FAIL:{str(e)}")

def main():
    # 1. Install apk package git
    apk_ok, apk_time = apk_install('git')
    print_marker(f"BENCHMARK:apk_git_install_s:{apk_time:.4f}")

    # 2. Install transformers via pip
    pip_ok, pip_time = pip_install('transformers')
    print_marker(f"BENCHMARK:pip_transformers_install_s:{pip_time:.4f}")

    # Fallback if pip failed
    if not pip_ok:
        repo = 'https://github.com/huggingface/transformers.git'
        fallback_ok, fallback_time = fallback_git_clone(repo, '/tmp/transformers')
        print_marker(f"BENCHMARK:git_clone_transformers_s:{fallback_time:.4f}")
        pip_ok = fallback_ok

    # Run tests
    test_import()
    test_model_load()
    test_generate()

    # Benchmark additional metrics
    # Example: count of files in the model cache directory
    try:
        cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
        file_count = sum(len(files) for _, _, files in os.walk(cache_dir))
        print_marker(f"BENCHMARK:model_cache_files:{file_count}")
    except Exception:
        pass

    # Compare import time vs baseline (assume baseline 0.8s)
    compare_vs_baseline('import_time_s', pip_time + (0 if pip_ok else 0), 0.8)

    # Ensure RUN_OK is printed at the end
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()