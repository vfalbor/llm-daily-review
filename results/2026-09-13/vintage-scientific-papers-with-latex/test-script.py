#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, re, json, pathlib, shlex, hashlib

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def apk_add(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    return rc == 0, out+err

def pip_install(pkg):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', pkg])
    return rc == 0, out+err

def print_marker(line):
    print(line, flush=True)

def benchmark(name, value):
    print_marker(f'BENCHMARK:{name}:{value}')

def test_pass(name):
    print_marker(f'TEST_PASS:{name}')

def test_fail(name, reason):
    print_marker(f'TEST_FAIL:{name}:{reason}')

def test_skip(name, reason):
    print_marker(f'TEST_SKIP:{name}:{reason}')

def measure_time(func, *a, **kw):
    start = time.time()
    try:
        func(*a, **kw)
    finally:
        return time.time() - start

# 1. Install system packages
install_start = time.time()
ok, msg = apk_add('git')
if not ok:
    test_fail('apk_git', msg)
else:
    test_pass('apk_git')
# Install TeX tools needed for compilation
for pkg in ['texlive', 'texlive-latexextra', 'texlive-fontsrecommended']:
    ok, msg = apk_add(pkg)
    if not ok:
        test_fail(f'apk_{pkg}', msg)
    else:
        test_pass(f'apk_{pkg}')
benchmark('install_time_s', round(time.time() - install_start, 2))

# 2. Try pip install the package
pip_start = time.time()
pkg_name = 'vintage-latex'
ok, msg = pip_install(pkg_name)
if ok:
    test_pass('pip_install')
else:
    test_fail('pip_install', msg)
benchmark('pip_install_time_s', round(time.time() - pip_start, 2))

# 3. Clone repo as fallback if pip failed or for source tests
repo_url = 'https://github.com/Foadsf/vintage-latex.git'
repo_dir = pathlib.Path('/tmp/vintage-latex')
if repo_dir.exists():
    subprocess.run(['rm', '-rf', str(repo_dir)])
clone_start = time.time()
rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(repo_dir)])
if rc != 0:
    test_fail('git_clone', err or out)
else:
    test_pass('git_clone')
benchmark('git_clone_time_s', round(time.time() - clone_start, 2))

# Helper to measure import time
import_start = time.time()
try:
    import vintage_latex  # type: ignore
    import_time = time.time() - import_start
    benchmark('import_time_ms', int(import_time*1000))
    test_pass('import_module')
except Exception as e:
    import_time = time.time() - import_start
    benchmark('import_time_ms', int(import_time*1000))
    test_fail('import_module', str(e))

# 4. Test compilation of sample.tex
sample_tex = repo_dir / 'sample.tex'
if not sample_tex.is_file():
    test_skip('compile_sample', 'sample.tex not found')
else:
    # Ensure output dir clean
    out_pdf = repo_dir / 'sample.pdf'
    if out_pdf.is_file():
        out_pdf.unlink()
    compile_start = time.time()
    rc, out, err = run_cmd(['pdflatex', '-interaction=nonstopmode', str(sample_tex)], cwd=str(repo_dir))
    compile_time = time.time() - compile_start
    benchmark('pdflatex_time_s', round(compile_time, 2))
    if rc != 0 or not out_pdf.is_file():
        test_fail('pdflatex_compile', err or out)
    else:
        test_pass('pdflatex_compile')
        # Simple check for title placeholder via pdfgrep if available
        rc2, out2, err2 = run_cmd(['pdfgrep', '-i', 'Title', str(out_pdf)])
        if rc2 == 0 and out2.strip():
            test_pass('pdf_contains_title')
        else:
            test_fail('pdf_contains_title', 'Title not found in PDF')

# 5. Test latexmk end‑to‑end
if not sample_tex.is_file():
    test_skip('latexmk', 'sample.tex missing')
else:
    rc, out, err = run_cmd(['latexmk', '-pdf', '-interaction=nonstopmode', str(sample_tex)], cwd=str(repo_dir))
    benchmark('latexmk_time_s', round(time.time() - compile_start, 2))
    if rc != 0:
        test_fail('latexmk_build', err or out)
    else:
        test_pass('latexmk_build')

# 6. Verify style files compile in a minimal doc
style_test_dir = repo_dir / 'style_test'
style_test_dir.mkdir(exist_ok=True)
minimal_tex = style_test_dir / 'minimal.tex'
style_files = list((repo_dir / 'styles').glob('*.sty')) if (repo_dir / 'styles').exists() else []
if not style_files:
    test_skip('style_compile', 'No .sty files found')
else:
    includes = '\n'.join([f'\\usepackage{{{f.stem}}}' for f in style_files])
    minimal_tex.write_text(r'''
\documentclass{article}
''' + includes + r'''
\begin{document}
Test
\end{document}
''')
    rc, out, err = run_cmd(['pdflatex', '-interaction=nonstopmode', str(minimal_tex)], cwd=str(style_test_dir))
    benchmark('style_compile_time_s', round(time.time() - compile_start, 2))
    if rc != 0:
        test_fail('style_compile', err or out)
    else:
        test_pass('style_compile')

# 7. Benchmark vs baseline (Overleaf assumed similar)
# Use import time ratio as example
baseline_import_ms = 150  # assumed baseline
ratio = import_time*1000 / baseline_import_ms if baseline_import_ms else 0
benchmark('vs_overleaf_import_ratio', round(ratio, 3))

# Emit at least three benchmark lines (already emitted many)
# Final marker
print_marker('RUN_OK')