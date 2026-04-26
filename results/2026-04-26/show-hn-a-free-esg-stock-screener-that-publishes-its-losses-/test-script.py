import subprocess
import time
import tracemalloc
import os

def install_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_pip(pkg):
    try:
        subprocess.run(['pip', 'install', pkg], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_npm(pkg):
    try:
        subprocess.run(['npm', 'install', '-g', pkg], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_cargo(pkg):
    try:
        subprocess.run(['cargo', 'install', pkg], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_jumpstartsignal():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['jumpstartsignal', '--help'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:jumpstartsignal_help_time_ms:{int((end_time - start_time) * 1000)}")
        print(f"BENCHMARK:jumpstartsignal_help_peak_memory_mb:{peak / 1024 / 1024}")
        print("TEST_PASS:jumpstartsignal_help")
    except Exception as e:
        print(f"TEST_FAIL:jumpstartsignal_help:{str(e)}")

def test_esgtool():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['esgtool', '--help'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:esgtool_help_time_ms:{int((end_time - start_time) * 1000)}")
        print(f"BENCHMARK:esgtool_help_peak_memory_mb:{peak / 1024 / 1024}")
        print("TEST_PASS:esgtool_help")
    except Exception as e:
        print(f"TEST_FAIL:esgtool_help:{str(e)}")

def compare_performance():
    try:
        jumpstartsignal_time = int(subprocess.check_output(['grep', 'jumpstartsignal_help_time_ms:', 'benchmark.log']).decode('utf-8').split(':')[1].strip())
        esgtool_time = int(subprocess.check_output(['grep', 'esgtool_help_time_ms:', 'benchmark.log']).decode('utf-8').split(':')[1].strip())
        ratio = jumpstartsignal_time / esgtool_time
        print(f"BENCHMARK:vs_esgtool_help_time_ratio:{ratio}")
    except Exception as e:
        print(f"BENCHMARK:vs_esgtool_help_time_ratio:None")

def main():
    install_apk('nodejs')
    install_apk('npm')
    install_apk('git')
    install_apk('cargo')
    install_apk('rust')
    install_npm('jumpstartsignal')
    install_pip('esgtool')
    test_jumpstartsignal()
    test_esgtool()
    compare_performance()
    print("RUN_OK")

if __name__ == "__main__":
    main()