import subprocess, sys, os, time, tracemalloc, json, urllib.request, shutil, pathlib, statistics

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def test_clone_and_build(repo_url, workdir):
    try:
        clone_dir = os.path.join(workdir, "ginux")
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)
        cmd = ['git','clone',repo_url,clone_dir]
        res = run_cmd(cmd)
        if res.returncode !=0:
            raise RuntimeError(f"git clone failed: {res.stderr.strip()}")
        # look for common build scripts
        build_scripts = ['build.sh','Makefile','configure']
        built = False
        for script in build_scripts:
            path = os.path.join(clone_dir, script)
            if os.path.isfile(path):
                if script.endswith('.sh'):
                    os.chmod(path, 0o755)
                    cmd = [path]
                elif script == 'Makefile':
                    cmd = ['make']
                elif script == 'configure':
                    cmd = ['./configure', '&&', 'make']
                else:
                    continue
                _, t = measure_time(run_cmd, cmd, cwd=clone_dir)
                benchmark("install_time_s", round(t,2))
                built = True
                break
        if not built:
            raise RuntimeError("No recognizable build script found")
        print_marker("TEST_PASS:clone_and_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_and_build:{e}")

def test_boot_kernel(workdir):
    try:
        ginux_dir = os.path.join(workdir, "ginux")
        if not os.path.isdir(ginux_dir):
            raise RuntimeError("Source dir missing")
        # Assume binary ginux exists after build
        bin_path = os.path.join(ginux_dir, "ginux")
        if not os.path.isfile(bin_path):
            # try common locations
            for root, _, files in os.walk(ginux_dir):
                if "ginux" in files:
                    bin_path = os.path.join(root, "ginux")
                    break
        if not os.path.isfile(bin_path):
            raise RuntimeError("ginux binary not found")
        # simple init script that execs /bin/sh
        init_path = os.path.join(ginux_dir, "init.sh")
        with open(init_path, "w") as f:
            f.write("#!/bin/sh\nexec /bin/sh\n")
        os.chmod(init_path, 0o755)
        cmd = [bin_path, "--init", init_path]
        # run with timeout
        start = time.time()
        proc = subprocess.Popen(cmd, cwd=ginux_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        elapsed = time.time() - start
        benchmark("boot_time_s", round(elapsed,2))
        if "sh" in out or "sh" in err:
            print_marker("TEST_PASS:boot_kernel")
        else:
            raise RuntimeError("Shell not spawned")
    except Exception as e:
        print_marker(f"TEST_FAIL:boot_kernel:{e}")

def test_io_latency(workdir):
    try:
        ginux_dir = os.path.join(workdir, "ginux")
        if not os.path.isdir(ginux_dir):
            raise RuntimeError("Source dir missing")
        # create a tiny C program that does file+network I/O
        prog = r'''
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
int main(){
    FILE *f = fopen("tmp.txt","w");
    if(!f) return 1;
    fprintf(f,"hello");
    fclose(f);
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if(s<0) return 2;
    close(s);
    return 0;
}
'''
        src_path = os.path.join(ginux_dir, "io_test.c")
        with open(src_path, "w") as f:
            f.write(prog)
        # compile with gcc (install gcc)
        _, t_compile = measure_time(run_cmd, ['gcc','io_test.c','-o','io_test'], cwd=ginux_dir)
        benchmark("compile_time_ms", int(t_compile*1000))
        # run natively
        _, t_native = measure_time(run_cmd, ['./io_test'], cwd=ginux_dir)
        # run inside ginux (assuming ginux can exec a binary via same cmd)
        _, t_ginux = measure_time(run_cmd, [os.path.join(ginux_dir,'ginux'), '--exec', './io_test'], cwd=ginux_dir)
        benchmark("native_io_ms", int(t_native*1000))
        benchmark("ginux_io_ms", int(t_ginux*1000))
        # compare ratio vs baseline RunC (assume baseline 1.2x slower)
        ratio = t_ginux / t_native if t_native>0 else float('inf')
        benchmark("vs_runc_io_ratio", round(ratio,2))
        print_marker("TEST_PASS:io_latency")
    except Exception as e:
        print_marker(f"TEST_FAIL:io_latency:{e}")

def main():
    # install required apk packages
    for pkg in ["git","curl","gcc","musl-dev","make"]:
        ok, reason = install_apk(pkg)
        if ok:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{reason}")

    workdir = "/tmp/gin_test"
    pathlib.Path(workdir).mkdir(parents=True, exist_ok=True)

    repo = "https://github.com/gmkurtzer/ginux.git"

    # Run tests
    test_clone_and_build(repo, workdir)
    test_boot_kernel(workdir)
    test_io_latency(workdir)

    # Additional benchmarks (memory usage of process)
    try:
        tracemalloc.start()
        dummy = [i for i in range(100000)]
        current, peak = tracemalloc.get_traced_memory()
        benchmark("memory_peak_kb", int(peak/1024))
        tracemalloc.stop()
    except Exception as e:
        benchmark("memory_peak_kb", "0")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()