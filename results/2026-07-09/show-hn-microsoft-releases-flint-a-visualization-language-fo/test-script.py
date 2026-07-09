import subprocess
import sys
import time
import tracemalloc
import matplotlib.pyplot as plt
import networkx as nx

def install_pkg(pkg):
    subprocess.run(['apk', 'add', '--no-cache', pkg], check=False)
    print(f"INSTALL_OK: {pkg}")

def install_flint():
    try:
        subprocess.run(['pip', 'install', 'flint'], check=False)
        print("INSTALL_OK: flint")
    except Exception as e:
        print(f"INSTALL_FAIL: flint - {str(e)}")

def install_graphviz():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'graphviz'], check=False)
        subprocess.run(['pip', 'install', 'graphviz'], check=False)
        print("INSTALL_OK: graphviz")
    except Exception as e:
        print(f"INSTALL_FAIL: graphviz - {str(e)}")

def test_plot_simple_chart():
    try:
        import flint
        import matplotlib.pyplot as plt
        start_time = time.time()
        plt.plot([1, 2, 3, 4, 5])
        plt.show(block=False)
        plt.pause(0.1)
        plt.close()
        end_time = time.time()
        print(f"BENCHMARK:plot_time_s:{end_time - start_time}")
        print(f"TEST_PASS:plot_simple_chart")
    except Exception as e:
        print(f"TEST_FAIL:plot_simple_chart:{str(e)}")

def test_rendering_speed_flint_vs_graphviz():
    try:
        import flint
        import graphviz
        import time
        start_time = time.time()
        # Create a simple graph
        G = nx.Graph()
        G.add_node("A")
        G.add_node("B")
        G.add_edge("A", "B")
        flint.render(G)
        flint_time = time.time() - start_time
        start_time = time.time()
        graphviz.render(G, format="png")
        graphviz_time = time.time() - start_time
        print(f"BENCHMARK:flint_render_time_s:{flint_time}")
        print(f"BENCHMARK:graphviz_render_time_s:{graphviz_time}")
        print(f"BENCHMARK:vs_flint_graphviz_time_ratio:{flint_time / graphviz_time}")
        print(f"TEST_PASS:rendering_speed")
    except Exception as e:
        print(f"TEST_FAIL:rendering_speed:{str(e)}")

def test_dijkstra_visualization():
    try:
        import flint
        import networkx as nx
        import time
        start_time = time.time()
        # Create a graph with Dijkstra's algorithm
        G = nx.Graph()
        G.add_node("A")
        G.add_node("B")
        G.add_node("C")
        G.add_edge("A", "B", weight=1)
        G.add_edge("B", "C", weight=2)
        G.add_edge("A", "C", weight=3)
        flint.render(G, layout="spring")
        dijkstra_time = time.time() - start_time
        print(f"BENCHMARK:dijkstra_time_s:{dijkstra_time}")
        print(f"TEST_PASS:dijkstra_visualization")
    except Exception as e:
        print(f"TEST_FAIL:dijkstra_visualization:{str(e)}")

def main():
    install_pkg("git")
    install_flint()
    install_graphviz()
    test_plot_simple_chart()
    test_rendering_speed_flint_vs_graphviz()
    test_dijkstra_visualization()
    tracemalloc.start()
    import flint
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}")
    tracemalloc.stop()
    start_time = time.time()
    import flint
    import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{import_time * 1000}")
    print(f"RUN_OK")

if __name__ == "__main__":
    main()