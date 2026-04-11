import subprocess
import time
import tracemalloc
import json
import os

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install json-formatter
try:
    subprocess.run(['pip', 'install', 'json-formatter'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:json-formatter:{str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/callumlocke/json-formatter.git'], check=False)
        subprocess.run(['pip', 'install', '-e', 'json-formatter'], cwd='json-formatter')
    except Exception as e:
        print(f"INSTALL_FAIL:json-formatter:{str(e)}")
        exit()

print("INSTALL_OK")

# Import json-formatter
try:
    import json_formatter
except Exception as e:
    print(f"TEST_FAIL:import_test:{str(e)}")

# Measure import time
start_time = time.time()
import json_formatter
import_time = (time.time() - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Run a minimal functional test
try:
    input_json = '{"key": "value"}'
    output = json_formatter.format_json(input_json)
    if output:
        print("TEST_PASS:format_test")
    else:
        print("TEST_FAIL:format_test:no output")
except Exception as e:
    print(f"TEST_FAIL:format_test:{str(e)}")

# Measure core operation latency
start_time = time.time()
json_formatter.format_json('{"key": "value"}')
end_time = time.time()
latency = (end_time - start_time) * 1000
print(f"BENCHMARK:format_latency_ms:{latency}")

# Measure performance
tracemalloc.start()
json_formatter.format_json('{"key": "value"}')
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Compare vs similar tool
# Assuming similar tool is 'pygments'
try:
    import pygments
except Exception as e:
    print(f"TEST_FAIL:pygments_import_test:{str(e)}")
else:
    start_time = time.time()
    pygments.highlight('{"key": "value"}', pygments.lexers.JsonLexer(), pygments.formatters.TerminalFormatter())
    end_time = time.time()
    pygments_latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:pygments_latency_ms:{pygments_latency}")
    ratio = latency / pygments_latency
    print(f"BENCHMARK:vs_pygments_ratio:{ratio}")

print("RUN_OK")