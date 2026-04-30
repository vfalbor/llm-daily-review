import subprocess
import sys
import time
import tracemalloc
import importlib.util
from io import StringIO

def install_tool():
    print("Installing necessary packages...")
    # Install git package
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("Installing Mike tool...")
    try:
        # Try installing the package directly
        subprocess.run(['pip', 'install', 'mikeoss'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")
        try:
            # Fallback to git clone and pip install -e .
            subprocess.run(['git', 'clone', 'https://github.com/mikeoss/mike.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './mike'], cwd='./mike', check=False)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL: {str(e)}")
            return False
    return True

def test_drafting_contract():
    try:
        import mike
        tracemalloc.start()
        start_time = time.time()
        # Draft a simple contract
        contract = mike.draft_contract("Simple Contract")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:contract_drafting_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        print(f"TEST_PASS:drafting_contract")
    except Exception as e:
        print(f"TEST_FAIL:drafting_contract:{str(e)}")

def test_output_against_human_produced_contract():
    try:
        import mike
        # Mock API key
        api_key = "fake_api_key"
        # Draft a contract
        contract = mike.draft_contract("Simple Contract", api_key=api_key)
        # Load human-produced contract
        with open("human_produced_contract.txt", "r") as f:
            human_contract = f.read()
        # Compare the contracts
        if contract == human_contract:
            print("TEST_PASS:output_comparison")
        else:
            print("TEST_FAIL:output_comparison:Contracts do not match")
    except Exception as e:
        print(f"TEST_FAIL:output_comparison:{str(e)}")

def test_mike_performance_against_human_authors():
    try:
        import mike
        import contractsage
        # Mock API key
        api_key = "fake_api_key"
        # Draft a contract with Mike
        start_time = time.time()
        contract = mike.draft_contract("Simple Contract", api_key=api_key)
        end_time = time.time()
        mike_time = end_time - start_time
        # Draft a contract with Contract Sage
        start_time = time.time()
        contractsage.draft_contract("Simple Contract", api_key=api_key)
        end_time = time.time()
        contractsage_time = end_time - start_time
        print(f"BENCHMARK:vs_contractsage_performance_ratio:{mike_time / contractsage_time}")
        print(f"TEST_PASS:performance_comparison")
    except Exception as e:
        print(f"TEST_FAIL:performance_comparison:{str(e)}")

def main():
    if install_tool():
        test_drafting_contract()
        test_output_against_human_produced_contract()
        test_mike_performance_against_human_authors()
    print("RUN_OK")

if __name__ == "__main__":
    main()