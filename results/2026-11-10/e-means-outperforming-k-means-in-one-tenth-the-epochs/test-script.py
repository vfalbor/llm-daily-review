import subprocess, sys, time, tracemalloc, json, os, math, traceback
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    start = time.time()
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker(f"INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    duration = time.time() - start
    print_marker(f"BENCHMARK:apk_{pkg}_install_time_s:{duration:.3f}")

def pip_install(package):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    duration = time.time() - start
    print_marker(f"BENCHMARK:pip_{package}_install_time_s:{duration:.3f}")

def git_clone(repo, dest):
    start = time.time()
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    duration = time.time() - start
    print_marker(f"BENCHMARK:git_clone_time_s:{duration:.3f}")

def pip_install_editable(path):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    duration = time.time() - start
    print_marker(f"BENCHMARK:pip_editable_install_time_s:{duration:.3f}")

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        print_marker(f"TEST_PASS:import_{module_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
    duration = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:import_{module_name}_time_ms:{duration:.2f}")

def run_clustering_test():
    test_name = "clustering_iris"
    try:
        import numpy as np
        from sklearn import datasets
        from sklearn.cluster import KMeans
        import e_means

        iris = datasets.load_iris()
        X = iris.data

        # e-means clustering
        em = e_means.EMeans(n_clusters=3, random_state=42, max_iter=10)
        start = time.time()
        em_labels = em.fit_predict(X)
        em_time = (time.time() - start) * 1000

        # scikit-learn k-means
        km = KMeans(n_clusters=3, random_state=42, n_init=10, max_iter=300)
        start = time.time()
        km_labels = km.fit_predict(X)
        km_time = (time.time() - start) * 1000

        # verify cluster count
        if len(set(em_labels)) != 3:
            raise AssertionError(f"Expected 3 clusters, got {len(set(em_labels))}")

        print_marker(f"TEST_PASS:{test_name}")
        print_marker(f"BENCHMARK:e_means_clustering_time_ms:{em_time:.2f}")
        print_marker(f"BENCHMARK:sklearn_kmeans_time_ms:{km_time:.2f}")
        ratio = em_time / km_time if km_time else float('inf')
        print_marker(f"BENCHMARK:vs_sklearn_kmeans_time_ratio:{ratio:.3f}")

    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")
        traceback.print_exc()

def run_reproducibility_test():
    test_name = "reproducibility_seed"
    try:
        import numpy as np
        from sklearn import datasets
        import e_means

        iris = datasets.load_iris()
        X = iris.data

        em1 = e_means.EMeans(n_clusters=3, random_state=123, max_iter=10)
        labels1 = em1.fit_predict(X)

        em2 = e_means.EMeans(n_clusters=3, random_state=123, max_iter=10)
        labels2 = em2.fit_predict(X)

        if not np.array_equal(labels1, labels2):
            raise AssertionError("Labels differ across runs with same seed")
        print_marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")

def run_centroid_dim_test():
    test_name = "centroid_dimensionality"
    try:
        from sklearn import datasets
        import e_means

        iris = datasets.load_iris()
        X = iris.data

        em = e_means.EMeans(n_clusters=3, random_state=0, max_iter=5)
        em.fit(X)
        centroids = em.cluster_centers_
        if centroids.shape != (3, X.shape[1]):
            raise AssertionError(f"Centroids shape {centroids.shape} unexpected")
        print_marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")

def main():
    # 1. Install required APK packages
    install_apk('git')

    # 2. Install e-means via pip, fallback to source
    try:
        pip_install('e-means')
        import importlib
        importlib.import_module('e_means')
    except Exception:
        # fallback
        repo_url = "https://github.com/e-means/e-means.git"
        src_dir = "/tmp/e_means_src"
        if Path(src_dir).exists():
            subprocess.run(['rm', '-rf', src_dir])
        git_clone(repo_url, src_dir)
        pip_install_editable(src_dir)

    # 3. Measure imports
    measure_import('e_means')
    measure_import('sklearn')

    # 4. Run tests
    run_clustering_test()
    run_reproducibility_test()
    run_centroid_dim_test()

    # 5. Additional benchmarks: memory usage during import
    tracemalloc.start()
    import importlib
    start = time.time()
    importlib.reload(importlib.import_module('e_means'))
    mem = tracemalloc.get_traced_memory()[1] / 1024
    duration = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:e_means_reload_time_ms:{duration:.2f}")
    print_marker(f"BENCHMARK:e_means_memory_peak_kb:{mem:.0f}")
    tracemalloc.stop()

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()