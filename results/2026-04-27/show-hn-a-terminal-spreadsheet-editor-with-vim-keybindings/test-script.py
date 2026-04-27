import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery
import os

def install_cell():
    try:
        # Install git
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        
        # Try pip install first
        try:
            subprocess.run(['pip', 'install', 'cell'], check=True)
        except subprocess.CalledProcessError:
            # Fallback to git clone and pip install -e
            subprocess.run(['git', 'clone', 'https://github.com/garritfra/cell.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './cell'], cwd='./cell', check=True)
        
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_load_time():
    try:
        import cell
        
        start_time = time.time()
        sheet = cell.Sheet()
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"BENCHMARK:load_time_ms:{load_time}")
        
        print(f"TEST_PASS:load_time")
    except Exception as e:
        print(f"TEST_FAIL:load_time:{str(e)}")
    
    # Compare with Vim
    try:
        # Create a temporary file
        with open("temp.txt", "w") as f:
            pass
        
        # Measure time to open file in Vim
        start_time = time.time()
        subprocess.run(['vim', 'temp.txt'], check=True)
        end_time = time.time()
        
        vim_time = (end_time - start_time) * 1000  # Convert to ms
        ratio = load_time / vim_time
        
        print(f"BENCHMARK:vs_vim_load_time_ratio:{ratio}")
    except Exception as e:
        print(f"BENCHMARK:vs_vim_load_time_ratio:Failed to measure")

def test_query_latency():
    try:
        import cell
        
        sheet = cell.Sheet()
        sheet.append([1, 2, 3])
        
        start_time = time.time()
        sheet[0][0]  # Simple query
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"BENCHMARK:query_latency_ms:{query_time}")
        
        print(f"TEST_PASS:query_latency")
    except Exception as e:
        print(f"TEST_FAIL:query_latency:{str(e)}")

def test_vim_keybinding_response_time():
    try:
        import cell
        
        sheet = cell.Sheet()
        
        # Measure time to handle key press
        start_time = time.time()
        sheet.handle_key_press('j')  # Vim keybinding for moving down
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"BENCHMARK:keybind_response_time_ms:{response_time}")
        
        print(f"TEST_PASS:vim_keybinding")
    except Exception as e:
        print(f"TEST_FAIL:vim_keybinding:{str(e)}")

def test_memory_usage():
    try:
        import cell
        
        tracemalloc.start()
        sheet = cell.Sheet()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        
        print(f"TEST_PASS:memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

def test_import_time():
    try:
        start_time = time.time()
        import cell
        end_time = time.time()
        
        import_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"BENCHMARK:import_time_ms:{import_time}")
        
        print(f"TEST_PASS:import_time")
    except Exception as e:
        print(f"TEST_FAIL:import_time:{str(e)}")

def main():
    install_cell()
    test_load_time()
    test_query_latency()
    test_vim_keybinding_response_time()
    test_memory_usage()
    test_import_time()
    
    print("RUN_OK")

if __name__ == "__main__":
    main()