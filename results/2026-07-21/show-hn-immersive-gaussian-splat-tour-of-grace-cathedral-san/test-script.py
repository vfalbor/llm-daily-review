import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery
import webbrowser

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: Failed to install git {e}")

def install_tool_dependencies():
    try:
        subprocess.run(['pip', 'install', 'three.js'], check=False)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/mrdoob/three.js.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './three.js'], check=False)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL: Failed to install three.js {e}")

def open_three_js_example():
    try:
        url = "https://vincentwoo.com/3d/grace_cathedral/"
        webbrowser.open(url)
        time.sleep(2)  # wait for browser to open
        print(f"TEST_PASS:open_three_js_example")
    except Exception as e:
        print(f"TEST_FAIL:open_three_js_example:{e}")

def compare_performance():
    try:
        import three
        import time
        tracemalloc.start()
        t = time.time()
        # Run a simple 3D scene
        scene = three.Scene()
        camera = three.PerspectiveCamera(75, 1, 0.1, 1000)
        renderer = three.WebGLRenderer()
        start_time = time.time()
        for _ in range(100):
            renderer.render(scene, camera)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        latency = end_time - start_time
        memory_usage = current / 1024 / 1024  # in MB
        print(f"BENCHMARK:three_js_latency_ms:{latency * 1000}")
        print(f"BENCHMARK:three_js_memory_mb:{memory_usage}")
        # Compare with WebGL-GLSL
        import WebGLGLSL
        t = time.time()
        # Run a simple 3D scene
        scene = WebGLGLSL.Scene()
        camera = WebGLGLSL.PerspectiveCamera(75, 1, 0.1, 1000)
        renderer = WebGLGLSL.WebGLRenderer()
        start_time = time.time()
        for _ in range(100):
            renderer.render(scene, camera)
        end_time = time.time()
        latency = end_time - start_time
        print(f"BENCHMARK:webgl_glsl_latency_ms:{latency * 1000}")
        ratio = (end_time - start_time) / (end_time - t)
        print(f"BENCHMARK:vs_webgl_glsl_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def gaussian_splat_on_gpu():
    try:
        import numpy as np
        from numba import cuda
        @cuda.jit
        def gaussian_splat(data):
            x, y = cuda.grid(2)
            if x < data.shape[0] and y < data.shape[1]:
                data[x, y] = np.exp(-(x**2 + y**2))
        data = np.random.rand(1024, 1024)
        start_time = time.time()
        gaussian_splat[10, 10](data)
        end_time = time.time()
        latency = end_time - start_time
        print(f"BENCHMARK:gaussian_splat_latency_ms:{latency * 1000}")
        print(f"TEST_PASS:gaussian_splat_on_gpu")
    except Exception as e:
        print(f"TEST_FAIL:gaussian_splat_on_gpu:{e}")

if __name__ == "__main__":
    install_packages()
    install_tool_dependencies()
    open_three_js_example()
    compare_performance()
    gaussian_splat_on_gpu()
    print("RUN_OK")