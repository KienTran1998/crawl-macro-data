import os
import json
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred
from dotenv import load_dotenv
from pathlib import Path

# Setup paths relative to this script
# Script is in: project/scrapers/fred/scraper_fred.py
# Project root is: ../../
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables from project root
load_dotenv(ENV_PATH)

# Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY")
OUTPUT_FILE = DATA_DIR / "vietnam_macro_fred.json"

# Series IDs to fetch
SERIES_IDS = [
    "DEXVND",           # Exchange Rate - Daily
    "VNMCPIALLMINMEI",  # CPI Inflation - Monthly
    "VNMNGDP"           # GDP - Annual
]

def fetch_fred_data(api_key: str, series_ids: list):
    """
    Fetches data for the given series IDs from FRED API.
    """
    if not api_key:
        print("❌ Error: FRED_API_KEY not found in .env file.")
        return None

    print("🚀 Connecting to FRED API...")
    try:
        fred = Fred(api_key=api_key)
    except Exception as e:
        print(f"❌ Error initializing Fred client: {e}")
        return None

    # Calculate start date (365 days ago)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    all_data = {}

    for series_id in series_ids:
        print(f"📥 Fetching series: {series_id}...")
        try:
            # Fetch data
            # observation_start expects string or datetime
            series_data = fred.get_series(series_id, observation_start=start_date)
            
            # Convert to list of dicts
            processed_data = []
            for date, value in series_data.items():
                # Handle NaN/None values
                if pd.isna(value):
                    clean_value = None
                else:
                    clean_value = float(value)
                
                processed_data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "value": clean_value
                })
            
            all_data[series_id] = processed_data
            print(f"   ✅ Retrieved {len(processed_data)} data points.")
            
        except Exception as e:
            print(f"   ❌ Failed to fetch {series_id}: {e}")
            all_data[series_id] = []

    return all_data

def save_to_json(data: dict):
    """
    Saves the data to a JSON file.
    """
    output_structure = {
        "source": "FRED",
        "period": "Last 1 Year",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=4, ensure_ascii=False)
        print(f"💾 Data successfully saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

def main():
    print("--- FRED Macro Data Scraper ---")
    
    if not FRED_API_KEY:
        print("⚠️  Please set FRED_API_KEY in your .env file.")
        return

    data = fetch_fred_data(FRED_API_KEY, SERIES_IDS)
    
    if data:
        save_to_json(data)
    
    print("🏁 Scraper finished.")

if __name__ == "__main__":
    main()
