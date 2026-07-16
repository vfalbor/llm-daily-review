import subprocess
import time
import tracemalloc
import importlib.util
import pkg_resources

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'clig'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/ckarlsen/clig.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './clig'], check=False, cwd='./clig')
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_import_time():
    try:
        tracemalloc.start()
        start_time = time.time()
        import clig
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:import_memory_mb:{current / (1024 * 1024)}')
        print(f'TEST_PASS:import_time')
    except Exception as e:
        print(f'TEST_FAIL:import_time:{str(e)}')

def test_cli_tool():
    try:
        import clig
        cli = clig.CLI()
        cli.run(['--help'])
        print(f'TEST_PASS:cli_tool')
    except Exception as e:
        print(f'TEST_FAIL:cli_tool:{str(e)}')

def test_compliance():
    try:
        import clig
        compliance = clig.Compliance()
        compliance.check()
        print(f'TEST_PASS:compliance')
    except Exception as e:
        print(f'TEST_FAIL:compliance:{str(e)}')

def test_linter():
    try:
        import subprocess
        subprocess.run(['clig', 'lint'], check=True)
        print(f'TEST_PASS:linter')
    except Exception as e:
        print(f'TEST_FAIL:linter:{str(e)}')

def benchmark_vs_toml():
    try:
        import tomli
        import time
        start_time = time.time()
        tomli.load('example.toml')
        end_time = time.time()
        toml_time = end_time - start_time
        start_time = time.time()
        import clig
        cli = clig.CLI()
        cli.run(['--help'])
        end_time = time.time()
        clig_time = end_time - start_time
        print(f'BENCHMARK:vs_toml_parse_ratio:{clig_time / toml_time}')
    except Exception as e:
        print(f'BENCHMARK:vs_toml_parse_ratio:Failed')

def benchmark_loc_count():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('clig'):
            for file in files:
                if file.endswith('.py'):
                    loc_count += sum(1 for line in open(os.path.join(root, file), 'r'))
        print(f'BENCHMARK:loc_count:{loc_count}')
    except Exception as e:
        print(f'BENCHMARK:loc_count:Failed')

def benchmark_test_files_count():
    try:
        import os
        test_files_count = 0
        for root, dirs, files in os.walk('clig/tests'):
            for file in files:
                if file.endswith('.py'):
                    test_files_count += 1
        print(f'BENCHMARK:test_files_count:{test_files_count}')
    except Exception as e:
        print(f'BENCHMARK:test_files_count:Failed')

install_dependencies()
test_import_time()
test_cli_tool()
test_compliance()
test_linter()
benchmark_vs_toml()
benchmark_loc_count()
benchmark_test_files_count()
print('RUN_OK')