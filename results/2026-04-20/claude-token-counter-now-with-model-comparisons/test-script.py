import subprocess
import time
import tracemalloc
import sys

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_tool_dependencies():
    try:
        subprocess.run(['pip', 'install', 'git+https://github.com/simonw/claude-token-counter.git'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/simonw/claude-token-counter.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './claude-token-counter'], check=True)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def run_test():
    try:
        import claude_token_counter
        import time
        start_time = time.time()
        claude_token_counter.count_tokens(["This is a test sentence"])
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:token_count")
    except Exception as e:
        print(f"TEST_FAIL:token_count:{str(e)}")

def run_benchmark():
    try:
        import claude_token_counter
        import time
        tracemalloc.start()
        start_time = time.time()
        claude_token_counter.count_tokens(["This is a test sentence"] * 100)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:token_count_latency_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:token_count_memory_mb:{current / 10**6}")
        tracemalloc.stop()
    except Exception as e:
        print(f"TEST_FAIL:token_count_benchmark:{str(e)}")

def compare_with_baseline():
    try:
        import lm_eval
        import time
        start_time = time.time()
        lm_eval.count_tokens(["This is a test sentence"])
        end_time = time.time()
        import claude_token_counter
        claude_start_time = time.time()
        claude_token_counter.count_tokens(["This is a test sentence"])
        claude_end_time = time.time()
        print(f"BENCHMARK:vs_lm_eval_token_count_ratio:{(claude_end_time - claude_start_time) / (end_time - start_time)}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_comparison:{str(e)}")

install_dependencies()
install_tool_dependencies()
run_test()
run_benchmark()
compare_with_baseline()
print("RUN_OK")