import os
import json
import pandas as pd
from datetime import datetime

# Configuration
DATA_DIR = os.path.dirname(__file__) + "/data"
JSON_OUTPUT = os.path.join(DATA_DIR, "dxy_index.json")

# Indicators
INDICATORS = {
    "DTWEXBGS": {
        "name": "Trade Weighted U.S. Dollar Index: Broad, Goods and Services",
        "category": "Broad Index",
        "unit": "Index 2006=100",
        "description": "A weighted average of the foreign exchange value of the U.S. dollar against the currencies of a broad group of major U.S. trading partners."
    },
    "DTWEXEMEGS": {
        "name": "Trade Weighted U.S. Dollar Index: Emerging Market Economies",
        "category": "Emerging Markets",
        "unit": "Index 2006=100",
        "description": "A weighted average of the foreign exchange value of the U.S. dollar against currencies of emerging market economies."
    },
    "DTWEXAFEGS": {
        "name": "Trade Weighted U.S. Dollar Index: Advanced Foreign Economies, Goods and Services",
        "category": "Major Currencies",
        "unit": "Index 2006=100",
        "description": "A weighted average of the foreign exchange value of the U.S. dollar against currencies of advanced foreign economies (similar to major currencies)."
    }
}


def fetch_data(series_id, info, start_year=2020):
    """
    Lấy dữ liệu trực tiếp từ FRED.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    print(f"📥 Processing {info['name']} from {url}...")
    
    try:
        # Read directly from URL
        df = pd.read_csv(url)
        df.columns = ['date', 'value']
        
        # Filter data from start_year
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'].dt.year >= start_year]
        
        records = []
        for _, row in df.iterrows():
            if pd.notna(row['value']) and row['value'] != '.':
                records.append({
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "year": row['date'].year,
                    "month": row['date'].month,
                    "day": row['date'].day,
                    "value": float(row['value']),
                    "indicator": info["name"],
                    "category": info["category"],
                    "unit": info["unit"],
                    "description": info["description"],
                    "series_id": series_id
                })
        
        print(f"   ✅ Loaded {len(records)} records")
        return records
    
    except Exception as e:
        print(f"   ❌ Error processing {series_id}: {e}")
        return []


def main():
    print("--- DXY Index Scraper (Direct API) ---")
    
    all_data = []
    
    for series_id, info in INDICATORS.items():
        data = fetch_data(series_id, info)
        all_data.extend(data)
    
    # Sort
    all_data.sort(key=lambda x: (x["category"], x["date"]))
    
    # Prepare output
    output_structure = {
        "source": "FRED (Federal Reserve Economic Data)",
        "description": "US Dollar Indices (Broad, Major, Emerging Markets) from 2020 onwards",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(all_data),
        "categories": list(set(c["category"] for c in all_data)),
        "data": all_data
    }
    
    # Save to JSON
    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(all_data)} records to {JSON_OUTPUT}")
        
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
    
    print("\n🏁 Done!")

if __name__ == "__main__":
    main()
