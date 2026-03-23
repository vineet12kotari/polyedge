"""Quick smoke test — run with: py test_run.py"""
import sys

print("=== PolyEdge Smoke Test ===\n")

# 1. Polymarket API
print("[1] Testing Polymarket API...")
try:
    from src.polymarket import get_markets
    data = get_markets(limit=3)
    print(f"    OK — got {len(data)} markets")
    if data:
        print(f"    Sample: {data[0].get('question','')[:70]}")
except Exception as e:
    print(f"    FAIL: {e}")

# 2. Kalshi API
print("\n[2] Testing Kalshi API...")
try:
    from src.kalshi import get_all_active_markets
    km = get_all_active_markets(max_pages=1)
    print(f"    OK — got {len(km)} markets")
    if km:
        print(f"    Sample: {km[0].get('title','')[:70]}")
except Exception as e:
    print(f"    FAIL: {e}")

# 3. Matcher
print("\n[3] Testing Matcher...")
try:
    from src.matcher import match_score, find_matches
    score = match_score("Will Donald Trump win the 2024 election?", "Trump wins 2024 presidential election")
    print(f"    OK — match score: {score:.1f}")
except Exception as e:
    print(f"    FAIL: {e}")

# 4. Bond scanner (dry run with mock data)
print("\n[4] Testing Bond Scanner (mock)...")
try:
    from src.bond_scanner import annualized_yield
    y = annualized_yield(0.94, 2)
    print(f"    OK — annualized yield at 0.94 / 2 days: {y*100:.0f}%")
except Exception as e:
    print(f"    FAIL: {e}")

# 5. Dashboard import
print("\n[5] Testing Dashboard import...")
try:
    from src.dashboard import console
    console.print("    [green]OK — Rich dashboard loaded[/green]")
except Exception as e:
    print(f"    FAIL: {e}")

# 6. FastAPI import
print("\n[6] Testing API server import...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("server", "api/server.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("    OK — FastAPI app loaded")
except Exception as e:
    print(f"    FAIL: {e}")

print("\n=== Done ===")
