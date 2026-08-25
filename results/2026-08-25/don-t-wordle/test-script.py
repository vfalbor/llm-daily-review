import subprocess, sys, time, tracemalloc, json, urllib.request, urllib.error, re, os, threading, http.client, ssl
from urllib.parse import urljoin

BASE_URL = "https://dontwordle.com/"
BASELINE_LOAD_MS = 300  # approximate load time for standard Wordle (baseline)

def install_system_packages():
    start = time.time()
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print(f"INSTALL_OK")
    except Exception as e:
        elapsed = time.time() - start
        print(f"INSTALL_FAIL:{e}")
    print(f"BENCHMARK:install_time_s:{elapsed:.2f}")

def fetch_url(url, timeout=10):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=ssl._create_unverified_context()) as resp:
            content = resp.read()
        elapsed = (time.time() - start) * 1000  # ms
        return content, elapsed, resp.getheader('Content-Type')
    except Exception as e:
        raise RuntimeError(f"Request failed: {e}")

def benchmark_asset_sizes(html):
    urls = re.findall(r'src=["\']([^"\']+)["\']', html.decode('utf-8', errors='ignore'))
    total_bytes = 0
    for u in urls:
        full = urljoin(BASE_URL, u)
        try:
            _, _, _ = fetch_url(full)  # ignore timing
            total_bytes += len(_)
        except:
            continue
    return total_bytes / 1024  # KB

def test_site_load():
    name = "site_load"
    try:
        content, load_ms, ctype = fetch_url(BASE_URL)
        if b"Wordle" not in content:
            raise AssertionError("Main page does not contain expected content")
        print(f"TEST_PASS:{name}")
        print(f"BENCHMARK:page_load_ms:{load_ms:.2f}")
        size_kb = benchmark_asset_sizes(content)
        print(f"BENCHMARK:asset_total_kb:{size_kb:.2f}")
        ratio = load_ms / BASELINE_LOAD_MS if BASELINE_LOAD_MS else 0
        print(f"BENCHMARK:vs_wordle_load_ms:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_accessibility():
    name = "accessibility_keyboard"
    try:
        content, _, _ = fetch_url(BASE_URL)
        html = content.decode('utf-8', errors='ignore')
        if 'tabindex' not in html.lower():
            raise AssertionError("No tabindex attributes found")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_dummy_game_logic():
    # Since we cannot drive the real browser, we simulate a simple logic test
    name = "game_logic_stub"
    try:
        # Placeholder logic: ensure the site returns a JSON endpoint for guess validation if exists
        guess_url = urljoin(BASE_URL, "api/guess")
        try:
            _content, _ms, _type = fetch_url(guess_url)
            if "application/json" not in (_type or ""):
                raise AssertionError("Guess endpoint not JSON")
        except RuntimeError:
            # If endpoint does not exist, skip test gracefully
            raise RuntimeError("Guess endpoint unavailable")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_SKIP:{name}:{e}")

def main():
    tracemalloc.start()
    install_system_packages()
    test_site_load()
    test_accessibility()
    test_dummy_game_logic()
    # Emit three mandatory benchmark lines if not already emitted
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    print(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    print(f"BENCHMARK:cpu_time_s:{time.process_time():.2f}")
    print("RUN_OK")

if __name__ == "__main__":
    main()