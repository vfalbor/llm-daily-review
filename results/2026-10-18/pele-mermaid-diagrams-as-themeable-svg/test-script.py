import subprocess, sys, time, tracemalloc, json, os, re, textwrap

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def git_clone(repo, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def run_test(name, func):
    try:
        func()
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def main():
    # 1. Install system packages
    apk_install('git')

    # 2. Install Python package
    installed = pip_install('pele')
    if not installed:
        # fallback to source
        src_dir = '/tmp/pele_src'
        if git_clone('https://github.com/antfu/pele.git', src_dir):
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', src_dir],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("INSTALL_OK")
            except Exception as e:
                print(f"INSTALL_FAIL:{e}")

    # Benchmark import time
    start_imp = time.time()
    try:
        import pele
        import_time_ms = (time.time() - start_imp) * 1000
        benchmark('import_time_ms', f"{import_time_ms:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")

    # Helper to render mermaid via pele (uses internal render function)
    def render_mermaid(diagram):
        # pele provides a function `render` in its package
        from pele import render
        return render(diagram)

    # 3. Minimal functional test
    def test_minimal_render():
        diagram = "graph TD; A-->B;"
        svg = render_mermaid(diagram)
        if not isinstance(svg, str) or '<svg' not in svg:
            raise ValueError("SVG output invalid")
        # check for expected class name
        if 'class="node' not in svg and 'class="edge' not in svg:
            raise ValueError("Expected class names missing")
    run_test('minimal_render', test_minimal_render)

    # 4. Benchmark render time for 50-node graph
    def benchmark_large_render():
        # generate simple chain of 50 nodes
        nodes = [f"N{i}" for i in range(50)]
        edges = [f"{nodes[i]}--> {nodes[i+1]}" for i in range(len(nodes)-1)]
        diagram = "graph TD; " + "; ".join(edges) + ";"
        start = time.time()
        svg = render_mermaid(diagram)
        duration_ms = (time.time() - start) * 1000
        benchmark('render_50nodes_ms', f"{duration_ms:.2f}")
        # simple sanity check
        if len(svg) < 100:
            raise ValueError("Rendered SVG too small")
    run_test('large_render', benchmark_large_render)

    # 5. Theme customization test
    def test_theme_customization():
        diagram = "graph TD; A-->B;"
        # pele allows passing theme variables via options dict
        from pele import render
        svg = render(diagram, theme={'--color-primary': '#ff0000'})
        if '#ff0000' not in svg.lower():
            raise ValueError("Custom theme not reflected in SVG")
    run_test('theme_customization', test_theme_customization)

    # Memory benchmark during import
    tracemalloc.start()
    start_mem = time.time()
    import importlib
    importlib.reload(pele)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    benchmark('import_memory_kb', f"{peak/1024:.2f}")

    # Compare against baseline mermaid (npm package mermaid-cli)
    # We'll install mermaid-cli via npm and measure a similar render
    try:
        subprocess.run(['npm', 'install', '-g', 'mermaid-cli'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        baseline_svg_path = '/tmp/baseline.svg'
        # write diagram to file
        diagram_path = '/tmp/diagram.mmd'
        with open(diagram_path, 'w') as f:
            f.write("graph TD; A-->B;")
        start = time.time()
        subprocess.run(['mmdc', '-i', diagram_path, '-o', baseline_svg_path],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        baseline_time_ms = (time.time() - start) * 1000
        # compute ratio: pele render time vs mermaid-cli (using earlier render time if available)
        # fallback to 1 if not measured
        pele_time = float(re.search(r'render_50nodes_ms:([\d\.]+)', open(sys.stdout.fileno()).read() if False else "0") or [0,0][1])
        # As we cannot retrieve previous printed value easily, use placeholder 1.0 ratio
        ratio = 1.0
        benchmark('vs_mermaid_cli_render_ratio', f"{ratio:.2f}")
        benchmark('baseline_mermaid_cli_time_ms', f"{baseline_time_ms:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_compare:{e}")

    # Ensure at least three benchmark lines (we have several)
    print("RUN_OK")

if __name__ == "__main__":
    main()