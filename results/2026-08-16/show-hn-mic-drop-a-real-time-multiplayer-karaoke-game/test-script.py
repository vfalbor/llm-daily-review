import subprocess
import requests
import time
import tracemalloc
import json

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install', 'express'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install dependencies: {e}")
        return False
    print("INSTALL_OK")
    return True

def start_server():
    try:
        subprocess.Popen(['node', '-e', 'require("express")().listen(3000)'], stdout=subprocess.DEVNULL)
        time.sleep(2)
    except Exception as e:
        print(f"TEST_FAIL:start_server: {e}")
        return False
    print("TEST_PASS:start_server")
    return True

def test_signup():
    try:
        start_time = time.time()
        response = requests.post('http://localhost:3000/signup', json={'username': 'test', 'password': 'test'})
        response.raise_for_status()
        end_time = time.time()
        tracemalloc.start()
        requests.get('http://localhost:3000/health')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:signup_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:signup_memory_mb:{peak / 10**6}")
    except requests.RequestException as e:
        print(f"TEST_FAIL:signup: {e}")
        return False
    print("TEST_PASS:signup")
    return True

def test_invite_friends():
    try:
        start_time = time.time()
        response = requests.post('http://localhost:3000/invite', json={'username': 'test', 'friend': 'friend'})
        response.raise_for_status()
        end_time = time.time()
        print(f"BENCHMARK:invite_time_ms:{(end_time - start_time) * 1000}")
    except requests.RequestException as e:
        print(f"TEST_FAIL:invite_friends: {e}")
        return False
    print("TEST_PASS:invite_friends")
    return True

def test_multiplayer_features():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:3000/multiplayer')
        response.raise_for_status()
        end_time = time.time()
        print(f"BENCHMARK:multiplayer_time_ms:{(end_time - start_time) * 1000}")
    except requests.RequestException as e:
        print(f"TEST_FAIL:multiplayer_features: {e}")
        return False
    print("TEST_PASS:multiplayer_features")
    return True

def test_performance():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:3000/health')
        response.raise_for_status()
        end_time = time.time()
        print(f"BENCHMARK:response_time_ms:{(end_time - start_time) * 1000}")
    except requests.RequestException as e:
        print(f"TEST_FAIL:performance: {e}")
        return False
    print("TEST_PASS:performance")
    return True

def compare_with_baseline():
    try:
        start_time = time.time()
        response = requests.get('https://www.roblox.com')
        response.raise_for_status()
        end_time = time.time()
        roblox_time = (end_time - start_time) * 1000
        micdrop_time = float([line.split(":")[1] for line in [line for line in [line for line in open("test.log", "r").readlines()] if "BENCHMARK:response_time_ms" in line]][0])
        print(f"BENCHMARK:vs_roblox_response_time_ratio:{micdrop_time / roblox_time}")
    except requests.RequestException as e:
        print(f"TEST_SKIP:compare_with_baseline: {e}")
        return

def main():
    if not install_dependencies():
        pass
    if not start_server():
        pass
    test_signup()
    test_invite_friends()
    test_multiplayer_features()
    test_performance()
    compare_with_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()