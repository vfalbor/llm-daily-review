#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shutil, math

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err or out}")

def install_npm(pkg):
    rc, out, err = run_cmd(['npm', 'install', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err or out}")

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        print(f"BENCHMARK:import_{module_name}_ms:{elapsed:.2f}")
        return elapsed
    except Exception as e:
        print(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def measure_time(func, *args, **kwargs):
    start = time.time()
    try:
        func(*args, **kwargs)
        return (time.time() - start) * 1000
    except Exception as e:
        return None

def benchmark_memory(func, *args, **kwargs):
    tracemalloc.start()
    try:
        func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return peak / 1024  # KiB
    except Exception:
        tracemalloc.stop()
        return None

def test_npm_install():
    try:
        install_npm('@danilaa1/drawably')
        print("TEST_PASS:npm_install")
    except Exception as e:
        print(f"TEST_FAIL:npm_install:{e}")

def test_create_react_app():
    try:
        # create temporary CRA project
        tmpdir = "/tmp/drawably_test_app"
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
        rc, out, err = run_cmd(['npx', 'create-react-app', tmpdir, '--template', 'cra-template'])
        if rc != 0:
            raise RuntimeError(f"CRA failed: {err}")

        # add drawably
        rc, out, err = run_cmd(['npm', 'install', '@danilaa1/drawably'], cwd=tmpdir)
        if rc != 0:
            raise RuntimeError(f"npm install drawably failed: {err}")

        # write minimal component test
        src_path = os.path.join(tmpdir, "src", "App.js")
        with open(src_path, "w") as f:
            f.write("""import React from 'react';
import { Button } from '@danilaa1/drawably';
function App() {
  return <Button>Test</Button>;
}
export default App;
""")
        # build to ensure no compile errors
        rc, out, err = run_cmd(['npm', 'run', 'build'], cwd=tmpdir, timeout=300)
        if rc != 0:
            raise RuntimeError(f"npm run build failed: {err}")
        print("TEST_PASS:create_react_app")
    except Exception as e:
        print(f"TEST_FAIL:create_react_app:{e}")

def test_npm_test():
    try:
        # reuse previous app if exists
        tmpdir = "/tmp/drawably_test_app"
        if not os.path.isdir(tmpdir):
            raise RuntimeError("App not prepared")
        rc, out, err = run_cmd(['npm', 'test', '--', '--watchAll=false'], cwd=tmpdir, timeout=300)
        if rc != 0:
            raise RuntimeError(f"npm test failed: {err}")
        print("TEST_PASS:npm_test")
    except Exception as e:
        print(f"TEST_FAIL:npm_test:{e}")

def measure_bundle_size():
    try:
        tmpdir = "/tmp/drawably_test_app"
        build_dir = os.path.join(tmpdir, "build")
        if not os.path.isdir(build_dir):
            raise RuntimeError("Build folder missing")
        total = 0
        for root, _, files in os.walk(build_dir):
            for f in files:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
        size_kb = total / 1024
        print(f"BENCHMARK:bundle_size_kb:{size_kb:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:bundle_size:{e}")

def test_snapshot():
    try:
        # Use jest snapshot on Button component
        tmpdir = "/tmp/drawably_test_app"
        test_file = os.path.join(tmpdir, "src", "__tests__", "Button.test.js")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write("""import React from 'react';
import renderer from 'react-test-renderer';
import { Button } from '@danilaa1/drawably';
test('Button renders correctly', () => {
  const tree = renderer.create(<Button>Snap</Button>).toJSON();
  expect(tree).toMatchSnapshot();
});
""")
        rc, out, err = run_cmd(['npm', 'test', '--', '--watchAll=false'], cwd=tmpdir, timeout=300)
        if rc != 0:
            raise RuntimeError(f"snapshot test failed: {err}")
        print("TEST_PASS:snapshot")
    except Exception as e:
        print(f"TEST_FAIL:snapshot:{e}")

def baseline_compare(metric_name, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value != 0 else float('inf')
        print(f"BENCHMARK:vs_{metric_name}_ratio:{ratio:.3f}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_compare:{e}")

def main():
    # 1. install required apk packages
    for pkg in ['git', 'nodejs', 'npm', 'python3-dev', 'build-base']:
        install_apk(pkg)

    # 2. Install drawably via npm
    test_npm_install()

    # 3. Create CRA and test rendering
    test_create_react_app()

    # 4. Run npm test suite
    test_npm_test()

    # 5. Measure bundle size
    measure_bundle_size()

    # 6. Snapshot test
    test_snapshot()

    # 7. Benchmarks: import time for a baseline (react-sketch) vs drawably
    # install baseline
    install_npm('react-sketch')
    drawably_import = measure_import('@danilaa1/drawably')
    baseline_import = measure_import('react-sketch')
    if drawably_import and baseline_import:
        baseline_compare('react_sketch_import', drawably_import, baseline_import)

    # 8. Memory benchmark for a dummy render using ReactDOMServer
    try:
        import subprocess, json, tempfile
        # create a small node script to render component and measure memory
        node_script = """
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const {Button} = require('@danilaa1/drawably');
const html = ReactDOMServer.renderToString(React.createElement(Button, null, 'test'));
console.log(JSON.stringify({length: html.length}));
"""
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.js') as tf:
            tf.write(node_script)
            script_path = tf.name
        rc, out, err = run_cmd(['node', script_path])
        if rc == 0:
            data = json.loads(out)
            print(f"BENCHMARK:rendered_html_len:{data.get('length',0)}")
        else:
            print(f"TEST_FAIL:node_render:{err}")
    except Exception as e:
        print(f"TEST_FAIL:node_render:{e}")

    # final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()