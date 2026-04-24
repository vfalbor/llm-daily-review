import subprocess
import time
import tracemalloc
import importlib
import sys

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tolaria via pip
try:
    subprocess.run(['pip', 'install', 'tolaria'], check=True)
    INSTALL_MSG = "INSTALL_OK"
except Exception as e:
    INSTALL_MSG = f"INSTALL_FAIL:{e}"

print(INSTALL_MSG)

# Install tolaria via git clone as fallback if pip install fails
if INSTALL_MSG.startswith("INSTALL_FAIL"):
    subprocess.run(['git', 'clone', 'https://github.com/refactoringhq/tolaria.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './tolaria'], cwd='./tolaria', check=True)

# Import tolaria
try:
    import tolaria
except Exception as e:
    print(f"TEST_FAIL:import_tolaria:{e}")
    tolaria = None

# Measure import time
start = time.time()
importlib.import_module('tolaria')
end = time.time()
import_time = (end - start) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Test creating a knowledge base and inserting new notes
if tolaria is not None:
    try:
        knowledge_base = tolaria.KnowledgeBase()
        knowledge_base.create_note("test_note", "This is a test note.")
        start = time.time()
        knowledge_base.create_note("another_test_note", "This is another test note.")
        end = time.time()
        create_note_time = (end - start) * 1000
        print(f"BENCHMARK:create_note_time_ms:{create_note_time}")
        print(f"TEST_PASS:create_knowledge_base")
    except Exception as e:
        print(f"TEST_FAIL:create_knowledge_base:{e}")

# Test editing existing notes with Markdown formatting
if tolaria is not None:
    try:
        knowledge_base = tolaria.KnowledgeBase()
        knowledge_base.create_note("test_note", "This is a test note.")
        start = time.time()
        knowledge_base.edit_note("test_note", "# This is a test note with markdown formatting")
        end = time.time()
        edit_note_time = (end - start) * 1000
        print(f"BENCHMARK:edit_note_time_ms:{edit_note_time}")
        print(f"TEST_PASS:edit_note")
    except Exception as e:
        print(f"TEST_FAIL:edit_note:{e}")

# Test exporting the entire knowledge base to PDF/HTML
if tolaria is not None:
    try:
        knowledge_base = tolaria.KnowledgeBase()
        knowledge_base.create_note("test_note", "This is a test note.")
        start = time.time()
        knowledge_base.export_to_pdf()
        end = time.time()
        export_to_pdf_time = (end - start) * 1000
        print(f"BENCHMARK:export_to_pdf_time_ms:{export_to_pdf_time}")
        print(f"TEST_PASS:export_to_pdf")
    except Exception as e:
        print(f"TEST_FAIL:export_to_pdf:{e}")

# Compare performance vs the most similar baseline tool (Typora)
try:
    start = time.time()
    subprocess.run(['typora', '--help'], check=True)
    end = time.time()
    typora_help_time = (end - start) * 1000
    print(f"BENCHMARK:vs_typora_help_time_ms:{typora_help_time}")
    print(f"BENCHMARK:vs_typora_import_ratio:{import_time / typora_help_time}")
except Exception as e:
    print(f"BENCHMARK:vs_typora_help_time_ms:0")
    print(f"BENCHMARK:vs_typora_import_ratio:0")

# Measure memory usage
tracemalloc.start()
importlib.import_module('tolaria')
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{current}")
tracemalloc.stop()

# Print RUN_OK at the end
print("RUN_OK")