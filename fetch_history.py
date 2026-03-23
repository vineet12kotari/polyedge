"""
Entry point: python fetch_history.py
Fetches resolved Polymarket markets and saves to data/resolved_markets.json.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from src.fetch_history import main

if __name__ == "__main__":
    main()
