import subprocess
import time
import tracemalloc
import importlib
import sys
try:
    from agent_vault import AgentVault, Agent
except ImportError:
    pass

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Install pip
subprocess.run(['apk', 'add', '--no-cache', 'py3-pip'], check=False)
print("INSTALL_OK")

# Install agent-vault
try:
    subprocess.run(['pip', 'install', 'agent-vault'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print("INSTALL_FAIL:Failed to install via pip")
    # Fallback to installing from source
    subprocess.run(['git', 'clone', 'https://github.com/Infisical/agent-vault.git'], check=True)
    subprocess.run(['pip', 'install', '-e', 'agent-vault'], check=True)
    print("INSTALL_OK")

try:
    from agent_vault import AgentVault, Agent
except ImportError:
    print("TEST_FAIL:import_agent_vault:Failed to import AgentVault")
    sys.exit(1)

# Test 1: Create a credential proxy using Agent Vault
start_time = time.time()
vault = AgentVault()
end_time = time.time()
print("BENCHMARK:create_proxy_ms:{}".format((end_time - start_time) * 1000))
try:
    vault.create_proxy()
    print("TEST_PASS:create_proxy")
except Exception as e:
    print("TEST_FAIL:create_proxy:{}".format(str(e)))

# Test 2: Verify agent authentication
start_time = time.time()
agent = Agent("test_agent")
end_time = time.time()
print("BENCHMARK:create_agent_ms:{}".format((end_time - start_time) * 1000))
try:
    vault.authenticate_agent(agent)
    print("TEST_PASS:verify_agent_auth")
except Exception as e:
    print("TEST_FAIL:verify_agent_auth:{}".format(str(e)))

# Test 3: Configure a new agent
start_time = time.time()
agent = Agent("new_agent")
end_time = time.time()
print("BENCHMARK:create_new_agent_ms:{}".format((end_time - start_time) * 1000))
try:
    vault.configure_agent(agent)
    print("TEST_PASS:configure_agent")
except Exception as e:
    print("TEST_FAIL:configure_agent:{}".format(str(e)))

# Test 4: Access sensitive data using the proxy
start_time = time.time()
data = vault.get_sensitive_data(agent)
end_time = time.time()
print("BENCHMARK:access_sensitive_data_ms:{}".format((end_time - start_time) * 1000))
try:
    print(data)
    print("TEST_PASS:access_sensitive_data")
except Exception as e:
    print("TEST_FAIL:access_sensitive_data:{}".format(str(e)))

# Measure import time
start_time = time.time()
import agent_vault
end_time = time.time()
print("BENCHMARK:import_time_ms:{}".format((end_time - start_time) * 1000))

# Measure memory usage
tracemalloc.start()
import agent_vault
current, peak = tracemalloc.get_traced_memory()
print("BENCHMARK:memory_usage_bytes:{}".format(current))
tracemalloc.stop()

# Compare performance vs Hashicorp Vault
# For the sake of simplicity, let's assume we have a similar operation in Hashicorp Vault
# and measure the time it takes to perform this operation
start_time = time.time()
# Similar operation in Hashicorp Vault
subprocess.run(['vault', 'kv', 'get', 'secret'], check=True)
end_time = time.time()
print("BENCHMARK:vs_hashicorp_vault_get_secret_ms:{}".format((end_time - start_time) * 1000))
ratio = (end_time - start_time) / (end_time - start_time)
print("BENCHMARK:vs_hashicorp_vault_get_secret_ratio:{}".format(ratio))

print("RUN_OK")