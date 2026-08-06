import subprocess
import time
import tracemalloc
import requests
import json

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    try:
        subprocess.run(['npm', 'install'], cwd='/app', check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def build_project():
    try:
        subprocess.run(['npm', 'run', 'build'], cwd='/app', check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_install_time():
    start_time = time.time()
    subprocess.run(['npm', 'install'], cwd='/app', check=False)
    end_time = time.time()
    install_time = end_time - start_time
    print(f'BENCHMARK:install_time_s:{install_time}')

def test_import_time():
    start_time = time.time()
    subprocess.run(['node', '-e', 'require("./app")'], cwd='/app', check=False)
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')

def test_response_time():
    start_server()
    time.sleep(2)
    start_time = time.time()
    response = requests.get('http://localhost:3000')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:hello_world_ms:{response_time}')

def test_coop_multiplayer():
    try:
        start_server()
        time.sleep(2)
        players = [requests.get(f'http://localhost:3000/player/{i}') for i in range(2, 5)]
        for player in players:
            if player.status_code != 200:
                print(f'TEST_FAIL:coop_multiplayer:Failed to create player {player.status_code}')
                return
        print('TEST_PASS:coop_multiplayer')
    except Exception as e:
        print(f'TEST_FAIL:coop_multiplayer:{str(e)}')

def test_custom_item():
    try:
        start_server()
        time.sleep(2)
        custom_item = {'name': 'custom_item', 'description': 'This is a custom item'}
        response = requests.post('http://localhost:3000/item', json=custom_item)
        if response.status_code != 201:
            print(f'TEST_FAIL:custom_item:Failed to create custom item {response.status_code}')
            return
        print('TEST_PASS:custom_item')
    except Exception as e:
        print(f'TEST_FAIL:custom_item:{str(e)}')

def test_cloud_saves():
    try:
        start_server()
        time.sleep(2)
        player_data = {'player_id': 1, 'game_state': {'city': 'New York'}}
        response = requests.post('http://localhost:3000/save', json=player_data)
        if response.status_code != 201:
            print(f'TEST_FAIL:cloud_saves:Failed to save game state {response.status_code}')
            return
        response = requests.get('http://localhost:3000/save/1')
        if response.status_code != 200:
            print(f'TEST_FAIL:cloud_saves:Failed to load game state {response.status_code}')
            return
        if response.json() != player_data:
            print(f'TEST_FAIL:cloud_saves:Loaded game state does not match saved state')
            return
        print('TEST_PASS:cloud_saves')
    except Exception as e:
        print(f'TEST_FAIL:cloud_saves:{str(e)}')

def start_server():
    subprocess.Popen(['npm', 'start'], cwd='/app')

def compare_baseline():
    # Compare against SimTower
    simtower_response_time = 100  # ms
    response_time = float([line.split(':')[1] for line in output if line.startswith('BENCHMARK:hello_world_ms')][0])
    ratio = response_time / simtower_response_time
    print(f'BENCHMARK:vs_simtower_response_time_ms:{ratio}')

def measure_memory_usage():
    tracemalloc.start()
    subprocess.run(['npm', 'start'], cwd='/app')
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}')

def measure_loc_count():
    loc_count = subprocess.run(['find', '/app', '-type', 'f', '-name', '*.js', '-exec', 'wc', '-l', '{}', ';'], stdout=subprocess.PIPE)
    loc_count = loc_count.stdout.decode('utf-8').strip().split('\n')[-1]
    print(f'BENCHMARK:loc_count:{int(loc_count)}')

def measure_test_files_count():
    test_files_count = subprocess.run(['find', '/app', '-type', 'f', '-name', '*.test.js'], stdout=subprocess.PIPE)
    test_files_count = len(test_files_count.stdout.decode('utf-8').strip().split('\n'))
    print(f'BENCHMARK:test_files_count:{test_files_count}')

install_dependencies()
build_project()
test_install_time()
test_import_time()
test_response_time()
test_coop_multiplayer()
test_custom_item()
test_cloud_saves()
compare_baseline()
measure_memory_usage()
measure_loc_count()
measure_test_files_count()
print('RUN_OK')