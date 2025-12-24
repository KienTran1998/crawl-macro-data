import os
import json
import time
from datetime import datetime
from fredapi import Fred
import pandas as pd
from dotenv import load_dotenv

# Setup
OUTPUT_DIR = 'scrapers/fred/data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'vietnam_all_indicators.json')
ROOT_CATEGORY_ID = 32841  # Vietnam

def get_all_series_ids(fred, category_id, found_series=None, processed_categories=None):
    """
    Đệ quy tìm tất cả Series ID trong category cha và các category con.
    """
    if found_series is None:
        found_series = {}
    if processed_categories is None:
        processed_categories = set()

    if category_id in processed_categories:
        return found_series
    
    processed_categories.add(category_id)
    print(f"📂 Scanning Category ID: {category_id}...")

    try:
        # 1. Lấy danh sách Series trực tiếp trong Category này
        # limit=1000 để đảm bảo lấy hết (mặc định thường ít hơn)
        series_in_cat = fred.search_by_category(category_id, limit=1000)
        
        if not series_in_cat.empty:
            for _, row in series_in_cat.iterrows():
                sid = row['id']
                if sid not in found_series:
                    found_series[sid] = {
                        'id': sid,
                        'title': row['title'],
                        'units': row['units'],
                        'frequency': row['frequency'],
                        'seasonal_adjustment': row['seasonal_adjustment'],
                        'notes': row.get('notes', '')
                    }

        # 2. Lấy danh sách Category con (Children)
        children = fred.get_child_categories(category_id)
        if not children.empty:
            for child_id in children.index: # children index is the category id
                get_all_series_ids(fred, child_id, found_series, processed_categories)
                
    except Exception as e:
        print(f"⚠️ Error scanning category {category_id}: {e}")

    return found_series

def main():
    load_dotenv()
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print("Error: FRED_API_KEY missing.")
        return

    try:
        fred = Fred(api_key=api_key)
    except Exception as e:
        print(f"Error init: {e}")
        return

    print(f"--- STARTING FULL SCAN FOR CATEGORY {ROOT_CATEGORY_ID} (VIETNAM) ---")
    print("This may take a while depending on the number of sub-categories...")

    # 1. Get All Series Metadata
    all_series_metadata = get_all_series_ids(fred, ROOT_CATEGORY_ID)
    total_series = len(all_series_metadata)
    print(f"\n✅ Found {total_series} unique series. Starting data fetch...")

    final_data = {
        "source": "FRED (Category 32841 - Vietnam)",
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_indicators": total_series,
        "indicators": []
    }

    # 2. Fetch Latest Data for each Series
    count = 0
    for s_id, meta in all_series_metadata.items():
        count += 1
        print(f"[{count}/{total_series}] Fetching: {s_id}...", end='\r')
        
        try:
            # Lấy dữ liệu. sort_order='desc' & limit=1 để lấy cái mới nhất
            # fredapi cho phép truyền kwargs vào underlying request
            # API param: sort_order='desc', limit=1
            series_data = fred.get_series(s_id, sort_order='desc', limit=1)
            
            latest_val = None
            latest_date = None

            if not series_data.empty:
                latest_date = series_data.index[0].strftime('%Y-%m-%d')
                val = series_data.iloc[0]
                latest_val = float(val) if pd.notna(val) else None

            # Add to result
            item = {
                "id": s_id,
                "metadata": {
                    "title": meta['title'],
                    "units": meta['units'],
                    "frequency": meta['frequency'],
                    "seasonal_adjustment": meta['seasonal_adjustment']
                },
                "latest_data": {
                    "date": latest_date,
                    "value": latest_val
                }
            }
            final_data["indicators"].append(item)
            
            # Nhẹ nhàng với API (Rate limit)
            time.sleep(0.1) 

        except Exception as e:
            # Vẫn lưu metadata nhưng data null
            final_data["indicators"].append({
                "id": s_id,
                "metadata": meta,
                "error": str(e),
                "latest_data": None
            })

    # 3. Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"\n\n🎉 Completed! Saved {len(final_data['indicators'])} indicators to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
