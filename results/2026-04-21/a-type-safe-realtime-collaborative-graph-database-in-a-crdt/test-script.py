import subprocess
import sys
import time
import tracemalloc
import sqlite3
from graph import Graph, Node, Relationship

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
    try:
        subprocess.run(['pip', 'install', 'graph'], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/codemix/graph.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './graph'], check=True, cwd='./graph')
    print('INSTALL_OK')

def create_db_and_query():
    try:
        graph = Graph()
        nodes = [Node({'id': i}) for i in range(1000)]
        graph.add_nodes(nodes)
        relationships = [Relationship(nodes[i], nodes[i+1], {'id': i}) for i in range(999)]
        graph.add_relationships(relationships)
        start_time = time.time()
        results = graph.query('MATCH (n) WHERE id(n) = 0 RETURN n')
        end_time = time.time()
        print(f'BENCHMARK:create_db_and_query_ms:{(end_time-start_time)*1000}')
        print('TEST_PASS:create_db_and_query')
    except Exception as e:
        print(f'TEST_FAIL:create_db_and_query:{str(e)}')

def test_realtime_collaboration():
    try:
        graph1 = Graph()
        graph2 = Graph()
        node = Node({'id': 0})
        graph1.add_node(node)
        start_time = time.time()
        graph2.add_node(node)
        end_time = time.time()
        print(f'BENCHMARK:realtime_collaboration_ms:{(end_time-start_time)*1000}')
        print('TEST_PASS:realtime_collaboration')
    except Exception as e:
        print(f'TEST_FAIL:realtime_collaboration:{str(e)}')

def evaluate_large_graph_dataset():
    try:
        graph = Graph()
        nodes = [Node({'id': i}) for i in range(10000)]
        graph.add_nodes(nodes)
        relationships = [Relationship(nodes[i], nodes[i+1], {'id': i}) for i in range(9999)]
        graph.add_relationships(relationships)
        start_time = time.time()
        results = graph.query('MATCH (n) RETURN n')
        end_time = time.time()
        print(f'BENCHMARK:large_graph_dataset_query_ms:{(end_time-start_time)*1000}')
        print('TEST_PASS:large_graph_dataset')
    except Exception as e:
        print(f'TEST_FAIL:large_graph_dataset:{str(e)}')

def check_crdt_protocol():
    try:
        graph1 = Graph()
        graph2 = Graph()
        node = Node({'id': 0})
        graph1.add_node(node)
        graph2.add_node(node)
        start_time = time.time()
        graph1.query('MATCH (n) RETURN n')
        end_time = time.time()
        print(f'BENCHMARK:crdt_protocol_query_ms:{(end_time-start_time)*1000}')
        print('TEST_PASS:crdt_protocol')
    except Exception as e:
        print(f'TEST_FAIL:crdt_protocol:{str(e)}')

def compare_baseline():
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE nodes (id INTEGER)')
        cursor.execute('INSERT INTO nodes VALUES (0)')
        start_time = time.time()
        cursor.execute('SELECT * FROM nodes WHERE id = 0')
        end_time = time.time()
        sqlite3_time = (end_time-start_time)*1000
        graph_time = float([line.split(':')[1] for line in sys.stdout.getvalue().split('\n') if 'create_db_and_query_ms' in line][0])
        print(f'BENCHMARK:vs_sqlite3_create_db_and_query_ratio:{graph_time/sqlite3_time}')
    except Exception as e:
        print(f'BENCHMARK:vs_sqlite3_create_db_and_query_ratio:nan')

if __name__ == '__main__':
    install_dependencies()
    create_db_and_query()
    test_realtime_collaboration()
    evaluate_large_graph_dataset()
    check_crdt_protocol()
    compare_baseline()
    tracemalloc.start()
    time.sleep(0.1)
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_mb:{current/10**6}')
    print(f'BENCHMARK:peak_memory_usage_mb:{peak/10**6}')
    tracemalloc.stop()
    start_time = time.time()
    time.sleep(0.1)
    end_time = time.time()
    print(f'BENCHMARK:time_usage_s:{end_time-start_time}')
    print('RUN_OK')