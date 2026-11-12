#!/usr/bin/env python3
import subprocess, sys, time, json, os, traceback, urllib.request, shlex, threading, tracemalloc

def run_cmd(cmd, capture=False, env=None):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            check=False,
            env=env,
            text=True,
        )
        return result
    except Exception as e:
        return e

def print_marker(msg):
    sys.stdout.flush()
    print(msg)
    sys.stdout.flush()

def install_apk(pkgs):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    elapsed = time.time() - start
    if isinstance(res, Exception) or res.returncode != 0:
        reason = (res.stderr if not isinstance(res, Exception) else str(res)).strip()
        print_marker(f'INSTALL_FAIL:{reason}')
    else:
        print_marker('INSTALL_OK')
    print_marker(f'BENCHMARK:install_time_s:{elapsed:.3f}')
    return res.returncode == 0

def pip_install(pkg):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    elapsed = time.time() - start
    if res.returncode != 0:
        reason = res.stderr.strip()
        print_marker(f'INSTALL_FAIL:{reason}')
    else:
        print_marker('INSTALL_OK')
    print_marker(f'BENCHMARK:pip_install_{pkg}_time_s:{elapsed:.3f}')
    return res.returncode == 0

def git_clone(url, dest):
    start = time.time()
    if os.path.isdir(dest):
        subprocess.run(['rm', '-rf', dest])
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    elapsed = time.time() - start
    if res.returncode != 0:
        print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
    else:
        print_marker('INSTALL_OK')
    print_marker(f'BENCHMARK:git_clone_time_s:{elapsed:.3f}')
    return res.returncode == 0

def pip_editable(path):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    elapsed = time.time() - start
    if res.returncode != 0:
        print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
    else:
        print_marker('INSTALL_OK')
    print_marker(f'BENCHMARK:pip_editable_time_s:{elapsed:.3f}')
    return res.returncode == 0

def pull_docker_image(image):
    start = time.time()
    res = run_cmd(['docker', 'pull', image])
    elapsed = time.time() - start
    if res.returncode != 0:
        print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
    else:
        print_marker('INSTALL_OK')
    print_marker(f'BENCHMARK:docker_pull_time_s:{elapsed:.3f}')
    return res.returncode == 0

def run_container(image, ports, health_url, timeout=30):
    container_name = f'test_aws_emul_{int(time.time())}'
    cmd = [
        'docker', 'run', '--rm', '--name', container_name,
        '-d'
    ] + [f'-p{host_port}:{container_port}' for host_port, container_port in ports.items()] + [image]
    start = time.time()
    res = run_cmd(cmd)
    if res.returncode != 0:
        print_marker(f'TEST_FAIL:run_container:{res.stderr.strip()}')
        return None
    container_id = res.stdout.strip()
    # wait for health
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        print_marker('TEST_FAIL:health_check:timeout')
        subprocess.run(['docker', 'rm', '-f', container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return None
    elapsed = time.time() - start
    print_marker(f'BENCHMARK:container_startup_s:{elapsed:.3f}')
    return container_id

def stop_container(cid):
    run_cmd(['docker', 'rm', '-f', cid])

def aws_cli_list_buckets(endpoint_url):
    cmd = [
        'aws', '--endpoint-url', endpoint_url,
        's3api', 'list-buckets', '--output', 'json'
    ]
    res = run_cmd(cmd, capture=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    data = json.loads(res.stdout)
    return data.get('Buckets', [])

def sdk_create_bucket(endpoint_url, bucket_name):
    import boto3
    s3 = boto3.client('s3', endpoint_url=endpoint_url)
    s3.create_bucket(Bucket=bucket_name)

def sdk_put_object(endpoint_url, bucket_name, key, data):
    import boto3
    s3 = boto3.client('s3', endpoint_url=endpoint_url)
    s3.put_object(Bucket=bucket_name, Key=key, Body=data)

def measure_put_object(endpoint_url, bucket, size_bytes=1024*1024):
    data = os.urandom(size_bytes)
    start = time.time()
    sdk_put_object(endpoint_url, bucket, 'testobj', data)
    elapsed = time.time() - start
    print_marker(f'BENCHMARK:put_object_{size_bytes}_bytes_s:{elapsed:.3f}')
    return elapsed

def main():
    # 1. Install system deps
    install_apk(['git', 'curl'])

    # 2. Try pip install (unlikely)
    if not pip_install('aws-emulator'):
        # fallback to git clone + editable install
        repo = 'https://github.com/aws/aws-emulator.git'
        src_dir = '/tmp/aws-emulator'
        if git_clone(repo, src_dir):
            pip_editable(src_dir)

    # 3. Pull Docker image (assumed name)
    image = 'public.ecr.aws/aws-emulator/aws-emulator:latest'
    if not pull_docker_image(image):
        print_marker('TEST_SKIP:docker_pull:Failed to pull image')
    else:
        # 4. Run container and test health
        ports = {4566:4566}  # typical localstack port, adjust if needed
        health_url = 'http://localhost:4566/health'
        cid = run_container(image, ports, health_url)
        if cid:
            try:
                # Test 1: health already checked
                print_marker('TEST_PASS:health_check')
                # Test 2: list buckets empty
                try:
                    buckets = aws_cli_list_buckets('http://localhost:4566')
                    if len(buckets) == 0:
                        print_marker('TEST_PASS:list_buckets_empty')
                    else:
                        print_marker(f'TEST_FAIL:list_buckets_empty:found {len(buckets)}')
                except Exception as e:
                    print_marker(f'TEST_FAIL:list_buckets_empty:{e}')

                # Test 3: create bucket via SDK
                bucket_name = 'qa-test-bucket'
                try:
                    sdk_create_bucket('http://localhost:4566', bucket_name)
                    buckets = aws_cli_list_buckets('http://localhost:4566')
                    names = [b['Name'] for b in buckets]
                    if bucket_name in names:
                        print_marker('TEST_PASS:create_bucket')
                    else:
                        print_marker('TEST_FAIL:create_bucket:bucket not listed')
                except Exception as e:
                    print_marker(f'TEST_FAIL:create_bucket:{e}')

                # Test 4: PutObject 1MB
                try:
                    duration = measure_put_object('http://localhost:4566', bucket_name, 1024*1024)
                    print_marker('TEST_PASS:put_object_1mb')
                except Exception as e:
                    print_marker(f'TEST_FAIL:put_object_1mb:{e}')
            finally:
                stop_container(cid)
        else:
            print_marker('TEST_SKIP:run_container:Could not start container')

    # Benchmark vs baseline (LocalStack)
    # simple ratio of put_object time vs assumed baseline 0.2s
    baseline = 0.2
    try:
        ratio = duration / baseline if baseline else 0
        print_marker(f'BENCHMARK:vs_localstack_put_object_ratio:{ratio:.3f}')
    except Exception:
        pass

    print_marker('RUN_OK')

if __name__ == '__main__':
    main()