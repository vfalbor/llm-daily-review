import subprocess
import time
import tracemalloc
import os
import requests
from bs4 import BeautifulSoup
import re

def install_pkg(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def install_dependencies():
    try:
        install_pkg('git')
        subprocess.run(['git', 'clone', 'https://github.com/PetoiCamp/Petoi-Bittle.git'], check=True)
        subprocess.run(['pip', 'install', '-e', 'Petoi-Bittle'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def count_source_files():
    try:
        count = subprocess.run(['find', 'Petoi-Bittle', '-type', 'f'], capture_output=True, text=True).stdout.splitlines()
        print(f"BENCHMARK:source_files_count:{len(count)}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:count_source_files:{e}")

def count_languages():
    try:
        languages = set()
        for root, dirs, files in os.walk('Petoi-Bittle'):
            for file in files:
                if file.endswith('.py'):
                    languages.add('Python')
                elif file.endswith('.java'):
                    languages.add('Java')
                elif file.endswith('.js'):
                    languages.add('JavaScript')
        print(f"BENCHMARK:languages_count:{len(languages)}")
    except Exception as e:
        print(f"TEST_FAIL:count_languages:{e}")

def check_simulator():
    try:
        with open('Petoi-Bittle/index.html', 'r') as f:
            html = f.read()
            soup = BeautifulSoup(html, 'html.parser')
            simulator = soup.find('div', {'id': 'simulator'})
            if simulator:
                print("TEST_PASS:check_simulator")
            else:
                print("TEST_FAIL:check_simulator:Simulator not found")
    except Exception as e:
        print(f"TEST_FAIL:check_simulator:{e}")

def test_bittle_simulator():
    try:
        start_time = time.time()
        response = requests.get('https://bittlex-sim.petoi.com/')
        end_time = time.time()
        print(f"BENCHMARK:load_time_ms:{(end_time - start_time) * 1000}")
        soup = BeautifulSoup(response.text, 'html.parser')
        controls = soup.find('div', {'id': 'controls'})
        if controls:
            print("TEST_PASS:test_bittle_simulator")
        else:
            print("TEST_FAIL:test_bittle_simulator:Controls not found")
    except Exception as e:
        print(f"TEST_FAIL:test_bittle_simulator:{e}")

def compare_performance():
    try:
        # Compare performance with Robot Operating System (ROS)
        ros_response = requests.get('https://www.ros.org/')
        ros_load_time = (time.time() - start_time) * 1000
        bittle_load_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_ros_load_time_ratio:{bittle_load_time / ros_load_time}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def main():
    install_dependencies()
    count_source_files()
    count_languages()
    check_simulator()
    test_bittle_simulator()
    compare_performance()
    print("RUN_OK")

if __name__ == "__main__":
    main()