import os
import json
from datetime import date, timedelta
from fredapi import Fred
import pandas as pd
from dotenv import load_dotenv

# Setup paths
OUTPUT_DIR = 'scrapers/fred/data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'vietnam_macro_fred.json')

# Target Series
TARGETS = {
    'CCUSMA02VNM618N': 'Exchange Rate (Monthly - VND/USD)',
    'CPALTT01VNM659N': 'CPI Inflation (% YoY - Monthly)',
    'MKTGDPVNA646NWDB': 'GDP (Annual - USD)'
}

def main():
    load_dotenv()
    api_key = os.getenv('FRED_API_KEY')
    
    if not api_key:
        print("Error: FRED_API_KEY not found in .env file.")
        return

    try:
        fred = Fred(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Fred: {e}")
        return

    # Time Filter: Lấy 5 năm gần nhất để chắc chắn bao phủ cả dữ liệu công bố chậm (như GDP)
    today = date.today()
    start_date = today - timedelta(days=365*5)
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    print(f"--- Starting FRED Scraper ---")
    print(f"Fetching data from: {start_date_str} to present")

    final_data_structure = {
        "source": "FRED (St. Louis Fed)",
        "generated_at": today.strftime('%Y-%m-%d'),
        "data": {}
    }

    for series_id in TARGETS.keys():
        print(f"\nProcessing: {series_id}...")
        
        try:
            # 1. Get Metadata (Thông tin chi tiết về chỉ số)
            info = fred.get_series_info(series_id)
            
            # 2. Get Data (Dữ liệu quan sát)
            series_data = fred.get_series(series_id, observation_start=start_date_str)
            
            observations = []
            latest_date = "N/A"
            
            for timestamp, value in series_data.items():
                date_str = timestamp.strftime('%Y-%m-%d')
                latest_date = date_str # Cập nhật ngày mới nhất
                
                cleaned_value = None
                if pd.notna(value):
                    cleaned_value = float(value)
                
                observations.append({
                    "date": date_str,
                    "value": cleaned_value
                })
            
            # Sắp xếp lại để ngày mới nhất lên đầu (nếu muốn)
            # observations.sort(key=lambda x: x['date'], reverse=True)

            # 3. Construct Enhanced Object
            final_data_structure["data"][series_id] = {
                "metadata": {
                    "title": info.get('title'),
                    "units": info.get('units'),
                    "frequency": info.get('frequency'),
                    "last_updated_by_source": info.get('last_updated'),
                    "notes": info.get('notes', '')[:100] + "..." if info.get('notes') else "" # Cắt ngắn ghi chú
                },
                "latest_value_date": latest_date,
                "observations_count": len(observations),
                "observations": observations
            }
            
            print(f"  -> Title: {info.get('title')}")
            print(f"  -> Latest Date Found: {latest_date}")
            print(f"  -> Units: {info.get('units')}")

        except Exception as e:
            print(f"  -> Error fetching {series_id}: {e}")
            final_data_structure["data"][series_id] = {"error": str(e)}

    # Save Output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data_structure, f, indent=2, ensure_ascii=False)
        
    print(f"\nDone! Data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()