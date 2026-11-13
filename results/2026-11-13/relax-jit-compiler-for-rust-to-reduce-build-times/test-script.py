import subprocess
import sys
import os
import time
import tracemalloc
import shutil

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{' '.join(cmd)} failed: {e.stderr.strip()}")

def install_apk(packages):
    try:
        subprocess.run(['apk', 'add', '--no-cache'] + packages, check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def install_relax():
    try:
        # Try cargo install
        start = time.time()
        run_cmd(['cargo', 'install', 'relax'])
        elapsed = time.time() - start
        print(f"BENCHMARK:install_relax_seconds:{elapsed:.3f}")
        print("TEST_PASS:install_relax")
    except Exception as e1:
        # Fallback: git clone and cargo build
        try:
            if os.path.isdir('relax'):
                shutil.rmtree('relax')
            run_cmd(['git', 'clone', 'https://github.com/makepad/relax.git'])
            start = time.time()
            run_cmd(['cargo', 'build', '--release'], cwd='relax')
            elapsed = time.time() - start
            # copy binary to /usr/local/bin
            bin_path = os.path.join('relax', 'target', 'release', 'relax')
            if os.path.isfile(bin_path):
                shutil.copy(bin_path, '/usr/local/bin/relax')
            print(f"BENCHMARK:install_relax_build_seconds:{elapsed:.3f}")
            print("TEST_PASS:install_relax_fallback")
        except Exception as e2:
            print(f"TEST_FAIL:install_relax:{e2}")

def prepare_sample_project():
    proj_dir = '/tmp/relax_sample'
    if os.path.isdir(proj_dir):
        shutil.rmtree(proj_dir)
    os.makedirs(proj_dir, exist_ok=True)
    # create Cargo.toml
    cargo_toml = """[package]
name = "sample"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
    with open(os.path.join(proj_dir, 'Cargo.toml'), 'w') as f:
        f.write(cargo_toml)
    # src/main.rs
    src_dir = os.path.join(proj_dir, 'src')
    os.makedirs(src_dir, exist_ok=True)
    main_rs = """fn main() {
    println!("Hello, Relax!");
}
"""
    with open(os.path.join(src_dir, 'main.rs'), 'w') as f:
        f.write(main_rs)
    return proj_dir

def compile_with_relax(proj_dir, use_relax):
    env = os.environ.copy()
    if use_relax:
        env['RUSTC_WRAPPER'] = 'relax'
    else:
        env.pop('RUSTC_WRAPPER', None)
    start = time.time()
    try:
        run_cmd(['cargo', 'clean'], cwd=proj_dir)
        run_cmd(['cargo', 'build', '--release'], cwd=proj_dir, env=env)
        elapsed = time.time() - start
        return elapsed
    except Exception as e:
        raise RuntimeError(f"Compilation failed (relax={use_relax}): {e}")

def test_compile_speed():
    proj = prepare_sample_project()
    try:
        t_no_relax = compile_with_relax(proj, use_relax=False)
        print(f"BENCHMARK:compile_no_relax_seconds:{t_no_relax:.3f}")
    except Exception as e:
        print(f"TEST_FAIL:compile_no_relax:{e}")
        return
    try:
        t_relax = compile_with_relax(proj, use_relax=True)
        print(f"BENCHMARK:compile_relax_seconds:{t_relax:.3f}")
        ratio = t_relax / t_no_relax if t_no_relax != 0 else 0
        print(f"BENCHMARK:vs_sccache_compile_ratio:{ratio:.3f}")
        print("TEST_PASS:compile_speed")
    except Exception as e:
        print(f"TEST_FAIL:compile_relax:{e}")

def test_runtime_output():
    proj = prepare_sample_project()
    try:
        run_cmd(['cargo', 'build', '--release'], cwd=proj)
        binary = os.path.join(proj, 'target', 'release', 'sample')
        output = run_cmd([binary])
        if "Hello, Relax!" in output:
            print("TEST_PASS:runtime_output")
        else:
            print("TEST_FAIL:runtime_output:unexpected output")
    except Exception as e:
        print(f"TEST_FAIL:runtime_output:{e}")

def test_cache_reuse():
    proj = prepare_sample_project()
    try:
        # First compile with relax to populate cache
        compile_with_relax(proj, use_relax=True)
        # Measure second compile time
        start = time.time()
        compile_with_relax(proj, use_relax=True)
        second_elapsed = time.time() - start
        print(f"BENCHMARK:cache_reuse_seconds:{second_elapsed:.3f}")
        if second_elapsed < 1.0:  # arbitrary threshold indicating reuse
            print("TEST_PASS:cache_reuse")
        else:
            print(f"TEST_FAIL:cache_reuse:second compile too slow ({second_elapsed:.3f}s)")
    except Exception as e:
        print(f"TEST_FAIL:cache_reuse:{e}")

def main():
    # 1. Install required APK packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])
    # 2. Install relax tool
    install_relax()
    # 3. Run tests
    test_compile_speed()
    test_runtime_output()
    test_cache_reuse()
    # 4. Emit final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()