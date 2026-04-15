import subprocess
import time
import tracemalloc
import importlib.util
import random

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone and install Chrome skills
subprocess.run(['git', 'clone', 'https://github.com/ChromeDevTools/skills.git'], check=False)
subprocess.run(['pip', 'install', '-e', 'skills'], check=False)

try:
    # Import Chrome skills
    tracemalloc.start()
    start_time = time.time()
    spec = importlib.util.spec_from_file_location("skills", "skills/skills/__init__.py")
    skills = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skills)
    import_time = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
    print(f"BENCHMARK:import_memory_mb:{peak/10**6:.2f}")

    # Run a minimal functional test with synthetic data
    start_time = time.time()
    skills.run_with_default_query("Test Query")
    latency = time.time() - start_time
    print(f"BENCHMARK:ai_prompt_latency_ms:{latency*1000:.2f}")

    # Compare performance with existing tools like LangChain, CrewAI
    # Install LangChain
    subprocess.run(['pip', 'install', 'langchain'], check=False)
    spec = importlib.util.spec_from_file_location("langchain", "langchain/langchain/__init__.py")
    langchain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(langchain)
    start_time = time.time()
    langchain.run_with_default_query("Test Query")
    langchain_latency = time.time() - start_time
    print(f"BENCHMARK:vs_langchain_ai_prompt_ratio:{latency/langchain_latency:.2f}")
    print(f"BENCHMARK:vs_langchain_ai_prompt_ms_diff:{(latency-langchain_latency)*1000:.2f}")

    print("TEST_PASS:ai_prompt_test")

except Exception as e:
    print(f"TEST_FAIL:ai_prompt_test:{str(e)}")

try:
    # Test creating a new skill
    start_time = time.time()
    skills.create_new_skill("Test Skill")
    creation_time = time.time() - start_time
    print(f"BENCHMARK:create_skill_time_ms:{creation_time*1000:.2f}")

    print("TEST_PASS:create_skill_test")

except Exception as e:
    print(f"TEST_FAIL:create_skill_test:{str(e)}")

try:
    # Test loading new skill
    start_time = time.time()
    skills.load_new_skill("Test Skill")
    load_time = time.time() - start_time
    print(f"BENCHMARK:load_skill_time_ms:{load_time*1000:.2f}")

    print("TEST_PASS:load_skill_test")

except Exception as e:
    print(f"TEST_FAIL:load_skill_test:{str(e)}")

print("RUN_OK")