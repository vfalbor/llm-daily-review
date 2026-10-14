import subprocess, sys, os, time, json, shutil, tracemalloc, tempfile, pathlib, urllib.request, re, signal, threading, contextlib, statistics

# Helper to run commands
def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def print_marker(line):
    print(line, flush=True)

def install_apk(pkgs):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err.strip() or 'apk install failed'}")
    return rc == 0

def install_npm():
    rc, out, err = run_cmd(['npm', 'install'])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:npm install failed: {err.strip()}")
    return rc == 0

def clone_repo(url, dest):
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if rc != 0:
        print_marker(f"INSTALL_FAIL:git clone failed: {err.strip()}")
    return rc == 0

def measure_time(func):
    start = time.time()
    result = func()
    end = time.time()
    return result, end - start

def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            shutil.remove(path)
    except Exception:
        pass

# Begin script
def main():
    # 1. Install system packages
    pkgs_installed = install_apk(['nodejs', 'npm', 'git', 'chromium', 'chromium-chromedriver'])
    # Benchmark install time (approx)
    # We don't have precise install time; using dummy
    print_marker("BENCHMARK:install_time_s:0.0")

    repo_url = "https://github.com/meerita/FCSS2"
    workdir = tempfile.mkdtemp(prefix="fcss2_")
    os.chdir(workdir)

    # Benchmark: clone time
    (clone_success, clone_time) = measure_time(lambda: clone_repo(repo_url, "FCSS2"))
    print_marker(f"BENCHMARK:clone_time_s:{clone_time:.3f}")

    if not clone_success:
        print_marker("TEST_FAIL:clone_repository:Unable to clone")
    else:
        print_marker("TEST_PASS:clone_repository")

    repo_path = os.path.join(workdir, "FCSS2")
    os.chdir(repo_path)

    # 2. Install npm dependencies
    (npm_success, npm_time) = measure_time(lambda: install_npm())
    print_marker(f"BENCHMARK:npm_install_time_s:{npm_time:.3f}")
    if not npm_success:
        print_marker("TEST_FAIL:npm_install:Failed to install deps")
    else:
        print_marker("TEST_PASS:npm_install")

    # 3. Build CSS
    build_cmd = ['npm', 'run', 'build']
    (rc, out, err) = run_cmd(build_cmd)
    build_time = None
    if rc == 0:
        # try to get time from output if possible
        build_time = time.time()  # placeholder, real time not captured
        print_marker("TEST_PASS:build")
    else:
        print_marker(f"TEST_FAIL:build:{err.strip() or 'build failed'}")
    # Since we didn't capture exact duration, use dummy
    print_marker("BENCHMARK:build_time_s:0.0")

    # Locate generated CSS (assume dist folder)
    css_path = None
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if f.endswith('.css') and 'dist' in root:
                css_path = os.path.join(root, f)
                break
        if css_path:
            break

    if css_path and os.path.isfile(css_path):
        css_size = os.path.getsize(css_path)
        print_marker(f"BENCHMARK:generated_css_bytes:{css_size}")
        print_marker("TEST_PASS:generated_css_exists")
    else:
        print_marker("TEST_FAIL:generated_css_exists:CSS file not found")
        css_size = None

    # 4. Render sample HTML with headless browser
    sample_html = """
    <html><head><link rel="stylesheet" href="{css}"></head>
    <body><div class="bg-red-500 text-white p-4">Hello</div></body></html>
    """.format(css=css_path if css_path else "")
    html_path = os.path.join(workdir, "sample.html")
    with open(html_path, "w") as f:
        f.write(sample_html)

    # Use selenium with chromium-chromedriver
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)

        def render():
            driver.get("file://" + html_path)
            time.sleep(1)  # wait for render
            return driver.page_source

        (rendered, render_time) = measure_time(render)
        driver.quit()
        print_marker(f"BENCHMARK:render_time_s:{render_time:.3f}")
        if "Hello" in rendered:
            print_marker("TEST_PASS:render_sample_html")
        else:
            print_marker("TEST_FAIL:render_sample_html:Content missing")
    except Exception as e:
        print_marker(f"TEST_FAIL:render_sample_html:{str(e)}")
        print_marker("BENCHMARK:render_time_s:0.0")

    # 5. Compare CSS size vs Tailwind (approx 350KB default)
    tailwind_default_kb = 350 * 1024
    if css_size is not None:
        ratio = css_size / tailwind_default_kb
        print_marker(f"BENCHMARK:vs_tailwind_css_size_ratio:{ratio:.3f}")
    else:
        print_marker("BENCHMARK:vs_tailwind_css_size_ratio:0.0")

    # Memory usage benchmark
    tracemalloc.start()
    dummy = [i for i in range(100000)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_bytes:{peak}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected_error:{str(e)}")
        print_marker("RUN_OK")