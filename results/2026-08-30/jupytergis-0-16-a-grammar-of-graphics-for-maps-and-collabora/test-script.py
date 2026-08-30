import subprocess, sys, os, time, tracemalloc, json, tempfile, shutil, pathlib, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

def install_system_packages():
    pkgs = ["git", "python3-dev", "build-base"]
    for pkg in pkgs:
        res = run_cmd(["apk", "add", "--no-cache", pkg])
        if res is None or res.returncode != 0:
            print_marker(f"INSTALL_FAIL:{pkg} - {res.stderr.strip() if res else 'exception'}")
        else:
            print_marker("INSTALL_OK")

def pip_install_package():
    start = time.time()
    try:
        # try direct pip install
        res = run_cmd([sys.executable, "-m", "pip", "install", "jupytergis"], env=os.environ)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker("INSTALL_OK")
    except Exception as e:
        # fallback to git clone + editable install
        try:
            tmpdir = tempfile.mkdtemp()
            clone = run_cmd(["git", "clone", "https://github.com/jupyter-widgets/jupytergis", tmpdir])
            if clone.returncode != 0:
                raise RuntimeError(clone.stderr.strip())
            res2 = run_cmd([sys.executable, "-m", "pip", "install", "-e", "."], cwd=tmpdir)
            if res2.returncode != 0:
                raise RuntimeError(res2.stderr.strip())
            print_marker("INSTALL_OK")
        except Exception as e2:
            print_marker(f"INSTALL_FAIL:{e2}")
            return None
    finally:
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")

def measure_import():
    start = time.time()
    tracemalloc.start()
    try:
        import jupytergis
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        print_marker("TEST_PASS:import_jupytergis")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_jupytergis:{e}")
        return False

def minimal_plot_test():
    try:
        import json, ipywidgets
        from jupytergis import Map
        # create tiny GeoJSON
        geo = {
            "type": "FeatureCollection",
            "features": [{
                "type":"Feature",
                "geometry":{"type":"Point","coordinates":[0,0]},
                "properties":{}
            }]
        }
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".geojson")
        json.dump(geo, open(tmp.name, "w"))
        start = time.time()
        m = Map(center=[0,0], zoom=2)
        m.add_geojson(tmp.name)
        # In headless env we can't render, just ensure no exception
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:minimal_plot_ms:{elapsed:.2f}")
        print_marker("TEST_PASS:minimal_plot")
        os.unlink(tmp.name)
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:minimal_plot:{e}")
        return False

def collaborative_test():
    # Simplified: just import and instantiate collaborative components
    try:
        from jupytergis import CollaborativeMap
        start = time.time()
        cm = CollaborativeMap(center=[0,0], zoom=2)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:collab_init_ms:{elapsed:.2f}")
        print_marker("TEST_PASS:collaborative_init")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:collaborative_init:{e}")
        return False

def load_large_geojson_test():
    try:
        import json, random
        from jupytergis import Map
        # generate 50k random points
        features = []
        for _ in range(50000):
            lon = random.uniform(-180, 180)
            lat = random.uniform(-90, 90)
            features.append({
                "type":"Feature",
                "geometry":{"type":"Point","coordinates":[lon, lat]},
                "properties":{}
            })
        geo = {"type":"FeatureCollection","features":features}
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".geojson")
        json.dump(geo, open(tmp.name, "w"))
        m = Map(center=[0,0], zoom=2)
        start = time.time()
        m.add_geojson(tmp.name)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:load_50k_geojson_ms:{elapsed:.2f}")
        print_marker("TEST_PASS:load_50k_geojson")
        os.unlink(tmp.name)
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:load_50k_geojson:{e}")
        return False

def baseline_comparison():
    # compare import time against folium (similar tool)
    try:
        import folium
        start = time.time()
        import jupytergis
        j_elapsed = (time.time() - start) * 1000
        start2 = time.time()
        import folium
        f_elapsed = (time.time() - start2) * 1000
        ratio = j_elapsed / f_elapsed if f_elapsed else 0
        print_marker(f"BENCHMARK:vs_folium_import_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"BENCHMARK:vs_folium_import_ratio:0.0")

def main():
    install_system_packages()
    pip_install_package()
    measure_import()
    minimal_plot_test()
    collaborative_test()
    load_large_geojson_test()
    baseline_comparison()
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()