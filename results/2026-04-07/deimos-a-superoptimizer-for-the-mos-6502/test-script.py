import subprocess
import time
import tracemalloc
import os

def install_deimos():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/aran-sentin/deimos.git'], check=False)
        os.chdir('deimos')
        subprocess.run(['git', 'submodule', 'update', '--init'], check=False)
        subprocess.run(['mkdir', '-p', 'build'], check=False)
        os.chdir('build')
        subprocess.run(['cmake', '..'], check=False)
        subprocess.run(['cmake', '--build', '.'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def assemble_test_program():
    try:
        # Assemble a test program
        start_time = time.time()
        subprocess.run(['deimos', 'examples/hello.asm', '-o', 'hello'], check=False)
        assemble_time = time.time() - start_time
        print(f'BENCHMARK:assemble_time_ms:{assemble_time*1000:.2f}')
        print('TEST_PASS:assemble_test_program')
    except Exception as e:
        print(f'TEST_FAIL:assemble_test_program:{str(e)}')

def run_test_program():
    try:
        # Run the test program
        start_time = time.time()
        subprocess.run(['./hello'], check=False)
        run_time = time.time() - start_time
        print(f'BENCHMARK:run_time_ms:{run_time*1000:.2f}')
        print('TEST_PASS:run_test_program')
    except Exception as e:
        print(f'TEST_FAIL:run_test_program:{str(e)}')

def verify_test_program_output():
    try:
        # Verify the output of the test program
        output = subprocess.check_output(['./hello']).decode('utf-8')
        if 'Hello World!' in output:
            print('TEST_PASS:verify_test_program_output')
        else:
            print('TEST_FAIL:verify_test_program_output:unexpected output')
    except Exception as e:
        print(f'TEST_FAIL:verify_test_program_output:{str(e)}')

def compare_performance_with_baseline():
    try:
        # Compare the performance of DeiMOS with the MOS 6502 Assembler
        subprocess.run(['git', 'clone', 'https://github.com/aran-sentin/mos-6502-assembler.git'], check=False)
        os.chdir('mos-6502-assembler')
        start_time = time.time()
        subprocess.run(['make', 'all'], check=False)
        baseline_assemble_time = time.time() - start_time
        print(f'BENCHMARK:baseline_assemble_time_ms:{baseline_assemble_time*1000:.2f}')
        print(f'BENCHMARK:vs_mos6502_assemble_ratio:{(assemble_time/baseline_assemble_time):.2f}')
        print('TEST_PASS:compare_performance_with_baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance_with_baseline:{str(e)}')

def get_source_file_count():
    try:
        # Get the source file count
        file_count = 0
        for root, dirs, files in os.walk('deimos'):
            for file in files:
                if file.endswith('.c') or file.endswith('.cpp') or file.endswith('.h'):
                    file_count += 1
        print(f'BENCHMARK:source_file_count:{file_count}')
    except Exception as e:
        print(f'BENCHMARK:source_file_count:0')

def get_language_count():
    try:
        # Get the language count
        language_count = set()
        for root, dirs, files in os.walk('deimos'):
            for file in files:
                if file.endswith('.c') or file.endswith('.cpp') or file.endswith('.h'):
                    language_count.add(file.split('.')[-1])
        print(f'BENCHMARK:language_count:{len(language_count)}')
    except Exception as e:
        print(f'BENCHMARK:language_count:0')

def main():
    install_deimos()
    assemble_test_program()
    run_test_program()
    verify_test_program_output()
    compare_performance_with_baseline()
    get_source_file_count()
    get_language_count()
    tracemalloc.start()
    subprocess.run(['deimos', '--help'], check=False)
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{peak}')
    tracemalloc.stop()
    print('RUN_OK')

if __name__ == '__main__':
    main()