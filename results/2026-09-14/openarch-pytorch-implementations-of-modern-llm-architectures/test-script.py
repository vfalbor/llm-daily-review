import subprocess
import sys
import os
import time
import tracemalloc
import shutil
import json
import math

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

# 1. Install system packages
def install_system():
    pkgs = ["git"]
    for pkg in pkgs:
        res = run_cmd(["apk", "add", "--no-cache", pkg])
        if res and res.returncode == 0:
            marker("INSTALL_OK")
        else:
            reason = (res.stderr.strip() if res else "exception") or "unknown"
            marker(f"INSTALL_FAIL:{reason}")

# 2. Clone repo and install python deps
REPO_URL = "https://github.com/anuj0456/OpenArch.git"
REPO_DIR = "/tmp/OpenArch"

def clone_and_install():
    start = time.time()
    try:
        if os.path.isdir(REPO_DIR):
            shutil.rmtree(REPO_DIR)
        res = run_cmd(["git", "clone", REPO_URL, REPO_DIR])
        if res is None or res.returncode != 0:
            raise RuntimeError(f"git clone failed: {res.stderr if res else 'no result'}")
        # try pip install -r requirements.txt
        req_path = os.path.join(REPO_DIR, "requirements.txt")
        if os.path.isfile(req_path):
            res = run_cmd([sys.executable, "-m", "pip", "install", "-r", req_path])
            if res is None or res.returncode != 0:
                raise RuntimeError(f"pip install -r failed: {res.stderr if res else 'no result'}")
        # install package itself
        res = run_cmd([sys.executable, "-m", "pip", "install", "-e", REPO_DIR])
        if res is None or res.returncode != 0:
            raise RuntimeError(f"pip install -e . failed: {res.stderr if res else 'no result'}")
        marker("INSTALL_OK")
    except Exception as e:
        marker(f"INSTALL_FAIL:{str(e)}")
    finally:
        elapsed = time.time() - start
        marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")

# 3. Measure import time
def test_import():
    start = time.time()
    try:
        import OpenArch  # Assuming package name matches repo
        marker("TEST_PASS:import_module")
    except Exception as e:
        marker(f"TEST_FAIL:import_module:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")

# 4. Load a pretrained checkpoint and verify hidden shape
def test_load_checkpoint():
    name = "load_checkpoint"
    start = time.time()
    try:
        # Use provided loader if exists
        from OpenArch.models import gpt2  # placeholder import path
        model = gpt2.GPT2Model.from_pretrained("gpt2")
        dummy_input = torch.randn(1, 10, model.config.hidden_size)
        with torch.no_grad():
            outputs = model(dummy_input)
        hidden = outputs.last_hidden_state if hasattr(outputs, "last_hidden_state") else outputs[0]
        if hidden.shape[-1] == model.config.hidden_size:
            marker(f"TEST_PASS:{name}")
        else:
            raise AssertionError(f"Unexpected hidden size {hidden.shape}")
    except Exception as e:
        marker(f"TEST_FAIL:{name}:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:{name}_ms:{elapsed:.2f}")

# 5. Generate sequence with beam search and compare to baseline (simple ratio)
def test_generate():
    name = "generate_beam"
    start = time.time()
    try:
        import torch
        from OpenArch.models import gpt2
        model = gpt2.GPT2Model.from_pretrained("gpt2").eval()
        tokenizer = gpt2.GPT2Tokenizer.from_pretrained("gpt2")
        input_ids = tokenizer.encode("Hello", return_tensors="pt")
        # beam search placeholder using generate if available
        if hasattr(model, "generate"):
            output_ids = model.generate(input_ids, max_length=60, num_beams=5)
        else:
            # fallback simple forward pass
            with torch.no_grad():
                output = model(input_ids)
            output_ids = input_ids  # dummy
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        # baseline: just length check
        if len(generated.split()) >= 5:
            marker(f"TEST_PASS:{name}")
        else:
            raise AssertionError("Generated too short")
    except Exception as e:
        marker(f"TEST_FAIL:{name}:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:{name}_ms:{elapsed:.2f}")

# 6. Measure throughput (tokens/sec) on CPU (GPU not guaranteed)
def benchmark_throughput():
    name = "throughput"
    start = time.time()
    try:
        import torch
        from OpenArch.models import gpt2
        model = gpt2.GPT2Model.from_pretrained("gpt2").eval()
        tokenizer = gpt2.GPT2Tokenizer.from_pretrained("gpt2")
        input_ids = tokenizer.encode("The quick brown fox jumps over the lazy dog.", return_tensors="pt")
        total_tokens = 0
        dur = 0.0
        for _ in range(20):
            t0 = time.time()
            with torch.no_grad():
                _ = model(input_ids)
            dur += time.time() - t0
            total_tokens += input_ids.numel()
        tokens_per_sec = total_tokens / dur if dur > 0 else 0
        marker(f"BENCHMARK:{name}_tps:{tokens_per_sec:.2f}")
    except Exception as e:
        marker(f"TEST_FAIL:{name}:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:{name}_ms:{elapsed:.2f}")

# 7. Run included unit tests if any
def run_unit_tests():
    name = "unit_tests"
    start = time.time()
    try:
        test_dir = os.path.join(REPO_DIR, "tests")
        if os.path.isdir(test_dir):
            res = run_cmd([sys.executable, "-m", "pytest", test_dir, "-q"])
            if res and res.returncode == 0:
                marker(f"TEST_PASS:{name}")
            else:
                raise RuntimeError(res.stderr.strip() if res else "pytest failed")
        else:
            raise FileNotFoundError("No tests directory")
    except Exception as e:
        marker(f"TEST_FAIL:{name}:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:{name}_ms:{elapsed:.2f}")

# 8. Compare a metric to baseline (using a dummy baseline value)
def compare_baseline():
    # Example: compare import time to transformer-libs baseline of 120 ms
    baseline_import_ms = 120.0
    # Retrieve last import benchmark line from stdout not possible; store locally
    # We'll recompute import time quickly
    start = time.time()
    try:
        import OpenArch
    except Exception:
        pass
    import_ms = (time.time() - start) * 1000
    ratio = import_ms / baseline_import_ms if baseline_import_ms else 0
    marker(f"BENCHMARK:vs_transformer-libs_import_ratio:{ratio:.3f}")

def main():
    install_system()
    clone_and_install()
    test_import()
    test_load_checkpoint()
    test_generate()
    benchmark_throughput()
    run_unit_tests()
    compare_baseline()
    marker("RUN_OK")

if __name__ == "__main__":
    main()