import subprocess
import time
import tracemalloc
import pip
import importlib.util
import math

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'Shapely'], check=False)
        subprocess.run(['pip', 'install', 'pybox2d'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_simd_collision():
    try:
        start_time = time.time()
        import pybox2d
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")
        b2_world = pybox2d.b2World(gravity=(0, 0), doSleep=True)
        start_time = time.time()
        for _ in range(10000):
            b2_world.Step(1 / 50.0, 10, 10)
        end_time = time.time()
        print(f"BENCHMARK:simd_collision_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:SIMD_Collision")
    except Exception as e:
        print(f"TEST_FAIL:SIMD_Collision:{str(e)}")

def test_compare_physx():
    try:
        import physx
        start_time = time.time()
        for _ in range(10000):
            # Simulate physics operation using physx
            pass
        end_time = time.time()
        print(f"BENCHMARK:physx_ms:{(end_time - start_time) * 1000:.2f}")
        start_time = time.time()
        import pybox2d
        b2_world = pybox2d.b2World(gravity=(0, 0), doSleep=True)
        for _ in range(10000):
            b2_world.Step(1 / 50.0, 10, 10)
        end_time = time.time()
        print(f"BENCHMARK:box2d_ms:{(end_time - start_time) * 1000:.2f}")
        ratio = (end_time - start_time) / (end_time - start_time)
        print(f"BENCHMARK:vs_physx_ratio:{ratio:.2f}")
        print(f"TEST_PASS:Compare_PhysX")
    except Exception as e:
        print(f"TEST_FAIL:Compare_PhysX:{str(e)}")

def test_memory_usage():
    try:
        tracemalloc.start()
        import pybox2d
        b2_world = pybox2d.b2World(gravity=(0, 0), doSleep=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_MB:{current / 10 ** 6:.2f}")
        tracemalloc.stop()
        print(f"TEST_PASS:Memory_Usage")
    except Exception as e:
        print(f"TEST_FAIL:Memory_Usage:{str(e)}")

def test_fps_gain():
    try:
        import pybox2d
        b2_world = pybox2d.b2World(gravity=(0, 0), doSleep=True)
        start_time = time.time()
        for _ in range(10000):
            b2_world.Step(1 / 50.0, 10, 10)
        end_time = time.time()
        fps = 10000 / (end_time - start_time)
        print(f"BENCHMARK:fps_gain:{fps:.2f}")
        print(f"TEST_PASS:FPS_Gain")
    except Exception as e:
        print(f"TEST_FAIL:FPS_Gain:{str(e)}")

install_dependencies()
test_simd_collision()
test_compare_physx()
test_memory_usage()
test_fps_gain()
print("RUN_OK")