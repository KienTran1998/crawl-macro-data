#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper for US Macro Economic Indicators
- Fed Funds Rate (from FRED)
- US 10Y Treasury Yield (from Yahoo Finance)
- DXY Dollar Index (from Yahoo Finance)
"""

import yfinance as yf
import pandas as pd
from pandas_datareader import data as pdr
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configuration
OUTPUT_FILE = "data/us_macro_data.json"
START_DATE = "2020-01-01"  # 5年分のdata
END_DATE = datetime.now().strftime("%Y-%m-%d")

# Data sources
YAHOO_SYMBOLS = {
    # DXY removed due to Yahoo Finance API issues - using FRED instead
}

FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",  # Federal Funds Effective Rate
    "us_10y_yield": "DGS10",       # 10-Year Treasury Constant Maturity Rate
    "dxy": "DTWEXBGS"              # Trade Weighted U.S. Dollar Index: Broad, Goods and Services
}


def fetch_yahoo_data(symbol: str, name: str) -> List[Dict[str, Any]]:
    """
    Fetch data from Yahoo Finance using yfinance.
    """
    print(f"\n📊 Fetching: {name} ({symbol})")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=START_DATE, end=END_DATE)
        
        if df.empty:
            print(f"   ⚠️  No data available for {symbol}")
            return []
        
        # Convert to records
        records = []
        for date, row in df.iterrows():
            records.append({
                'indicator': name,
                'date': date.strftime("%Y-%m-%d"),
                'value': round(float(row['Close']), 4),
                'source': 'Yahoo Finance'
            })
        
        print(f"   ✓ Extracted {len(records)} records")
        return records
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def fetch_fred_data(series_id: str, name: str) -> List[Dict[str, Any]]:
    """
    Fetch data from FRED using pandas_datareader.
    """
    print(f"\n📊 Fetching: {name} ({series_id})")
    
    try:
        df = pdr.DataReader(series_id, 'fred', START_DATE, END_DATE)
        
        if df.empty:
            print(f"   ⚠️  No data available for {series_id}")
            return []
        
        # Convert to records
        records = []
        for date, value in df[series_id].items():
            if pd.notna(value):
                records.append({
                    'indicator': name,
                    'date': date.strftime("%Y-%m-%d"),
                    'value': round(float(value), 4),
                    'source': 'FRED'
                })
        
        print(f"   ✓ Extracted {len(records)} records")
        return records
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def scrape_all_data() -> Dict[str, Any]:
    """
    Main scraping function.
    """
    print("=" * 60)
    print("US MACRO DATA SCRAPER")
    print("=" * 60)
    print(f"Period: {START_DATE} to {END_DATE}")
    
    all_data = []
    
    # Fetch Yahoo Finance data
    print("\n📡 Fetching from Yahoo Finance...")
    for key, symbol in YAHOO_SYMBOLS.items():
        records = fetch_yahoo_data(symbol, key)
        all_data.extend(records)
    
    # Fetch FRED data
    print("\n📡 Fetching from FRED...")
    for key, series_id in FRED_SERIES.items():
        records = fetch_fred_data(series_id, key)
        all_data.extend(records)
    
    # Create summary
    result = {
        'metadata': {
            'description': 'US Macro Economic Indicators',
            'indicators': list(YAHOO_SYMBOLS.keys()) + list(FRED_SERIES.keys()),
            'sources': ['Yahoo Finance', 'FRED'],
            'period': f"{START_DATE} to {END_DATE}",
            'total_records': len(all_data),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        'data': all_data
    }
    
    return result


def main():
    """
    Main execution function.
    """
    try:
        # Scrape data
        result = scrape_all_data()
        
        # Save to JSON
        print(f"\n💾 Saving data to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ SCRAPING COMPLETED")
        print("=" * 60)
        print(f"Total records: {result['metadata']['total_records']}")
        print(f"Output file: {OUTPUT_FILE}")
        
        # Display summary by indicator
        print("\n📊 Summary by indicator:")
        df = pd.DataFrame(result['data'])
        summary = df.groupby('indicator').size()
        for indicator, count in summary.items():
            print(f"   - {indicator}: {count} records")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
