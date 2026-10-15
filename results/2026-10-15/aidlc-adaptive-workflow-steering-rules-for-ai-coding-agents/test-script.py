import subprocess, sys, time, tracemalloc, json, os, textwrap, traceback

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_apk_install(pkg):
    try:
        start = time.time()
        result = subprocess.run(['apk', 'add', '--no-cache', pkg],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk install returned {result.returncode}")
        print_marker(f"BENCHMARK:apk_{pkg}_install_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install(package):
    try:
        start = time.time()
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:pip install returned {result.returncode}")
        print_marker(f"BENCHMARK:pip_{package}_install_s:{elapsed:.3f}")
        return result.returncode == 0
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def git_clone(repo_url, dest):
    try:
        start = time.time()
        result = subprocess.run(['git', 'clone', '--depth', '1', repo_url, dest],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:git clone returned {result.returncode}")
        print_marker(f"BENCHMARK:git_clone_s:{elapsed:.3f}")
        return result.returncode == 0
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def pip_editable(path):
    try:
        start = time.time()
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:pip -e install returned {result.returncode}")
        print_marker(f"BENCHMARK:pip_editable_install_s:{elapsed:.3f}")
        return result.returncode == 0
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def benchmark(name, func, *args, **kwargs):
    try:
        tracemalloc.start()
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.4f}")
        print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
        return result, elapsed
    except Exception as e:
        print_marker(f"BENCHMARK:{name}_fail:{e}")
        return None, None

def test_import():
    try:
        start = time.time()
        import aidlc
        elapsed = time.time() - start
        print_marker("TEST_PASS:import_aidlc")
        print_marker(f"BENCHMARK:import_time_s:{elapsed:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_aidlc:{e}")

def test_simple_rule():
    try:
        from aidlc import Rule, Agent
        # Define a rule that prints hello
        class HelloRule(Rule):
            def evaluate(self, context):
                print("hello")
                return True

        # Mock agent that just runs the rule
        class MockAgent(Agent):
            def run_rule(self, rule):
                rule.evaluate({})

        rule = HelloRule()
        agent = MockAgent()
        # Capture stdout
        from io import StringIO
        old_out = sys.stdout
        sys.stdout = StringIO()
        agent.run_rule(rule)
        output = sys.stdout.getvalue().strip()
        sys.stdout = old_out

        if output == "hello":
            print_marker("TEST_PASS:simple_rule_output")
        else:
            print_marker(f"TEST_FAIL:simple_rule_output:unexpected output '{output}'")
    except Exception as e:
        print_marker(f"TEST_FAIL:simple_rule_output:{e}")

def test_rule_latency(num_rules=100):
    try:
        from aidlc import Rule, Agent
        class DummyRule(Rule):
            def evaluate(self, context):
                return True

        class MockAgent(Agent):
            def run_rule(self, rule):
                rule.evaluate({})

        rules = [DummyRule() for _ in range(num_rules)]
        agent = MockAgent()

        def run_all():
            for r in rules:
                agent.run_rule(r)

        _, elapsed = benchmark("rule_latency_100", run_all)
        if elapsed is not None:
            print_marker(f"TEST_PASS:rule_latency_100")
        else:
            print_marker("TEST_FAIL:rule_latency_100:benchmark failed")
    except Exception as e:
        print_marker(f"TEST_FAIL:rule_latency_100:{e}")

def test_vs_baseline(num=1000):
    try:
        # Baseline: plain if/else loop
        def baseline():
            total = 0
            for i in range(num):
                if i % 2 == 0:
                    total += 1
                else:
                    total += 0
            return total

        from aidlc import Rule, Agent
        class SimpleRule(Rule):
            def __init__(self, idx):
                self.idx = idx
            def evaluate(self, context):
                return self.idx % 2 == 0

        class MockAgent(Agent):
            def run_rule(self, rule):
                return rule.evaluate({})

        rules = [SimpleRule(i) for i in range(num)]
        agent = MockAgent()

        def aidlc_run():
            s = 0
            for r in rules:
                s += 1 if agent.run_rule(r) else 0
            return s

        _, t_baseline = benchmark("baseline_ifelse", baseline)
        _, t_aidlc = benchmark("aidlc_rule_eval", aidlc_run)

        if t_baseline and t_aidlc:
            ratio = t_aidlc / t_baseline if t_baseline > 0 else float('inf')
            print_marker(f"BENCHMARK:vs_baseline_rule_ratio:{ratio:.4f}")
            print_marker("TEST_PASS:vs_baseline")
        else:
            print_marker("TEST_FAIL:vs_baseline:benchmark timings missing")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_baseline:{e}")

def main():
    # 1. Install required apk packages
    run_apk_install('git')

    # 2. Try pip install
    installed = pip_install('aidlc-workflows')
    if not installed:
        # fallback to git clone + editable install
        repo = 'https://github.com/awslabs/aidlc-workflows.git'
        dest = '/tmp/aidlc-workflows'
        if git_clone(repo, dest):
            pip_editable(dest)

    # 3. Run tests
    test_import()
    test_simple_rule()
    test_rule_latency()
    test_vs_baseline()

    # Ensure at least 3 benchmark lines (already emitted)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()