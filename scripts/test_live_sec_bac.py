"""Script to make REAL live SEC EDGAR API requests for multiple tickers."""

import json
from agent.tools.edgar import get_financial_statements, lookup_cik_by_ticker

def test_ticker(ticker):
    print(f"\n=== EXECUTING REAL LIVE SEC EDGAR API CALL FOR {ticker} ===")
    cik = lookup_cik_by_ticker(ticker)
    print(f"Mapped Ticker {ticker} -> CIK {cik}")
    
    res_json_str = get_financial_statements(ticker, "all")
    res_data = json.loads(res_json_str)
    
    print("Status:", res_data.get("status"))
    print("Entity Name from SEC EDGAR:", res_data.get("entity_name"))
    print("CIK:", res_data.get("cik"))
    
    metrics = res_data.get("metrics", {})
    if "Revenues" in metrics:
        print(f"Real SEC EDGAR Revenue Data for {ticker}:")
        for item in metrics["Revenues"][:3]:
            print(f"  • FY{item.get('fy')}: ${item.get('val') / 1e9:,.2f} Billion (Filed: {item.get('filed')})")

def main():
    for t in ["GOOGL", "BAC", "JPM", "AAPL"]:
        test_ticker(t)

if __name__ == "__main__":
    main()
