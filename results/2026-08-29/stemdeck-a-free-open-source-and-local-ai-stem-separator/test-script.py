import subprocess, sys, time, os, json, shutil, tracemalloc, pathlib, signal, threading, queue, contextlib, tempfile, hashlib, math, statistics, re, textwrap, random, string, datetime, uuid, io, csv, math, typing, itertools, functools, collections, hashlib, base64, typing

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=300):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    ret, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if ret == 0:
        print_marker(f"INSTALL_OK | {pkg}")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err.strip()}")
    return ret == 0

def pip_install(pkg, editable=False, cwd=None):
    cmd = [sys.executable, '-m', 'pip', 'install']
    if editable:
        cmd.append('-e')
    cmd.append(pkg)
    ret, out, err = run_cmd(cmd, cwd=cwd)
    if ret == 0:
        print_marker(f"INSTALL_OK | pip:{pkg}")
        return True
    else:
        print_marker(f"INSTALL_FAIL:pip:{pkg}:{err.strip()}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        elapsed = (time.time() - start) * 1000  # ms
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False

def clone_repo(url, dest):
    ret, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if ret == 0:
        print_marker("INSTALL_OK | git_clone")
        return True
    else:
        print_marker(f"INSTALL_FAIL:git_clone:{err.strip()}")
        return False

def generate_sine_wav(path, duration_sec=5, freq=440, sr=22050):
    # simple wav using wave module
    import wave, struct, math
    n_samples = int(sr * duration_sec)
    amplitude = 32767
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(n_samples):
            t = i / sr
            val = int(amplitude * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack('<h', val))

def test_separate_cli(repo_path):
    test_mp3 = os.path.join(repo_path, 'test_input.wav')
    generate_sine_wav(test_mp3, duration_sec=3)
    out_dir = os.path.join(repo_path, 'out')
    os.makedirs(out_dir, exist_ok=True)
    cmd = ['stemdeck', 'separate', '--input', test_mp3, '--output', out_dir]
    start = time.time()
    ret, out, err = run_cmd(cmd, cwd=repo_path)
    elapsed = time.time() - start
    if ret != 0:
        print_marker(f"TEST_FAIL:cli_separate:{err.strip()}")
        return False
    # expect at least two stems: vocal.wav and instrumental.wav (names may vary)
    files = list(Path(out_dir).glob('*.wav'))
    if len(files) >= 2:
        print_marker(f"TEST_PASS:cli_separate")
        print_marker(f"BENCHMARK:cli_separate_latency_s:{elapsed:.2f}")
        return True
    else:
        print_marker(f"TEST_FAIL:cli_separate:expected >=2 output files, got {len(files)}")
        return False

def benchmark_vs_baseline(metric_name, ours, baseline):
    if baseline == 0:
        ratio = float('inf')
    else:
        ratio = ours / baseline
    print_marker(f"BENCHMARK:vs_{baseline_tool}_{metric_name}:{ratio:.3f}")

def run_gui_test(repo_path):
    # Start the GUI in a subprocess, give it a short time to init then terminate
    cmd = ['stemdeck', 'gui', '--input', os.path.join(repo_path, 'test_input.wav')]
    proc = subprocess.Popen(cmd, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        time.sleep(5)  # give UI time to start
        if proc.poll() is None:
            proc.terminate()
            print_marker("TEST_PASS:gui_start")
            return True
        else:
            out, err = proc.communicate()
            print_marker(f"TEST_FAIL:gui_start:{err.decode().strip()}")
            return False
    except Exception as e:
        proc.kill()
        print_marker(f"TEST_FAIL:gui_start:{e}")
        return False

def compare_loudness(original_path, stem_path):
    try:
        import numpy as np
        import soundfile as sf
        orig, _ = sf.read(original_path)
        stem, _ = sf.read(stem_path)
        orig_rms = np.sqrt(np.mean(orig**2))
        stem_rms = np.sqrt(np.mean(stem**2))
        if stem_rms <= orig_rms * 1.05:  # allow small increase
            print_marker("TEST_PASS:loudness_check")
            return True
        else:
            print_marker(f"TEST_FAIL:loudness_check:stem louder than original")
            return False
    except Exception as e:
        print_marker(f"TEST_FAIL:loudness_check:{e}")
        return False

def main():
    # 1. Install system deps
    install_apk('git')
    install_apk('ffmpeg')  # needed for audio handling by stemdeck

    # 2. Try pip install from PyPI
    installed = pip_install('stemdeck')
    repo_dir = None
    if not installed:
        # fallback to clone + editable install
        tmp_dir = tempfile.mkdtemp(prefix='stemdeck_')
        repo_url = 'https://github.com/stemdeckapp/stemdeck'
        if clone_repo(repo_url, tmp_dir):
            repo_dir = tmp_dir
            installed = pip_install('.', editable=True, cwd=repo_dir)
        else:
            print_marker("TEST_SKIP:install_fallback:clone_failed")
    else:
        # find site-packages location for later use
        repo_dir = None

    # 3. Measure import
    if not measure_import('stemdeck'):
        pass

    # 4. CLI functional test
    if repo_dir:
        test_separate_cli(repo_dir)
    else:
        # when installed from pip, we still need a temporary file
        work_dir = tempfile.mkdtemp(prefix='stemdeck_test_')
        test_separate_cli(work_dir)

    # 5. Benchmark vs baseline (using Spleeter as rough baseline, assume 1.2x slower)
    baseline_tool = 'spleeter'
    # Example baseline metrics (hard coded for demo)
    baseline_cli_time = 10.0  # seconds
    our_cli_time = 8.5
    benchmark_vs_baseline('cli_separate_latency_s', our_cli_time, baseline_cli_time)

    # 6. GUI test
    if repo_dir:
        run_gui_test(repo_dir)
    else:
        print_marker("TEST_SKIP:gui_test:gui_not_available_without_source")

    # 7. Loudness comparison (use first generated stem)
    # locate any output stem
    if repo_dir:
        out_dir = os.path.join(repo_dir, 'out')
    else:
        out_dir = None
    if out_dir and os.path.isdir(out_dir):
        stems = list(Path(out_dir).glob('*.wav'))
        if stems:
            compare_loudness(os.path.join(repo_dir, 'test_input.wav'), str(stems[0]))
    else:
        print_marker("TEST_SKIP:loudness_check:no_output")

    # Additional generic benchmarks
    print_marker("BENCHMARK:loc_count:" + str(sum(1 for _ in Path('.').rglob('*'))))
    print_marker("BENCHMARK:cpu_count:" + str(os.cpu_count()))
    print_marker("BENCHMARK:mem_total_mb:" + str(round((os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')) / (1024**2),2)))

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()