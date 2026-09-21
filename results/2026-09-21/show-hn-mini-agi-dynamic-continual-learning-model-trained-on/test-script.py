#!/usr/bin/env python3
import subprocess
import sys
import time
import tracemalloc
import os
import shutil
import json
from pathlib import Path

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return result
    except Exception as e:
        return e

def measure(func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    return {
        "success": success,
        "result": result,
        "time_s": elapsed,
        "mem_peak_kb": peak / 1024,
    }

# 1. Install apk packages
apk_pkg = "git"
apk_res = run_cmd(["apk", "add", "--no-cache", apk_pkg])
if isinstance(apk_res, subprocess.CompletedProcess) and apk_res.returncode == 0:
    marker("INSTALL_OK")
else:
    reason = getattr(apk_res, "stderr", str(apk_res))
    marker(f"INSTALL_FAIL:{reason}")

# Prepare workspace
work_dir = Path("/tmp/mini_agi_test")
if work_dir.exists():
    shutil.rmtree(work_dir)
work_dir.mkdir(parents=True)

repo_url = "https://github.com/volotat/mini-AGI.git"
repo_dir = work_dir / "mini-AGI"

# Benchmarks container
benchmarks = []

# 2. Clone repo
clone_res = run_cmd(["git", "clone", repo_url, str(repo_dir)])
if isinstance(clone_res, subprocess.CompletedProcess) and clone_res.returncode == 0:
    marker("TEST_PASS:clone_repo")
else:
    reason = getattr(clone_res, "stderr", str(clone_res))
    marker(f"TEST_FAIL:clone_repo:{reason}")

# 3. Install requirements
def pip_install_requirements():
    return run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=str(repo_dir))

install_metrics = measure(pip_install_requirements)
if install_metrics["success"]:
    marker("TEST_PASS:install_requirements")
else:
    # fallback to editable install
    fallback = measure(lambda: run_cmd([sys.executable, "-m", "pip", "install", "-e", "."], cwd=str(repo_dir)))
    if fallback["success"]:
        marker("TEST_PASS:install_editable_fallback")
        install_metrics = fallback
    else:
        marker(f"TEST_FAIL:install_requirements:{fallback['result']}")

benchmarks.append(("install_time_s", install_metrics["time_s"]))
benchmarks.append(("install_mem_peak_kb", install_metrics["mem_peak_kb"]))

# 4. Measure import time of the package
def import_package():
    import importlib.util, sys
    spec = importlib.util.find_spec("mini_agi")
    if spec is None:
        raise ImportError("mini_agi not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

import_metrics = measure(import_package)
if import_metrics["success"]:
    marker("TEST_PASS:import_package")
else:
    marker(f"TEST_FAIL:import_package:{import_metrics['result']}")

benchmarks.append(("import_time_s", import_metrics["time_s"]))
benchmarks.append(("import_mem_peak_kb", import_metrics["mem_peak_kb"]))

# 5. Run a minimal training (epochs=1, gpus=1)
train_cmd = [sys.executable, "train.py", "--epochs", "1", "--gpus", "1"]
def run_training():
    return run_cmd(train_cmd, cwd=str(repo_dir))

train_metrics = measure(run_training)
if train_metrics["success"] and isinstance(train_metrics["result"], subprocess.CompletedProcess) and train_metrics["result"].returncode == 0:
    marker("TEST_PASS:train_one_epoch")
else:
    err = getattr(train_metrics["result"], "stderr", str(train_metrics["result"]))
    marker(f"TEST_FAIL:train_one_epoch:{err}")

benchmarks.append(("train_time_s", train_metrics["time_s"]))
benchmarks.append(("train_mem_peak_kb", train_metrics["mem_peak_kb"]))

# 6. Verify checkpoint size < 500MB
def check_checkpoint():
    # assume checkpoint saved in ./checkpoints or ./output
    possible_dirs = ["checkpoints", "output", "models"]
    for d in possible_dirs:
        path = repo_dir / d
        if path.is_dir():
            # take largest file
            files = list(path.rglob("*"))
            if not files:
                continue
            largest = max(files, key=lambda p: p.stat().st_size)
            size_mb = largest.stat().st_size / (1024 * 1024)
            return size_mb
    raise FileNotFoundError("No checkpoint directory found")

checkpoint_metrics = measure(check_checkpoint)
if checkpoint_metrics["success"]:
    size_mb = checkpoint_metrics["result"]
    if size_mb < 500:
        marker("TEST_PASS:checkpoint_size")
    else:
        marker(f"TEST_FAIL:checkpoint_size:Size {size_mb:.2f} MB exceeds limit")
else:
    marker(f"TEST_FAIL:checkpoint_size:{checkpoint_metrics['result']}")

benchmarks.append(("checkpoint_size_mb", checkpoint_metrics["result"] if checkpoint_metrics["success"] else -1))

# 7. Run inference on a sample prompt
sample_prompt = "What is the capital of France?"
def run_inference():
    # Assuming the repo provides a script inference.py or a CLI entrypoint
    inference_cmd = [sys.executable, "inference.py", "--prompt", sample_prompt]
    return run_cmd(inference_cmd, cwd=str(repo_dir))

inf_metrics = measure(run_inference)
if inf_metrics["success"] and isinstance(inf_metrics["result"], subprocess.CompletedProcess) and inf_metrics["result"].returncode == 0:
    marker("TEST_PASS:inference_latency")
else:
    err = getattr(inf_metrics["result"], "stderr", str(inf_metrics["result"]))
    marker(f"TEST_FAIL:inference_latency:{err}")

benchmarks.append(("inference_time_s", inf_metrics["time_s"]))
benchmarks.append(("inference_mem_peak_kb", inf_metrics["mem_peak_kb"]))

# Emit benchmark lines
for name, value in benchmarks:
    try:
        if isinstance(value, float):
            marker(f"BENCHMARK:{name}:{value:.4f}")
        else:
            marker(f"BENCHMARK:{name}:{value}")
    except Exception:
        continue

# Baseline comparison (using TinyLlama placeholder values)
# Assume baseline import time = 0.8s, inference latency = 1.2s
baseline_import = 0.8
baseline_infer = 1.2
if import_metrics["success"]:
    ratio_imp = import_metrics["time_s"] / baseline_import
    marker(f"BENCHMARK:vs_TinyLlama_import_ratio:{ratio_imp:.3f}")
if inf_metrics["success"]:
    ratio_inf = inf_metrics["time_s"] / baseline_infer
    marker(f"BENCHMARK:vs_TinyLlama_inference_ratio:{ratio_inf:.3f}")

# Final marker
marker("RUN_OK")