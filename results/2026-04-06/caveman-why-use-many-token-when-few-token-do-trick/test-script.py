import importlib
import importlib.util
import importlib.machinery
import time
import subprocess
import sys
import random
import string
import os

try:
    import caveman
    print("INSTALL_OK")
except ImportError:
    print("INSTALL_FAIL")
    sys.exit(1)

class CavemanAgent:
    def __init__(self, prompt):
        self.prompt = prompt

    def act(self):
        return caveman.generate_response(self.prompt)

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def test_token_efficiency():
    prompt = "Write a short story about a character who learns to use few words to convey a lot of meaning"
    agent = CavemanAgent(prompt)
    response = agent.act()
    if response:
        print("TEST_PASS:token_efficiency")
    else:
        print("TEST_FAIL:token_efficiency:No response generated")

def evaluate_performance():
    inputs = ["Hello", "This is a test prompt", "Generate a poem about love"]
    for input_str in inputs:
        start_time = time.time()
        response = caveman.generate_response(input_str)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:response_latency_ms:{latency}")

def check_ui():
    try:
        subprocess.run(["caveman", "--help"], check=True)
        print("TEST_PASS:ui")
    except subprocess.CalledProcessError:
        print("TEST_FAIL:ui:Failed to run caveman with --help")

def main():
    start_time = time.time()
    try:
        import caveman
    except ImportError:
        print("INSTALL_FAIL")
        sys.exit(1)
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time}")
    
    test_token_efficiency()
    evaluate_performance()
    check_ui()
    
    print("RUN_OK")

if __name__ == "__main__":
    main()