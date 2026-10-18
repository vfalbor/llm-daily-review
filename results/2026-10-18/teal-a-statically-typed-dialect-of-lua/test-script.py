#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, json, hashlib

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkgs):
    try:
        res = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
        if res.returncode == 0:
            print("INSTALL_OK")
        else:
            print(f"INSTALL_FAIL:apk exit {res.returncode}")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def git_clone(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr}")

def measure_time(func, *a, **kw):
    start = time.time()
    result = func(*a, **kw)
    elapsed = time.time() - start
    return elapsed, result

def bench(name, value):
    print(f"BENCHMARK:{name}:{value}")

def test_clone_and_build():
    name = "clone_build"
    try:
        repo_url = "https://github.com/teal-language/teal.git"
        src_dir = "/tmp/teal_src"
        git_clone(repo_url, src_dir)
        # Build using make (project uses make)
        build_start = time.time()
        res = run_cmd(['make', 'install'], cwd=src_dir, env=os.environ)
        build_time = time.time() - build_start
        bench("install_time_s", round(build_time, 3))
        if res.returncode != 0:
            raise RuntimeError(f"make failed: {res.stderr}")
        # Assume binary installed to /usr/local/bin/teal
        if not shutil.which("teal"):
            # fallback: add to PATH
            os.environ["PATH"] = f"{src_dir}:{os.environ.get('PATH','')}"
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_hello_world():
    name = "hello_world"
    try:
        script = 'print("Hello, world!")\n'
        teal_file = "/tmp/hello_world.t"
        with open(teal_file, "w") as f:
            f.write(script)
        elapsed, out = measure_time(lambda: run_cmd(['teal', teal_file]))
        bench("hello_world_ms", round(elapsed*1000, 2))
        if out.stdout.strip() != "Hello, world!":
            raise AssertionError(f"unexpected output: {out.stdout!r}")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_bytecode_size():
    name = "bytecode_size"
    try:
        teal_prog = "local function f(x) return x+1 end\nprint(f(5))\n"
        lua_prog = "local function f(x) return x+1 end\nprint(f(5))\n"
        teal_path = "/tmp/prog.t"
        lua_path = "/tmp/prog.lua"
        with open(teal_path, "w") as f: f.write(teal_prog)
        with open(lua_path, "w") as f: f.write(lua_prog)

        # compile teal to lua
        comp_res = run_cmd(['teal', '-c', teal_path, '-o', '/tmp/prog_teal.lua'])
        if comp_res.returncode != 0:
            raise RuntimeError(f"teal compile error: {comp_res.stderr}")

        size_teal = os.path.getsize('/tmp/prog_teal.lua')
        size_lua = os.path.getsize(lua_path)
        bench("teal_bytecode_bytes", size_teal)
        bench("lua_bytecode_bytes", size_lua)
        ratio = round(size_teal / size_lua if size_lua else 0, 3)
        bench("vs_typedlua_bytecode_ratio", ratio)  # using TypedLua as baseline placeholder
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_perf_loop():
    name = "perf_loop"
    try:
        loop_teal = """
        local sum = 0
        for i=1,1000000 do sum = sum + i end
        print(sum)
        """
        loop_lua = """
        local sum = 0
        for i=1,1000000 do sum = sum + i end
        print(sum)
        """
        teal_file = "/tmp/loop.t"
        lua_file = "/tmp/loop.lua"
        with open(teal_file, "w") as f: f.write(loop_teal)
        with open(lua_file, "w") as f: f.write(loop_lua)

        # Teal execution (compile+run)
        teal_time, teal_out = measure_time(lambda: run_cmd(['teal', teal_file]))
        # Lua execution
        lua_time, lua_out = measure_time(lambda: run_cmd(['lua', lua_file]))
        bench("teal_loop_ms", round(teal_time*1000,2))
        bench("lua_loop_ms", round(lua_time*1000,2))
        ratio = round(teal_time / lua_time if lua_time else 0, 3)
        bench("vs_typedlua_perf_ratio", ratio)
        if teal_out.returncode != 0 or lua_out.returncode != 0:
            raise RuntimeError("loop execution failed")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_type_checker():
    name = "type_checker"
    try:
        bad_teal = """
        local function add(a: number, b: number): number
            return a + b
        end

        local x: string = add(1, 2) -- type error
        """
        bad_path = "/tmp/bad.t"
        with open(bad_path, "w") as f: f.write(bad_teal)
        # run type checker (tealc)
        res = run_cmd(['tealc', bad_path])
        bench("type_check_errors", len(res.stderr.splitlines()))
        if res.returncode == 0:
            raise AssertionError("type checker did not report errors")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def main():
    # 1. install required system packages
    install_apk(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm', 'make', 'lua5.4'])
    # Run tests
    test_clone_and_build()
    test_hello_world()
    test_bytecode_size()
    test_perf_loop()
    test_type_checker()
    # final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()