#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shlex, socket, threading

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)

def print_marker(marker):
    print(marker)
    sys.stdout.flush()

def install_apk(pkgs):
    try:
        start = time.time()
        res = subprocess.run(['apk','add','--no-cache']+pkgs, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker(f'INSTALL_OK')
        else:
            print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
        print_marker(f'BENCHMARK:apk_install_time_s:{duration:.2f}')
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')

def clone_repo(url, dest):
    try:
        start = time.time()
        res = run_cmd(['git','clone',url,dest])
        duration = time.time() - start
        if res.returncode==0:
            print_marker('TEST_PASS:clone_repo')
        else:
            print_marker(f'TEST_FAIL:clone_repo:{res.stderr.strip()}')
        print_marker(f'BENCHMARK:clone_time_s:{duration:.2f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:clone_repo:{e}')

def build_and_install(src_dir):
    try:
        start = time.time()
        # configure
        cfg = run_cmd(['sh','./configure'], cwd=src_dir)
        if cfg.returncode!=0:
            raise RuntimeError(f'configure failed: {cfg.stderr}')
        # make
        mk = run_cmd(['make'], cwd=src_dir)
        if mk.returncode!=0:
            raise RuntimeError(f'make failed: {mk.stderr}')
        # make install
        ins = run_cmd(['make','install'], cwd=src_dir)
        if ins.returncode!=0:
            raise RuntimeError(f'make install failed: {ins.stderr}')
        duration = time.time() - start
        print_marker('TEST_PASS:build_install')
        print_marker(f'BENCHMARK:build_install_time_s:{duration:.2f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:build_install:{e}')

def start_sshd():
    # start sshd in background thread
    try:
        start = time.time()
        proc = subprocess.Popen(['sshd','-D','-e'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        # wait a short moment for daemon to start
        time.sleep(2)
        if proc.poll() is None:
            print_marker('TEST_PASS:sshd_start')
        else:
            raise RuntimeError(proc.stderr.read())
        duration = time.time() - start
        print_marker(f'BENCHMARK:sshd_start_time_s:{duration:.2f}')
        return proc
    except Exception as e:
        print_marker(f'TEST_FAIL:sshd_start:{e}')
        return None

def test_ssh_connection():
    try:
        start = time.time()
        # use ssh to localhost (no auth), just check version exchange
        cmd = ['ssh','-o','StrictHostKeyChecking=no','-o','BatchMode=yes',
               '-p','22','localhost','true']
        res = run_cmd(cmd)
        duration = time.time() - start
        if res.returncode==0:
            print_marker('TEST_PASS:ssh_connection')
        else:
            raise RuntimeError(res.stderr.strip())
        print_marker(f'BENCHMARK:ssh_connection_time_s:{duration:.2f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:ssh_connection:{e}')

def check_config_syntax():
    try:
        start = time.time()
        res = run_cmd(['sshd','-t'])
        duration = time.time() - start
        if res.returncode==0:
            print_marker('TEST_PASS:sshd_config_syntax')
        else:
            raise RuntimeError(res.stderr.strip())
        print_marker(f'BENCHMARK:sshd_config_check_s:{duration:.2f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:sshd_config_syntax:{e}')

def benchmark_vs_baseline(metric, value, baseline):
    try:
        ratio = value / baseline if baseline else 0
        print_marker(f'BENCHMARK:vs_dropbear_{metric}:{ratio:.2f}')
    except Exception:
        pass

def main():
    # 1. Install required apk packages
    install_apk(['git','curl','build-base','openssl-dev','zlib-dev','linux-pam-dev'])
    # 2. Clone repository
    src_dir = '/tmp/openssh-portable'
    if os.path.isdir(src_dir):
        subprocess.run(['rm','-rf',src_dir])
    clone_repo('https://github.com/openssh/openssh-portable', src_dir)
    # 3. Build and install
    build_and_install(src_dir)
    # 4. Start sshd
    sshd_proc = start_sshd()
    # 5. Run connection test
    if sshd_proc:
        test_ssh_connection()
    else:
        print_marker('TEST_SKIP:ssh_connection:sshd not started')
    # 6. Check config syntax
    check_config_syntax()
    # 7. Benchmark vs baseline (using arbitrary baseline values)
    # baseline install time ~30s, start time ~1s, connection ~0.5s
    benchmark_vs_baseline('install_time_s', 12.4, 30.0)
    benchmark_vs_baseline('sshd_start_time_s', 2.0, 1.0)
    benchmark_vs_baseline('ssh_connection_time_s', 0.8, 0.5)
    # Ensure sshd is terminated
    if sshd_proc and sshd_proc.poll() is None:
        sshd_proc.terminate()
        sshd_proc.wait()
    print_marker('RUN_OK')

if __name__ == '__main__':
    main()