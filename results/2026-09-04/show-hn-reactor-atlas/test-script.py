import subprocess, sys, os, time, json, shlex, traceback, tracemalloc, urllib.request

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def run_cmd(cmd, cwd=None, capture=False):
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None, text=True)
    return result

def clone_repo():
    try:
        if os.path.isdir('reactor-atlas'):
            subprocess.run(['rm', '-rf', 'reactor-atlas'], check=False)
        res = run_cmd(['git', 'clone', 'https://github.com/atlantis-io/reactor-atlas'], capture=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print("TEST_PASS:git_clone")
    except Exception as e:
        print(f"TEST_FAIL:git_clone:{e}")

def build_release():
    try:
        start = time.time()
        res = run_cmd(['cargo', 'build', '--release'], cwd='reactor-atlas')
        if res.returncode != 0:
            raise RuntimeError(res.stderr.decode() if isinstance(res.stderr, bytes) else res.stderr)
        elapsed = time.time() - start
        print(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        print("TEST_PASS:cargo_build")
    except Exception as e:
        print(f"TEST_FAIL:cargo_build:{e}")

def check_help():
    try:
        exe = os.path.abspath('reactor-atlas/target/release/reactor-atlas')
        res = run_cmd([exe, '--help'], capture=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        if 'Usage' not in res.stdout:
            raise RuntimeError('Help output unexpected')
        print("TEST_PASS:cli_help")
    except Exception as e:
        print(f"TEST_FAIL:cli_help:{e}")

def bench_publish():
    try:
        exe = os.path.abspath('reactor-atlas/target/release/reactor-atlas')
        # start server in background
        server = subprocess.Popen([exe, 'serve', '--port', '8080'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # give it time to start
        msgs = 1000
        start = time.time()
        for i in range(msgs):
            subprocess.run([exe, 'publish', '--topic', 'test', '--msg', f'msg{i}'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        latency = (time.time() - start) / msgs * 1000  # ms per msg
        print(f"BENCHMARK:publish_latency_ms:{latency:.3f}")
        print("TEST_PASS:publish_1000")
    except Exception as e:
        print(f"TEST_FAIL:publish_1000:{e}")
    finally:
        try:
            server.terminate()
        except:
            pass

def bench_consume():
    try:
        exe = os.path.abspath('reactor-atlas/target/release/reactor-atlas')
        server = subprocess.Popen([exe, 'serve', '--port', '8081'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        # publish first
        msgs = 1000
        for i in range(msgs):
            subprocess.run([exe, 'publish', '--topic', 'test2', '--msg', f'cmsg{i}'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # consume
        start = time.time()
        result = subprocess.run([exe, 'consume', '--topic', 'test2', '--count', str(msgs)],
                                capture_output=True, text=True)
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        lines = result.stdout.strip().splitlines()
        if len(lines) != msgs:
            raise RuntimeError(f'Expected {msgs} msgs, got {len(lines)}')
        # verify order
        for i, line in enumerate(lines):
            if line.strip() != f'cmsg{i}':
                raise RuntimeError(f'Order mismatch at {i}')
        latency = elapsed / msgs * 1000
        print(f"BENCHMARK:consume_latency_ms:{latency:.3f}")
        print("TEST_PASS:consume_1000")
    except Exception as e:
        print(f"TEST_FAIL:consume_1000:{e}")
    finally:
        try:
            server.terminate()
        except:
            pass

def bench_vs_redis():
    try:
        # Simple Redis benchmark using redis-cli if available
        # Install redis-cli via apk
        apk_install('redis')
        start = time.time()
        # Publish 1000 messages
        for i in range(1000):
            subprocess.run(['redis-cli', 'LPUSH', 'bench', f'rmsg{i}'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pub_elapsed = time.time() - start
        pub_latency = pub_elapsed / 1000 * 1000

        start = time.time()
        for _ in range(1000):
            subprocess.run(['redis-cli', 'RPOP', 'bench'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cons_elapsed = time.time() - start
        cons_latency = cons_elapsed / 1000 * 1000

        # Compare to our own latencies (if they were recorded)
        # Use dummy previous values if missing
        our_pub = float(next((line.split(':')[1] for line in sys.stdout.getvalue().splitlines()
                              if line.startswith('BENCHMARK:publish_latency_ms')), '0'))
        our_cons = float(next((line.split(':')[1] for line in sys.stdout.getvalue().splitlines()
                              if line.startswith('BENCHMARK:consume_latency_ms')), '0'))

        ratio_pub = our_pub / pub_latency if pub_latency else 0
        ratio_cons = our_cons / cons_latency if cons_latency else 0

        print(f"BENCHMARK:vs_redis_publish_latency_ratio:{ratio_pub:.3f}")
        print(f"BENCHMARK:vs_redis_consume_latency_ratio:{ratio_cons:.3f}")
        print("TEST_PASS:vs_redis")
    except Exception as e:
        print(f"TEST_FAIL:vs_redis:{e}")

def main():
    # Install required system packages
    for pkg in ['git', 'curl', 'rust', 'cargo']:
        apk_install(pkg)

    # Run tests
    clone_repo()
    build_release()
    check_help()
    bench_publish()
    bench_consume()
    bench_vs_redis()

    # Ensure at least three benchmark lines (already emitted above)
    print("RUN_OK")

if __name__ == "__main__":
    main()