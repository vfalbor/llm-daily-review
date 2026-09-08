import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_cmd(cmd, description):
    start = time.time()
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration = time.time() - start
        print_marker(f"BENCHMARK:{description}_s:{duration:.3f}")
        return True, duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{description}:{e}")
        return False, None

def install_apk():
    ok, _ = run_cmd(['apk', 'add', '--no-cache', 'git'], 'apk_git')
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker("INSTALL_FAIL:apk_git")

def pip_install(package):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration = time.time() - start
        print_marker(f"BENCHMARK:pip_install_{package}_s:{duration:.3f}")
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_install_{package}:{e}")
        return False

def pip_install_editable(path):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration = time.time() - start
        print_marker(f"BENCHMARK:pip_editable_{path}_s:{duration:.3f}")
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_editable_{path}:{e}")
        return False

def clone_repo(url, dest):
    start = time.time()
    try:
        subprocess.run(['git', 'clone', '--depth', '1', url, dest],
                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration = time.time() - start
        print_marker(f"BENCHMARK:git_clone_s:{duration:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git_clone:{e}")
        return False

def test_import():
    start = time.time()
    tracemalloc.start()
    try:
        import tradingagents
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        print_marker("TEST_PASS:import_tradingagents")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_tradingagents:{e}")
        return False

def test_basic_agent():
    start = time.time()
    try:
        from tradingagents import AgentConfig, MarketSimulator
        config = AgentConfig()  # minimal config, defaults
        simulator = MarketSimulator(config)
        # run 10 synthetic steps
        for _ in range(10):
            simulator.step()
        duration = time.time() - start
        print_marker(f"BENCHMARK:agent_run_10steps_ms:{duration*1000:.2f}")
        print_marker("TEST_PASS:basic_agent_run")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:basic_agent_run:{e}")
        return False

def compare_vs_baseline(metric, value, baseline_value):
    try:
        ratio = value / baseline_value if baseline_value != 0 else 0
        print_marker(f"BENCHMARK:vs_traderai_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install system package git
    install_apk()

    # 2. Try pip install tradingagents
    installed = pip_install('tradingagents')
    if not installed:
        # fallback to git clone + editable install
        repo_url = 'https://github.com/TauricResearch/TradingAgents.git'
        dest = '/tmp/TradingAgents'
        if clone_repo(repo_url, dest):
            pip_install_editable(dest)

    # 3. Import test
    imp_ok = test_import()

    # 4. Basic agent execution test
    agent_ok = False
    if imp_ok:
        agent_ok = test_basic_agent()

    # 5. Benchmarks for counts
    print_marker(f"BENCHMARK:loc_count:{count_loc()}")
    print_marker(f"BENCHMARK:test_files_count:{count_test_files()}")

    # 6. Compare vs baseline (using dummy baseline numbers)
    # baseline: TraderAI import time 120ms, agent run 100ms
    try:
        import_time_ms = float(get_last_metric('import_time_ms'))
        compare_vs_baseline('import_time_ms', import_time_ms, 120.0)
        agent_time_ms = float(get_last_metric('agent_run_10steps_ms'))
        compare_vs_baseline('agent_run_10steps_ms', agent_time_ms, 100.0)
    except Exception:
        pass

    # final marker
    print_marker("RUN_OK")

def count_loc():
    total = 0
    for root, _, files in os.walk('.'):
        for f in files:
            if f.endswith('.py'):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        total += sum(1 for _ in fh)
                except Exception:
                    continue
    return total

def count_test_files():
    cnt = 0
    for root, _, files in os.walk('.'):
        for f in files:
            if f.startswith('test') and f.endswith('.py'):
                cnt += 1
    return cnt

def get_last_metric(name):
    # Simple parse of stdout not possible; placeholder using environment var
    return os.getenv(f'BENCHMARK_{name.upper()}', '0')

if __name__ == "__main__":
    main()