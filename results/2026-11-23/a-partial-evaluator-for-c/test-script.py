import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib

# Helper to print markers
def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(packages):
    try:
        start = time.time()
        result = subprocess.run(['apk', 'add', '--no-cache'] + packages, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo(url, dest):
    try:
        start = time.time()
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        result = run_cmd(['git', 'clone', '--depth', '1', url, dest])
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        print_marker("INSTALL_OK")
        print_marker(f"BENCHMARK:clone_time_s:{elapsed:.2f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def build_tempo(repo_path):
    try:
        start = time.time()
        # Assume Cargo based build
        result = run_cmd(['cargo', 'build', '--release'], cwd=repo_path)
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        print_marker("INSTALL_OK")
        print_marker(f"BENCHMARK:build_time_s:{elapsed:.2f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def run_hello_world(repo_path):
    try:
        # Create a tiny C file
        c_code = r'''
        #include <stdio.h>
        int main(){ printf("Hello Tempo\n"); return 0; }
        '''
        workdir = pathlib.Path(repo_path) / "tmp_test"
        workdir.mkdir(exist_ok=True)
        src_path = workdir / "hello.c"
        src_path.write_text(c_code)
        tempo_bin = pathlib.Path(repo_path) / "target" / "release" / "tempo"
        if not tempo_bin.is_file():
            raise RuntimeError("tempo binary not found")
        # Use tempo to compile
        start = time.time()
        result = run_cmd([str(tempo_bin), str(src_path), "-o", str(workdir / "hello_opt.c")])
        compile_time = time.time() - start
        print_marker(f"BENCHMARK:tempo_compile_time_ms:{compile_time*1000:.2f}")

        # Compile the optimized C with system gcc
        gcc = shutil.which("gcc")
        if not gcc:
            raise RuntimeError("gcc not found")
        exe_path = workdir / "hello_opt"
        result = run_cmd([gcc, str(workdir / "hello_opt.c"), "-o", str(exe_path)])
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        # Run the executable
        run_res = run_cmd([str(exe_path)])
        if run_res.returncode != 0:
            raise RuntimeError(run_res.stderr)
        output = run_res.stdout.strip()
        if output != "Hello Tempo":
            raise AssertionError(f"Unexpected output: {output}")
        print_marker("TEST_PASS:hello_world")
        print_marker(f"BENCHMARK:hello_world_ms:{compile_time*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:hello_world:{e}")

def test_constant_specialization(repo_path):
    try:
        # C source with a function that can be specialized
        c_code = r'''
        #include <stdio.h>
        int add(int a, int b){ return a+b; }
        int main(){ printf("%d\n", add(3, 4)); return 0; }
        '''
        workdir = pathlib.Path(repo_path) / "tmp_spec"
        workdir.mkdir(exist_ok=True)
        src_path = workdir / "spec.c"
        src_path.write_text(c_code)
        tempo_bin = pathlib.Path(repo_path) / "target" / "release" / "tempo"
        # Run tempo with constant arguments (assuming tempo has such flag; using placeholder --spec)
        start = time.time()
        result = run_cmd([str(tempo_bin), str(src_path), "--spec", "add(3,4)", "-o", str(workdir / "spec_opt.c")])
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:specialize_time_ms:{elapsed*1000:.2f}")
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        opt_src = (workdir / "spec_opt.c").read_text()
        if "return 7;" not in opt_src and "7" not in opt_src:
            raise AssertionError("Constant not inlined")
        print_marker("TEST_PASS:specialization")
    except Exception as e:
        print_marker(f"TEST_FAIL:specialization:{e}")

def benchmark_vs_clang(repo_path):
    try:
        # Simple loop benchmark
        c_code = r'''
        #include <stdio.h>
        int main(){
            volatile int sum=0;
            for(int i=0;i<1000000;i++) sum+=i;
            printf("%d\n", sum);
            return 0;
        }
        '''
        workdir = pathlib.Path(repo_path) / "tmp_bench"
        workdir.mkdir(exist_ok=True)
        src_path = workdir / "bench.c"
        src_path.write_text(c_code)

        tempo_bin = pathlib.Path(repo_path) / "target" / "release" / "tempo"
        gcc = shutil.which("gcc")
        if not gcc:
            raise RuntimeError("gcc not found")

        # Compile with clang (assuming clang installed; fallback to gcc)
        clang = shutil.which("clang") or gcc

        # Tempo compile
        tempo_out = workdir / "tempo_opt.c"
        start = time.time()
        res = run_cmd([str(tempo_bin), str(src_path), "-o", str(tempo_out)])
        tempo_compile = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr)

        tempo_exe = workdir / "tempo_exe"
        res = run_cmd([gcc, str(tempo_out), "-O2", "-o", str(tempo_exe)])
        if res.returncode != 0:
            raise RuntimeError(res.stderr)

        start = time.time()
        run_cmd([str(tempo_exe)])
        tempo_run = time.time() - start

        # Clang compile
        clang_out = workdir / "clang_exe"
        start = time.time()
        res = run_cmd([clang, str(src_path), "-O2", "-o", str(clang_out)])
        clang_compile = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr)

        start = time.time()
        run_cmd([str(clang_out)])
        clang_run = time.time() - start

        # Benchmarks
        print_marker(f"BENCHMARK:tempo_total_ms:{(tempo_compile+tempo_run)*1000:.2f}")
        print_marker(f"BENCHMARK:clang_total_ms:{(clang_compile+clang_run)*1000:.2f}")
        ratio = (tempo_compile+tempo_run) / (clang_compile+clang_run) if (clang_compile+clang_run)>0 else 0
        print_marker(f"BENCHMARK:vs_clang_total_ratio:{ratio:.2f}")

        print_marker("TEST_PASS:benchmark_vs_clang")
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_vs_clang:{e}")

def main():
    # 1. Install required system packages
    install_apk(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm', 'gcc', 'make', 'clang'])

    repo_url = "https://github.com/tempo-lang/tempo"
    repo_dir = "/tmp/tempo_repo"

    # 2. Clone repository
    if not clone_repo(repo_url, repo_dir):
        print_marker("TEST_FAIL:clone_repo:clone failed")
        print_marker("RUN_OK")
        return

    # 3. Build tempo
    if not build_tempo(repo_dir):
        print_marker("TEST_FAIL:build_tempo:build failed")
        print_marker("RUN_OK")
        return

    # 4. Run tests
    run_hello_world(repo_dir)
    test_constant_specialization(repo_dir)
    benchmark_vs_clang(repo_dir)

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()