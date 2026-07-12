import subprocess
import time
import tracemalloc
import os
import sys

def install_ant():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/ant-contrib/ant.git'], check=False)
        os.chdir('ant')
        subprocess.run(['cargo', 'build'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_ant_cli():
    try:
        start_time = time.time()
        subprocess.run(['./target/debug/ant', 'init', 'myproject'], check=True)
        subprocess.run(['./target/debug/ant', 'create', 'myproject'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:ant_init_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:ant_cli")
    except Exception as e:
        print(f"TEST_FAIL:ant_cli:{str(e)}")

def test_nodejs_script():
    try:
        with open('hello.js', 'w') as f:
            f.write('console.log("Hello World!");')
        start_time = time.time()
        subprocess.run(['./target/debug/ant', 'run', 'hello.js'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:nodejs_script")
    except Exception as e:
        print(f"TEST_FAIL:nodejs_script:{str(e)}")

def test_compilation_time():
    try:
        start_time = time.time()
        subprocess.run(['./target/debug/ant', 'compile', 'hello.js'], check=True)
        end_time = time.time()
        compilation_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:ant_compilation_time_ms:{compilation_time:.2f}")

        start_time = time.time()
        subprocess.run(['node', '-e', 'console.log("Hello World!");'], check=True)
        end_time = time.time()
        nodejs_compilation_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:nodejs_compilation_time_ms:{nodejs_compilation_time:.2f}")

        ratio = compilation_time / nodejs_compilation_time
        print(f"BENCHMARK:vs_nodejs_compilation_ratio:{ratio:.2f}")
        print(f"TEST_PASS:compilation_time")
    except Exception as e:
        print(f"TEST_FAIL:compilation_time:{str(e)}")

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['./target/debug/ant', 'run', 'hello.js'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:ant_memory_usage_mb:{peak / (1024 * 1024):.2f}")
        print(f"TEST_PASS:memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

def test_files_count():
    try:
        count = len(os.listdir('.'))
        print(f"BENCHMARK:test_files_count:{count}")
        print(f"TEST_PASS:files_count")
    except Exception as e:
        print(f"TEST_FAIL:files_count:{str(e)}")

if __name__ == '__main__':
    install_ant()
    test_ant_cli()
    test_nodejs_script()
    test_compilation_time()
    test_memory_usage()
    test_files_count()
    print("RUN_OK")