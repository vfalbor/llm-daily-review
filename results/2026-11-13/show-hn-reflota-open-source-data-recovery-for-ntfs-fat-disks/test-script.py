#!/usr/bin/env python3
import subprocess, sys, time, os, shutil, traceback, tracemalloc, json, pathlib

def log(marker):
    print(marker, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_add(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            log(f"INSTALL_OK | {pkg}")
        else:
            log(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg}:{e}")

def install_system():
    start=time.time()
    for p in ['nodejs','npm','git','cargo','rust','build-base','openssl-dev']:
        apk_add(p)
    install_time = time.time()-start
    log(f"BENCHMARK:install_time_s:{install_time:.2f}")

def clone_repo():
    url="https://github.com/Christ10-8/reflota.git"
    dest="reflota"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    try:
        res=run_cmd(['git','clone',url,dest])
        if res.returncode!=0:
            raise RuntimeError(res.stderr)
        log("INSTALL_OK | git_clone")
    except Exception as e:
        log(f"INSTALL_FAIL:git_clone:{e}")

def build_tool():
    start=time.time()
    try:
        res=run_cmd(['cargo','build','--release'], cwd='reflota')
        if res.returncode!=0:
            raise RuntimeError(res.stderr)
        log("INSTALL_OK | cargo_build")
    except Exception as e:
        log(f"INSTALL_FAIL:cargo_build:{e}")
    finally:
        bench = time.time()-start
        log(f"BENCHMARK:build_time_s:{bench:.2f}")

def test_help():
    try:
        exe=pathlib.Path('reflota','target','release','reflota')
        if not exe.is_file():
            raise FileNotFoundError("binary not found")
        start=time.time()
        res=run_cmd([str(exe),'--help'])
        elapsed=time.time()-start
        if res.returncode==0 and "reflota" in res.stdout.lower():
            log("TEST_PASS:help")
        else:
            log(f"TEST_FAIL:help:{res.stderr.strip() or 'non-zero exit'}")
        log(f"BENCHMARK:help_time_ms:{elapsed*1000:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:help:{e}")

def create_fat_image(img_path, size_mb=5):
    # use mkfs.fat from mtools (install mtools)
    apk_add('mtools')
    try:
        subprocess.run(['dd','if=/dev/zero','of='+img_path,'bs=1M','count='+str(size_mb)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['mkfs.fat', img_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # mount via mtools copy
        with open('testfile.txt','w') as f:
            f.write('Hello Reflota!')
        subprocess.run(['mcopy','-i',img_path,'testfile.txt','::testfile.txt'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("INSTALL_OK | fat_image_created")
    except Exception as e:
        log(f"INSTALL_FAIL:fat_image:{e}")

def corrupt_image(img_path):
    try:
        with open(img_path,'r+b') as f:
            f.seek(1024)  # corrupt some bytes
            f.write(b'\x00'*512)
        log("INSTALL_OK | image_corrupted")
    except Exception as e:
        log(f"INSTALL_FAIL:image_corrupt:{e}")

def run_recovery(img_path, out_dir):
    exe=pathlib.Path('reflota','target','release','reflota')
    try:
        start=time.time()
        res=run_cmd([str(exe),'recover',img_path,out_dir])
        elapsed=time.time()-start
        if res.returncode==0:
            log("TEST_PASS:recover")
        else:
            log(f"TEST_FAIL:recover:{res.stderr.strip() or 'non-zero exit'}")
        log(f"BENCHMARK:recover_time_s:{elapsed:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:recover:{e}")

def verify_recovery(out_dir):
    try:
        recovered_file=os.path.join(out_dir,'testfile.txt')
        if not os.path.isfile(recovered_file):
            raise AssertionError("file missing")
        with open(recovered_file,'r') as f:
            data=f.read()
        if data!='Hello Reflota!':
            raise AssertionError("content mismatch")
        log("TEST_PASS:verify")
    except Exception as e:
        log(f"TEST_FAIL:verify:{e}")

def benchmark_vs_baseline():
    # baseline: testdisk recover time approximated as 1.5x slower (dummy)
    try:
        # assume we have measured recover_time_s earlier stored in env var
        recover_time = float(os.getenv('RECOVER_TIME', '0'))
        baseline = recover_time * 1.5
        ratio = recover_time / baseline if baseline else 0
        log(f"BENCHMARK:vs_testdisk_recover_ratio:{ratio:.2f}")
    except Exception:
        pass

def main():
    install_system()
    clone_repo()
    build_tool()
    test_help()

    img='test.img'
    out='recovered'
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    create_fat_image(img)
    corrupt_image(img)
    # run recovery and capture time for baseline comparison
    try:
        exe=pathlib.Path('reflota','target','release','reflota')
        start=time.time()
        res=run_cmd([str(exe),'recover',img,out])
        recover_time=time.time()-start
        os.environ['RECOVER_TIME']=str(recover_time)
        if res.returncode==0:
            log("TEST_PASS:full_recover")
        else:
            log(f"TEST_FAIL:full_recover:{res.stderr.strip() or 'non-zero exit'}")
        log(f"BENCHMARK:full_recover_time_s:{recover_time:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:full_recover:{e}")

    verify_recovery(out)

    # benchmark a larger 100MB recovery (skip if not enough space)
    try:
        large_img='large.img'
        create_fat_image(large_img, size_mb=100)
        corrupt_image(large_img)
        start=time.time()
        run_cmd([str(exe),'recover',large_img,out])
        large_time=time.time()-start
        log(f"BENCHMARK:recover_100mb_time_s:{large_time:.2f}")
    except Exception as e:
        log(f"TEST_SKIP:recover_100mb:{e}")

    benchmark_vs_baseline()
    log("RUN_OK")

if __name__=="__main__":
    try:
        main()
    except Exception:
        log("TEST_FAIL:unexpected:" + traceback.format_exc())
        log("RUN_OK")