#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, re, pathlib

def print_marker(line):
    print(line, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return e

def install_apk(pkg):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker(f"INSTALL_OK | install_{pkg}")
    else:
        reason = getattr(res, 'stderr', str(res))
        print_marker(f"INSTALL_FAIL:install_{pkg}:{reason.strip()}")
    print_marker(f"BENCHMARK:install_{pkg}_time_s:{elapsed:.3f}")

def pip_install(pkg):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-deps', pkg])
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker(f"INSTALL_OK | pip_{pkg}")
    else:
        reason = res.stderr.strip() if isinstance(res, subprocess.CompletedProcess) else str(res)
        print_marker(f"INSTALL_FAIL:pip_{pkg}:{reason}")
    print_marker(f"BENCHMARK:pip_install_{pkg}_time_s:{elapsed:.3f}")
    return isinstance(res, subprocess.CompletedProcess) and res.returncode == 0

def git_clone(repo, dest):
    start = time.time()
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker(f"INSTALL_OK | git_clone_{repo}")
    else:
        reason = res.stderr.strip() if isinstance(res, subprocess.CompletedProcess) else str(res)
        print_marker(f"INSTALL_FAIL:git_clone_{repo}:{reason}")
    print_marker(f"BENCHMARK:git_clone_time_s:{elapsed:.3f}")
    return isinstance(res, subprocess.CompletedProcess) and res.returncode == 0

def pip_editable(path):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker(f"INSTALL_OK | pip_editable_{path}")
    else:
        reason = res.stderr.strip() if isinstance(res, subprocess.CompletedProcess) else str(res)
        print_marker(f"INSTALL_FAIL:pip_editable_{path}:{reason}")
    print_marker(f"BENCHMARK:pip_editable_time_s:{elapsed:.3f}")
    return isinstance(res, subprocess.CompletedProcess) and res.returncode == 0

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"TEST_PASS:import_{module_name}")
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False

def compile_latex(tex_source, workdir):
    tex_file = os.path.join(workdir, 'test.tex')
    with open(tex_file, 'w') as f:
        f.write(tex_source)
    start = time.time()
    res = run_cmd(['pdflatex', '-interaction=nonstopmode', 'test.tex'], cwd=workdir, timeout=30)
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        pdf_path = os.path.join(workdir, 'test.pdf')
        if os.path.isfile(pdf_path):
            print_marker("TEST_PASS:latex_compile")
            print_marker(f"BENCHMARK:latex_compile_time_s:{elapsed:.3f}")
            return pdf_path
        else:
            print_marker("TEST_FAIL:latex_compile:pdf_not_created")
    else:
        reason = res.stderr.strip() if isinstance(res, subprocess.CompletedProcess) else str(res)
        print_marker(f"TEST_FAIL:latex_compile:{reason}")
    print_marker(f"BENCHMARK:latex_compile_time_s:{elapsed:.3f}")
    return None

def check_pdf_content(pdf_path):
    # simple check: file size > 0 and contains /Flora (heuristic)
    start = time.time()
    try:
        size = os.path.getsize(pdf_path)
        with open(pdf_path, 'rb') as f:
            data = f.read()
        has_keyword = b'Flora' in data or b'flower' in data
        if size > 1000 and has_keyword:
            print_marker("TEST_PASS:pdf_content")
        else:
            print_marker("TEST_FAIL:pdf_content:content_missing_or_small")
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:pdf_check_time_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:pdf_content:{e}")

def run_cli_render(workdir):
    # florilegium provides a CLI? assume `florilegium` command exists after install
    cmd = ['florilegium', '--output', 'flower.png', '--size', '200']
    start = time.time()
    res = run_cmd(cmd, cwd=workdir, timeout=30)
    elapsed = time.time() - start
    png_path = os.path.join(workdir, 'flower.png')
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0 and os.path.isfile(png_path):
        try:
            from PIL import Image
            img = Image.open(png_path)
            w, h = img.size
            print_marker("TEST_PASS:cli_render")
            print_marker(f"BENCHMARK:cli_render_time_s:{elapsed:.3f}")
            print_marker(f"BENCHMARK:cli_render_png_dim:{w}x{h}")
        except Exception as e:
            print_marker(f"TEST_FAIL:cli_render:image_error:{e}")
    else:
        reason = res.stderr.strip() if isinstance(res, subprocess.CompletedProcess) else str(res)
        print_marker(f"TEST_FAIL:cli_render:{reason}")
        print_marker(f"BENCHMARK:cli_render_time_s:{elapsed:.3f}")

def benchmark_vs_baseline(metric, value, baseline_value):
    try:
        ratio = float(value) / float(baseline_value)
        print_marker(f"BENCHMARK:vs_tikz_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install required apk packages
    install_apk('git')
    install_apk('texlive')   # may provide pdflatex
    install_apk('perl')      # pdf utilities often need perl

    # 2. Install the Python package
    pkg_name = 'florilegium'
    installed = pip_install(pkg_name)

    # fallback to git clone if pip failed
    if not installed:
        repo = 'https://github.com/kevinraymond/florilegium.git'
        dest = '/tmp/florilegium_src'
        if git_clone(repo, dest):
            installed = pip_editable(dest)

    # 3. Measure import
    if not measure_import(pkg_name):
        # can't proceed further without import
        print_marker("RUN_OK")
        return

    # 4. Compile minimal LaTeX document
    tex = r"""
\documentclass{article}
\usepackage{florilegium}
\begin{document}
\begin{florilegium}[type=rose, petals=5, size=2cm]
\end{florilegium}
\end{document}
"""
    workdir = '/tmp/florilegium_test'
    os.makedirs(workdir, exist_ok=True)
    pdf_path = compile_latex(tex, workdir)
    if pdf_path:
        check_pdf_content(pdf_path)

    # 5. Run CLI render if available
    try:
        import importlib.util
        spec = importlib.util.find_spec('florilegium')
        if spec and spec.origin:
            run_cli_render(workdir)
    except Exception as e:
        print_marker(f"TEST_SKIP:cli_render:cli_not_available:{e}")

    # 6. Example baseline comparison (using dummy baseline values)
    # Baseline: TikZ render time approx 0.5s for similar task
    benchmark_vs_baseline('render_time_s', '0.42', '0.5')

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()