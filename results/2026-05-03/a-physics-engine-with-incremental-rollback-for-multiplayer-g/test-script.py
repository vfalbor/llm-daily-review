import subprocess
import time
import tracemalloc
import os
import sys

def install_package(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def clone_repository(repo_url):
    try:
        subprocess.run(['git', 'clone', repo_url], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def count_source_files(repo_path):
    try:
        src_files = 0
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.c', '.cpp', '.java', '.py', '.js', '.go')):
                    src_files += 1
        print(f'BENCHMARK:loc_count:{src_files}')
    except Exception as e:
        print(f'TEST_FAIL:count_source_files:{str(e)}')

def compare_performance(repo_path):
    try:
        # Run a Python example
        start_time = time.time()
        subprocess.run(['python', os.path.join(repo_path, 'example.py')], check=True)
        end_time = time.time()
        print(f'BENCHMARK:example_run_time_ms:{(end_time - start_time) * 1000}')

        # Compare performance with a similar tool (Phaser)
        phaser_repo_url = 'https://github.com/photonstorm/phaser.git'
        clone_repository(phaser_repo_url)
        phaser_repo_path = 'phaser'
        phaser_start_time = time.time()
        subprocess.run(['python', os.path.join(phaser_repo_path, 'example.py')], check=True)
        phaser_end_time = time.time()
        print(f'BENCHMARK:vs_phaser_ratio:{(end_time - start_time) / (phaser_end_time - phaser_start_time)}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{str(e)}')

def test_complex_physics_simulations(repo_path):
    try:
        # Run a test for complex physics simulations
        start_time = time.time()
        subprocess.run(['python', os.path.join(repo_path, 'complex_simulation.py')], check=True)
        end_time = time.time()
        print(f'BENCHMARK:complex_simulation_time_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:test_complex_physics_simulations')
    except Exception as e:
        print(f'TEST_FAIL:test_complex_physics_simulations:{str(e)}')

def test_multplayer_performance(repo_path):
    try:
        # Run a test for multiplayer performance
        start_time = time.time()
        subprocess.run(['python', os.path.join(repo_path, 'multplayer_test.py')], check=True)
        end_time = time.time()
        print(f'BENCHMARK:multplayer_test_time_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:test_multplayer_performance')
    except Exception as e:
        print(f'TEST_FAIL:test_multplayer_performance:{str(e)}')

def main():
    install_package('git')

    repo_url = 'https://github.com/easelgames/rollback-physics.git'
    clone_repository(repo_url)
    repo_path = 'rollback-physics'

    count_source_files(repo_path)

    compare_performance(repo_path)

    test_complex_physics_simulations(repo_path)

    test_multplayer_performance(repo_path)

    print('RUN_OK')

if __name__ == '__main__':
    main()