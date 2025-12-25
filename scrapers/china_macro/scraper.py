#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper for China Macro Economic Indicators
- GDP Growth
- PMI (Manufacturing)
- Credit Growth / Total Social Financing
"""

import pandas as pd
from pandas_datareader import data as pdr
import json
from datetime import datetime
from typing import Dict, List, Any

# Configuration
OUTPUT_FILE = "data/china_macro_data.json"
START_DATE = "2015-01-01"  # 10年分のdata
END_DATE = datetime.now().strftime("%Y-%m-%d")

# Data sources - Using verified series IDs
FRED_SERIES = {
    "gdp": "RGDPNACNA666NRUG",            # Real GDP at Constant Prices for China (Annual)
    # Note: PMI and Credit data not directly available in FRED
    # Will use World Bank API for additional data
}

WORLD_BANK_INDICATORS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",   # GDP growth (annual %)
}


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


def fetch_worldbank_data(indicator_code: str, name: str) -> List[Dict[str, Any]]:
    """
    Fetch data from World Bank using pandas_datareader.
    """
    print(f"\n📊 Fetching: {name} ({indicator_code})")
    
    try:
        # World Bank data for China (country code: CN)
        df = pdr.DataReader(indicator_code, 'world-bank', start=2010, end=2025, countries=['CN'])
        
        if df.empty:
            print(f"   ⚠️  No data available for {indicator_code}")
            return []
        
        # Convert to records
        records = []
        for date_idx in df.index:
            year = date_idx.year
            value = df.loc[date_idx, 'CN']
            
            if pd.notna(value):
                records.append({
                    'indicator': name,
                    'date': f"{year}-12-31",  # World Bank annual data, use year-end
                    'value': round(float(value), 4),
                    'source': 'World Bank'
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
    print("CHINA MACRO DATA SCRAPER")
    print("=" * 60)
    print(f"Period: {START_DATE} to {END_DATE}")
    
    all_data = []
    all_indicators = list(FRED_SERIES.keys()) + list(WORLD_BANK_INDICATORS.keys())
    
    # Fetch FRED data
    if FRED_SERIES:
        print("\n📡 Fetching from FRED...")
        for key, series_id in FRED_SERIES.items():
            records = fetch_fred_data(series_id, key)
            all_data.extend(records)
    
    # Fetch World Bank data
    if WORLD_BANK_INDICATORS:
        print("\n📡 Fetching from World Bank...")
        for key, indicator_code in WORLD_BANK_INDICATORS.items():
            records = fetch_worldbank_data(indicator_code, key)
            all_data.extend(records)
    
    # Create summary
    result = {
        'metadata': {
            'description': 'China Macro Economic Indicators',
            'indicators': all_indicators,
            'sources': ['FRED', 'World Bank'],
            'period': f"{START_DATE} to {END_DATE}",
            'total_records': len(all_data),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'note': 'PMI and detailed credit data not available through these APIs. Consider manual data entry or alternative sources like Trading Economics.'
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
        if result['data']:
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
