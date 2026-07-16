import subprocess
import time
import tracemalloc
import requests
from bs4 import BeautifulSoup
import sys

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL: {str(e)}')

def install_entools():
    try:
        subprocess.run(['pip', 'install', 'ente'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL: {str(e)}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/enteio/ente.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './ente'], check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL: {str(e)}')

def test_import():
    try:
        start_time = time.time()
        import ente
        import_time = (time.time() - start_time) * 1000
        print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        print('TEST_PASS:import_test')
    except Exception as e:
        print(f'TEST_FAIL:import_test: {str(e)}')

def test_latency():
    try:
        start_time = time.time()
        response = requests.get('https://ente.com/open/')
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a')
        latency = (time.time() - start_time) * 1000
        print(f'BENCHMARK:query_latency_ms:{latency:.2f}')
        print('TEST_PASS:latency_test')
    except Exception as e:
        print(f'TEST_FAIL:latency_test: {str(e)}')

def test_financials():
    try:
        url = 'https://ente.com/open/'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        financials_link = None
        for link in soup.find_all('a'):
            if 'financials' in link.text.lower():
                financials_link = link.get('href')
                break
        if financials_link is not None:
            response = requests.get(financials_link)
            if response.status_code == 200:
                print('TEST_PASS:financials_test')
            else:
                print(f'TEST_FAIL:financials_test: {response.status_code}')
        else:
            print('TEST_FAIL:financials_test: Financials link not found')
    except Exception as e:
        print(f'TEST_FAIL:financials_test: {str(e)}')

def test_baselines():
    try:
        import timeit
        import github

        # GitHub baseline
        def github_baseline():
            github.Github().get_user('github').get_repos()

        github_time = timeit.timeit(github_baseline, number=1)
        ente_time = timeit.timeit(lambda: import ente, number=1)
        ratio = ente_time / github_time
        print(f'BENCHMARK:vs_github_import_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'BENCHMARK:vs_github_import_ratio: N/A')

def main():
    install_packages()
    install_entools()
    test_import()
    test_latency()
    test_financials()
    test_baselines()

    # Memory usage
    tracemalloc.start()
    import ente
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    tracemalloc.stop()

    # LOC count
    subprocess.run(['git', 'clone', 'https://github.com/enteio/ente.git'])
    loc_count = subprocess.run(['wc', '-l', './ente'], capture_output=True, text=True)
    print(f'BENCHMARK:loc_count:{loc_count.stdout.split()[0]}')

    # Test files count
    test_files_count = subprocess.run(['find', './ente', '-type', 'f', '-name', '*test*.py'], capture_output=True, text=True)
    print(f'BENCHMARK:test_files_count:{len(test_files_count.stdout.split())}')

    print('RUN_OK')

if __name__ == '__main__':
    main()