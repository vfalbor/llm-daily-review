import subprocess, sys, time, tracemalloc, os, json, hashlib, tempfile, shutil, contextlib, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err.strip() or 'apk error'}")
    return rc == 0

def pip_install(package):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    if rc == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:{package}:{err.strip() or 'pip error'}")
        return False

def git_clone(url, dest):
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if rc == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:git_clone:{err.strip() or 'git error'}")
        return False

def pip_editable(path):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    if rc == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:editable:{err.strip() or 'pip error'}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        dur = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{dur:.2f}")
        return True, dur, peak / 1024
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False, None, None

def create_sine_wave(duration=0.5, sr=22050, freq=440.0):
    import numpy as np
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    return (wave * 32767).astype(np.int16)

def write_wav(data, sr, path):
    import wave
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())

def run_dettato(audio_path, out_path):
    start = time.time()
    try:
        import dettato
        midi = dettato.transcribe(audio_path)
        midi.save(out_path)
        dur = (time.time() - start) * 1000
        size = os.path.getsize(out_path)
        print_marker(f"BENCHMARK:dettato_inference_ms:{dur:.2f}")
        print_marker(f"BENCHMARK:dettato_midi_size_bytes:{size}")
        return True, dur, size
    except Exception as e:
        print_marker(f"TEST_FAIL:dettato_inference:{e}")
        return False, None, None

def run_baseline(audio_path, out_path):
    # Use aubio as simple baseline for onset detection -> dummy MIDI
    start = time.time()
    try:
        import aubio
        samplerate = 22050
        win_s = 512
        hop_s = win_s // 2
        s = aubio.source(audio_path, samplerate, hop_s)
        o = aubio.onset("default", win_s, hop_s, samplerate)
        onsets = []
        total_frames = 0
        while True:
            samples, read = s()
            if o(samples):
                onsets.append(o.get_last())
            total_frames += read
            if read < hop_s:
                break
        # Write dummy midi (just timestamps)
        from mido import Message, MidiFile, MidiTrack
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        for ts in onsets:
            track.append(Message('note_on', note=60, velocity=64, time=int(ts*1000)))
        mid.save(out_path)
        dur = (time.time() - start) * 1000
        size = os.path.getsize(out_path)
        print_marker(f"BENCHMARK:aubio_inference_ms:{dur:.2f}")
        print_marker(f"BENCHMARK:aubio_midi_size_bytes:{size}")
        return True, dur, size
    except Exception as e:
        print_marker(f"TEST_FAIL:aubio_inference:{e}")
        return False, None, None

def validate_midi(path):
    try:
        from mido import MidiFile
        mf = MidiFile(path)
        # simple validation: at least one track and one message
        if len(mf.tracks) == 0:
            raise ValueError("No tracks")
        msgs = sum(1 for _ in mf.tracks[0])
        if msgs == 0:
            raise ValueError("Empty track")
        print_marker("TEST_PASS:validate_midi")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:validate_midi:{e}")
        return False

def benchmark_memory(func, *args, **kwargs):
    tracemalloc.start()
    try:
        func(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

def main():
    # 1. Install apk packages
    install_apk('git')
    # ensure pip is up‑to‑date
    pip_install('pip --upgrade')
    # 2. Install dettato via pip, fallback to git
    if not pip_install('dettato'):
        repo = 'https://github.com/kobi/dettato.git'
        tmpdir = tempfile.mkdtemp()
        if git_clone(repo, tmpdir):
            pip_editable(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 3. Measure import time
    imported, imp_time, imp_mem = measure_import('dettato')
    if not imported:
        pass  # continue

    # 4. Prepare synthetic audio
    try:
        sr = 22050
        wav_data = create_sine_wave(duration=0.5, sr=sr)
        audio_file = os.path.join(tempfile.gettempdir(), 'test.wav')
        write_wav(wav_data, sr, audio_file)
    except Exception as e:
        print_marker(f"TEST_FAIL:audio_generation:{e}")
        audio_file = None

    # 5. Run dettato inference
    dettato_midi = os.path.join(tempfile.gettempdir(), 'dettato.mid')
    dett_success, dett_time, dett_size = False, None, None
    if audio_file:
        dett_success, dett_time, dett_size = run_dettato(audio_file, dettato_midi)

    # 6. Run baseline (aubio)
    baseline_midi = os.path.join(tempfile.gettempdir(), 'aubio.mid')
    base_success, base_time, base_size = False, None, None
    if audio_file:
        base_success, base_time, base_size = run_baseline(audio_file, baseline_midi)

    # 7. Compare performance
    if dett_success and base_success:
        ratio = dett_time / base_time if base_time else 0
        print_marker(f"BENCHMARK:vs_aubio_inference_ratio:{ratio:.2f}")

    # 8. Validate MIDI output
    if dett_success:
        validate_midi(dettato_midi)

    # 9. Memory benchmark for dettato inference
    if dett_success:
        benchmark_memory(run_dettato, audio_file, dettato_midi)

    # 10. Additional generic benchmarks
    start = time.time()
    for _ in range(1000):
        hashlib.sha256(b'test').hexdigest()
    bench = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:hash_loop_ms:{bench:.2f}")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()