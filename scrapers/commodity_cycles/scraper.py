import os
import json
import pandas as pd
from datetime import datetime

# Configuration
DATA_DIR = os.path.dirname(__file__) + "/data"
JSON_OUTPUT = os.path.join(DATA_DIR, "commodity_cycles.json")

# Indicators
INDICATORS = {
    "PALLFNFINDEXM": {
        "name": "Global Price Index of All Commodities",
        "category": "Commodity Index",
        "unit": "Index 2016=100",
        "description": "IMF Global Price Index of All Commodities, Monthly. Base Year 2016 = 100."
    }
}


def main():
    print("--- Commodity Cycles Scraper (Local CSV) ---")
    
    all_data = []
    series_id = "PALLFNFINDEXM"
    info = INDICATORS[series_id]
    
    csv_file = os.path.join(DATA_DIR, "temp.csv")
    print(f"Reading from: {csv_file}")
    
    try:
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            
            # Column names: observation_date, {series_id}
            # Often FRED CSV has 'observation_date', 'PALLFNFINDEXM'
            # Let's handle dynamic column names or just assume position
            df.columns = ['date', 'value']
            
            # Filter data from 2020
            df['date'] = pd.to_datetime(df['date'])
            df = df[df['date'].dt.year >= 2020]
            
            for _, row in df.iterrows():
                if pd.notna(row['value']) and row['value'] != '.':
                    all_data.append({
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "year": row['date'].year,
                        "month": row['date'].month,
                        "value": float(row['value']),
                        "indicator": info["name"],
                        "category": info["category"],
                        "unit": info["unit"],
                        "series_id": series_id
                    })
            
            print(f"   ✅ Processed {len(all_data)} records")
        else:
             print(f"   ❌ File not found: {csv_file}")
             
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Prepare output
    output_structure = {
        "source": "FRED / IMF",
        "description": "Commodity Cycles Indices from 2020 onwards",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(all_data),
        "data": all_data
    }
    
    # Save to JSON
    try:
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {JSON_OUTPUT}")
        
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
    
    print("Done.")

if __name__ == "__main__":
    main()
