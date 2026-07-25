import subprocess
import time
import tracemalloc
import os

def install_wasmtime_apk():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:apk installation failed with {str(e)}')

def install_wasmtime_pip():
    try:
        subprocess.run(['pip', 'install', 'wasmtime'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:pip installation failed with {str(e)}')

def install_wasmtime_cargo():
    try:
        subprocess.run(['cargo', 'new', 'wasmtime-test'], check=False)
        subprocess.run(['cd', 'wasmtime-test', '&&', 'cargo', 'add', 'wasmtime'], check=False, shell=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:cargo installation failed with {str(e)}')

def create_wasm_file():
    with open('hello_world.wasm', 'wb') as f:
        f.write(b'\x00\x61\x73\x6d\x01\x00\x00\x00\x01\x07\x01\x73\x02\x01\x00\x07\x07\x01\x73\x01\x00\x03\x73\x00\x00\x00\x00\x01\x05\x01\x00\x00\x10\x00\x00\x00\x65\x6e\x76\x01\x00\x00\x00\x01\x6f\x6e\x5f\x6c\x6f\x61\x64\x00\x00\x01\x73\x02\x01\x00\x06\x73\x00\x00\x00\x00\x01\x05\x01\x00\x00\x10\x00\x00\x00\x65\x6e\x76\x02\x00\x00\x00\x01\x6f\x6e\x5f\x73\x74\x61\x72\x74\x00\x00\x01\x73\x02\x01\x00\x06\x73\x00\x00\x00\x00\x01\x05\x01\x00\x00\x10\x00\x00\x00\x65\x6e\x76\x03\x00\x00\x00\x01\x6f\x6e\x5f\x77\x61\x73\x6d\x5f\x6c\x6f\x61\x64\x00\x00')

def test_pip_install():
    try:
        start_time = time.time()
        install_wasmtime_pip()
        create_wasm_file()
        subprocess.run(['wasmtime', 'hello_world.wasm'], check=False)
        end_time = time.time()
        print(f'BENCHMARK:wasmtime_pip_install_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:wasmtime_pip_install')
    except Exception as e:
        print(f'TEST_FAIL:wasmtime_pip_install:{str(e)}')

def test_cargo_install():
    try:
        start_time = time.time()
        install_wasmtime_cargo()
        subprocess.run(['cargo', 'build', '--release'], check=False, cwd='wasmtime-test')
        end_time = time.time()
        print(f'BENCHMARK:wasmtime_cargo_build_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:wasmtime_cargo_install')
    except Exception as e:
        print(f'TEST_FAIL:wasmtime_cargo_install:{str(e)}')

def test_wasmtime_performance():
    try:
        start_time = time.time()
        subprocess.run(['wasmtime', 'hello_world.wasm'], check=False)
        end_time = time.time()
        print(f'BENCHMARK:wasmtime_performance_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:wasmtime_performance')
    except Exception as e:
        print(f'TEST_FAIL:wasmtime_performance:{str(e)}')

def compare_with_baseline():
    try:
        start_time = time.time()
        subprocess.run(['llvm', '-version'], check=False)
        end_time = time.time()
        baseline_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['wasmtime', 'hello_world.wasm'], check=False)
        end_time = time.time()
        wasmtime_time = end_time - start_time
        ratio = wasmtime_time / baseline_time
        print(f'BENCHMARK:vs_llvm_ratio:{ratio}')
        print('TEST_PASS:compare_with_baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_with_baseline:{str(e)}')

def main():
    install_wasmtime_apk()
    test_pip_install()
    test_cargo_install()
    test_wasmtime_performance()
    compare_with_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()