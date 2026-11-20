#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, threading, queue, os, math

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} exception:{e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip install {pkg} exit {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install {pkg} exception:{e}")
        return False

def git_clone(repo, dest):
    try:
        res = subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:git clone {repo} exit {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {repo} exception:{e}")
        return False

def pip_editable(path):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip install -e {path} exit {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install -e {path} exception:{e}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{duration:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False

def run_sample_index_and_query():
    try:
        import hippomaps
    except Exception as e:
        print_marker(f"TEST_FAIL:import_hippomaps:{e}")
        return

    # synthetic OSM data: a list of dicts mimicking nodes
    sample_data = [
        {"type":"node","id":1,"lat":40.7128,"lon":-74.0060,"tags":{"amenity":"cafe","name":"Cafe A"}},
        {"type":"node","id":2,"lat":40.7130,"lon":-74.0055,"tags":{"amenity":"cafe","name":"Cafe B"}},
        {"type":"node","id":3,"lat":40.7140,"lon":-74.0100,"tags":{"amenity":"restaurant","name":"Resto C"}}
    ]

    # indexing
    start_idx = time.time()
    try:
        index = hippomaps.Index()
        for feat in sample_data:
            index.add_feature(feat)
        index.build()
        idx_time = time.time() - start_idx
        print_marker(f"BENCHMARK:index_time_s:{idx_time:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:indexing:{e}")
        return

    # query
    query_point = (40.7129, -74.0062)
    start_q = time.time()
    try:
        results = index.nearest(query_point, tags={"amenity":"cafe"}, limit=2)
        q_time = (time.time() - start_q) * 1000  # ms
        print_marker(f"BENCHMARK:query_latency_ms:{q_time:.2f}")
        if not results:
            raise ValueError("no results")
        print_marker("TEST_PASS:query_execution")
    except Exception as e:
        print_marker(f"TEST_FAIL:query_execution:{e}")

def compare_with_nominatim():
    try:
        import requests
    except Exception:
        if not pip_install('requests'):
            print_marker("TEST_SKIP:nominatim_compare:requests not available")
            return
    try:
        import hippomaps
        index = hippomaps.Index()
        # minimal data as before
        index.add_feature({"type":"node","id":1,"lat":40.7128,"lon":-74.0060,"tags":{"amenity":"cafe","name":"Cafe A"}})
        index.build()
        ours = index.nearest((40.7129,-74.0062), tags={"amenity":"cafe"}, limit=1)[0]['name']
        # Nominatim public endpoint (no key)
        resp = requests.get('https://nominatim.openstreetmap.org/reverse',
                            params={'format':'json','lat':40.7129,'lon':-74.0062,'zoom':18,'addressdetails':1},
                            headers={'User-Agent':'hippomaps-test'})
        data = resp.json()
        theirs = data.get('name') or data.get('display_name','')
        match = ours.lower() in theirs.lower()
        if match:
            print_marker("TEST_PASS:nominatim_consistency")
        else:
            print_marker(f"TEST_FAIL:nominatim_consistency:ours={ours} theirs={theirs}")
    except Exception as e:
        print_marker(f"TEST_FAIL:nominatim_compare:{e}")

def throughput_test():
    try:
        import hippomaps, concurrent.futures
    except Exception as e:
        print_marker(f"TEST_FAIL:throughput_import:{e}")
        return

    # reuse index from previous test if possible
    index = hippomaps.Index()
    for i in range(50):
        index.add_feature({"type":"node","id":i,"lat":40.7128+i*0.0001,"lon":-74.0060+i*0.0001,
                           "tags":{"amenity":"cafe","name":f"Cafe{i}"}})
    index.build()

    query = (40.7129, -74.0062)
    def worker():
        try:
            index.nearest(query, tags={"amenity":"cafe"}, limit=1)
            return True
        except:
            return False

    start = time.time()
    successes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(100)]
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                successes += 1
    duration = time.time() - start
    rps = 100 / duration if duration>0 else 0
    print_marker(f"BENCHMARK:throughput_rps:{rps:.2f}")
    print_marker(f"BENCHMARK:throughput_success_ratio:{successes/100:.2f}")

def determinism_test():
    try:
        import hippomaps
    except Exception as e:
        print_marker(f"TEST_FAIL:determinism_import:{e}")
        return
    index = hippomaps.Index()
    for i in range(20):
        index.add_feature({"type":"node","id":i,"lat":40.71+i*0.001,"lon":-74.00+i*0.001,
                           "tags":{"amenity":"cafe","name":f"Cafe{i}"}})
    index.build()
    q = (40.715, -74.005)
    first = index.nearest(q, tags={"amenity":"cafe"}, limit=5)
    second = index.nearest(q, tags={"amenity":"cafe"}, limit=5)
    if first == second:
        print_marker("TEST_PASS:determinism")
    else:
        print_marker(f"TEST_FAIL:determinism:results differ")

def baseline_compare():
    # baseline: use Nominatim reverse query latency as reference
    try:
        import requests
    except Exception:
        if not pip_install('requests'):
            print_marker("TEST_SKIP:baseline_compare:requests not available")
            return
    start = time.time()
    try:
        requests.get('https://nominatim.openstreetmap.org/reverse',
                     params={'format':'json','lat':40.7129,'lon':-74.0062,'zoom':18,'addressdetails':1},
                     headers={'User-Agent':'hippomaps-test'}).json()
        baseline = (time.time() - start) * 1000  # ms
    except Exception:
        baseline = None
    # our query latency measured earlier stored in env var if possible
    # For demonstration, assume last measured query latency is in a file
    try:
        with open('/tmp/last_query_latency.txt','r') as f:
            our = float(f.read().strip())
    except:
        our = None
    if baseline and our:
        ratio = our / baseline
        print_marker(f"BENCHMARK:vs_nominatim_query_latency_ratio:{ratio:.3f}")

def main():
    # 1. install apk packages
    install_apk('git')
    # 2. pip install hippomaps
    if not pip_install('hippomaps'):
        # fallback to git clone
        repo = 'https://github.com/hippomaps/hippomaps.git'
        dest = '/tmp/hippomaps_src'
        if git_clone(repo, dest):
            pip_editable(dest)

    # measure import
    if measure_import('hippomaps'):
        print_marker("TEST_PASS:import_hippomaps")
    else:
        print_marker("TEST_FAIL:import_hippomaps")

    # run functional tests
    run_sample_index_and_query()
    compare_with_nominatim()
    throughput_test()
    determinism_test()

    # write last query latency for baseline compare (extract from previous output if possible)
    # For simplicity we re-run a query and store its latency
    try:
        import hippomaps
        idx = hippomaps.Index()
        idx.add_feature({"type":"node","id":1,"lat":40.7128,"lon":-74.0060,"tags":{"amenity":"cafe","name":"Cafe A"}})
        idx.build()
        start = time.time()
        idx.nearest((40.7129,-74.0062), tags={"amenity":"cafe"}, limit=1)
        latency = (time.time() - start) * 1000
        with open('/tmp/last_query_latency.txt','w') as f:
            f.write(f"{latency:.3f}")
        print_marker(f"BENCHMARK:sample_query_latency_ms:{latency:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:sample_query_latency:{e}")

    baseline_compare()

    # ensure at least three benchmark lines (we already emitted many)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()