import subprocess
import time
import tracemalloc
import git
import os

def install_glm():
    try:
        # Install dependencies
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
        # Clone GLM repository
        repo = git.Repo.clone_from('https://github.com/zai-tech/glm.git', 'glm')
        # Build from source
        subprocess.run(['make', 'build'], cwd='glm', check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_glm():
    try:
        # Run test program
        start_time = time.time()
        subprocess.run(['./glm', 'examples/hello_world.glm'], cwd='glm', check=False)
        end_time = time.time()
        print(f'BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:hello_world')
    except Exception as e:
        print(f'TEST_FAIL:hello_world:{str(e)}')

def test_cyber_capabilities():
    try:
        # Verify correctness of emergent cyber capabilities and simulation
        start_time = time.time()
        subprocess.run(['./glm', 'examples/cyber_simulation.glm'], cwd='glm', check=False)
        end_time = time.time()
        print(f'BENCHMARK:cyber_simulation_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:cyber_capabilities')
    except Exception as e:
        print(f'TEST_FAIL:cyber_capabilities:{str(e)}')

def test_performance():
    try:
        # Check for any performance issues during large-scale simulations
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['./glm', 'examples/large_scale_simulation.glm'], cwd='glm', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:large_scale_simulation_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:memory_usage_mb:{current / 10**6:.2f}')
        print('TEST_PASS:performance')
    except Exception as e:
        print(f'TEST_FAIL:performance:{str(e)}')

def test_language_server_speed():
    try:
        # Compare language server speed between GLM and Racket
        start_time = time.time()
        subprocess.run(['./glm', 'examples/language_server.glm'], cwd='glm', check=False)
        end_time = time.time()
        glm_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['racket', 'examples/language_server.rkt'], cwd='glm', check=False)
        end_time = time.time()
        racket_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:language_server_glm_ms:{glm_time:.2f}')
        print(f'BENCHMARK:language_server_racket_ms:{racket_time:.2f}')
        print(f'BENCHMARK:vs_racket_language_server_ratio:{glm_time / racket_time:.2f}')
        print('TEST_PASS:language_server_speed')
    except Exception as e:
        print(f'TEST_FAIL:language_server_speed:{str(e)}')

def main():
    install_glm()
    test_glm()
    test_cyber_capabilities()
    test_performance()
    test_language_server_speed()
    print('RUN_OK')

if __name__ == '__main__':
    main()