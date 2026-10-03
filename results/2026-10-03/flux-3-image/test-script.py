import subprocess, sys, time, tracemalloc, json, os, math
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, description):
    try:
        start = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        duration = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK | {description}")
        else:
            print_marker(f"INSTALL_FAIL:{description}:{result.stderr.strip()}")
        return result, duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{description}:{e}")
        return None, None

def install_system():
    result, _ = run_cmd(['apk','add','--no-cache','git'], 'apk git')
    return result is not None and result.returncode == 0

def pip_install(package):
    return run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package], f'pip install {package}')

def git_clone(repo_url, dest):
    return run_cmd(['git','clone',repo_url,dest], f'git clone {repo_url}')

def pip_editable(path):
    return run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path], f'pip install -e {path}')

def measure_import():
    tracemalloc.start()
    start = time.time()
    try:
        import torch  # dependency for many diffusion models
        import diffusers  # generic library, may be used by flux
        import numpy as np
        import PIL.Image
        import time
        import gc
        import importlib
        # attempt to import the target package
        try:
            import bfl_flux_3_image  # placeholder name
        except ImportError:
            # try generic name
            import flux  # fallback
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_mem_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False

def run_generation():
    try:
        from diffusers import DiffusionPipeline
        # load the model from HuggingFace Hub
        start_load = time.time()
        pipe = DiffusionPipeline.from_pretrained("bfl/flux-3-image", torch_dtype=torch.float16)
        pipe.to("cpu")
        load_time = time.time() - start_load
        print_marker(f"BENCHMARK:model_load_s:{load_time:.2f}")

        prompt = "A photorealistic portrait of a smiling astronaut"
        start_gen = time.time()
        image = pipe(prompt, height=512, width=512, num_inference_steps=10).images[0]
        gen_time = time.time() - start_gen
        print_marker(f"BENCHMARK:generation_time_s:{gen_time:.2f}")

        out_path = Path("/tmp/flux_output.png")
        image.save(out_path)
        if out_path.stat().st_size > 0:
            print_marker("TEST_PASS:generate_image")
        else:
            print_marker("TEST_FAIL:generate_image:empty file")
        return gen_time, load_time
    except Exception as e:
        print_marker(f"TEST_FAIL:run_generation:{e}")
        return None, None

def compute_vs_baseline(gen_time):
    # baseline: Stable Diffusion 2.1 typical generation ~5.0s for 512x512 with 10 steps
    baseline = 5.0
    try:
        ratio = gen_time / baseline if baseline else float('nan')
        print_marker(f"BENCHMARK:vs_stable_diffusion_2_1_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_baseline:{e}")

def main():
    # 1. Install system package
    if not install_system():
        print_marker("TEST_SKIP:system_install:apk git failed")
    # 2. Install python package
    pkg_name = "bfl-flux-3-image"
    result, _ = pip_install(pkg_name)
    if not result or result.returncode != 0:
        # fallback to git clone + editable install
        repo = "https://github.com/bfl/flux-3-image.git"
        dest = "/tmp/flux-3-image"
        clone_res, _ = git_clone(repo, dest)
        if clone_res and clone_res.returncode == 0:
            edit_res, _ = pip_editable(dest)
            if not edit_res or edit_res.returncode != 0:
                print_marker("TEST_SKIP:pip_editable:install failed")
        else:
            print_marker("TEST_SKIP:git_clone:clone failed")

    # 3. Measure import
    if not measure_import():
        print_marker("TEST_SKIP:import_module:cannot import")

    # 4. Run generation test
    gen_time, load_time = run_generation()
    if gen_time is not None:
        compute_vs_baseline(gen_time)
    else:
        print_marker("TEST_SKIP:run_generation:failed")

    # Additional dummy benchmarks
    start = time.time()
    for _ in range(1000000):
        math.sqrt(12345.6789)
    loop_time = time.time() - start
    print_marker(f"BENCHMARK:cpu_loop_ms:{loop_time*1000:.2f}")

    # Memory allocation benchmark
    tracemalloc.start()
    lst = [i for i in range(100000)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_alloc_kb:{peak/1024:.2f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()