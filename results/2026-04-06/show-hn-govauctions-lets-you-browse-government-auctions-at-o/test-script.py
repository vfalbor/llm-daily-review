import importlib
import importlib.metadata
import json
import os
import requests
import subprocess
import sys
import time
from unittest import skipIf

def pip_install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL")

def test_import_time(package):
    start_time = time.time()
    importlib.import_module(package)
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

def test_govauctions_api():
    try:
        response = requests.get("https://www.govauctions.app/")
        response.raise_for_status()
        print("TEST_PASS:gov_auctions_api")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:gov_auctions_api:{e}")

def test_search_items():
    try:
        response = requests.get("https://www.govauctions.app/search", params={"q": "cars"})
        response.raise_for_status()
        print("TEST_PASS:search_items")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:search_items:{e}")

def test_auction_times():
    try:
        response = requests.get("https://www.govauctions.app/auctions")
        response.raise_for_status()
        auction_times = response.json()
        for auction in auction_times:
            if "time" not in auction:
                print(f"TEST_FAIL:auction_times:time not found in {auction}")
                break
        else:
            print("TEST_PASS:auction_times")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:auction_times:{e}")

def test_browse_auctions():
    try:
        response = requests.get("https://www.govauctions.app/auctions")
        response.raise_for_status()
        auctions = response.json()
        for auction in auctions:
            if "country" not in auction:
                print(f"TEST_FAIL:browse_auctions:country not found in {auction}")
                break
        else:
            print("TEST_PASS:browse_auctions")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:browse_auctions:{e}")

def main():
    try:
        pip_install("requests")
        test_import_time("requests")
        test_govauctions_api()
        test_search_items()
        test_auction_times()
        test_browse_auctions()
    except Exception as e:
        print(f"TEST_FAIL:main:{e}")
    finally:
        print("RUN_OK")

if __name__ == "__main__":
    main()