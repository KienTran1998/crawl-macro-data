import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
JSON_OUTPUT = os.path.join(DATA_DIR, "commodity_prices.json")

# FRED Series IDs for Commodity Prices (Monthly data)
# Nguồn: Federal Reserve Economic Data (FRED)
COMMODITIES = {
    # Năng lượng / Energy
    "DCOILWTICO": {
        "name": "Crude Oil - WTI",
        "category": "Energy",
        "unit": "USD per Barrel"
    },
    "DCOILBRENTEU": {
        "name": "Crude Oil - Brent",
        "category": "Energy", 
        "unit": "USD per Barrel"
    },
    "PNGASEUUSDM": {
        "name": "Natural Gas - Europe",
        "category": "Energy",
        "unit": "USD per Million BTU"
    },
    
    # Kim loại / Metals
    "PCOPPUSDM": {
        "name": "Copper",
        "category": "Metals",
        "unit": "USD per Metric Ton"
    },
    "WPU101": {
        "name": "Steel - Iron and Steel (PPI)",
        "category": "Metals",
        "unit": "Index (PPI)"
    },
    
    # Nông sản / Agriculture
    "PWHEAMTUSDM": {
        "name": "Wheat",
        "category": "Agriculture",
        "unit": "USD per Metric Ton"
    },
    "PMAIZMTUSDM": {
        "name": "Maize (Corn)",
        "category": "Agriculture",
        "unit": "USD per Metric Ton"
    },
    "PSOYBUSDQ": {
        "name": "Soybeans",
        "category": "Agriculture",
        "unit": "USD per Metric Ton"
    },
    "PCOFFOTMUSDM": {
        "name": "Coffee",
        "category": "Agriculture",
        "unit": "USD per Kilogram"
    },
    "PSUGAISAUSDM": {
        "name": "Sugar",
        "category": "Agriculture", 
        "unit": "USD per Kilogram"
    },
    "PRICENPUSDM": {
        "name": "Rice",
        "category": "Agriculture",
        "unit": "USD per Metric Ton"
    },
    
    # Phân bón / Fertilizer  
    "PCU325311325311P": {
        "name": "Fertilizer - Nitrogenous (Primary Products)",
        "category": "Fertilizer",
        "unit": "Index (PPI)"
    }
}


def fetch_commodity_data(series_id, commodity_info, start_year=2020):
    """
    Lấy dữ liệu commodity từ FRED API.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV data  
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Column names: observation_date, {series_id}
        df.columns = ['date', 'value']
        
        # Filter data từ start_year
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'].dt.year >= start_year]
        
        # Convert to list of dicts
        records = []
        for _, row in df.iterrows():
            if pd.notna(row['value']) and row['value'] != '.':  # Chỉ lấy data không null
                records.append({
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "year": row['date'].year,
                    "month": row['date'].month,
                    "value": float(row['value']),
                    "commodity": commodity_info["name"],
                    "category": commodity_info["category"],
                    "unit": commodity_info["unit"],
                    "series_id": series_id
                })
        
        return records
    
    except Exception as e:
        print(f"   ❌ Lỗi khi tải {series_id}: {e}")
        return []


def main():
    print("--- Commodity Prices Scraper (FRED) ---\n")
    
    all_data = []
    
    for series_id, commodity_info in COMMODITIES.items():
        print(f"📥 Đang tải {commodity_info['name']} ({commodity_info['category']})...")
        
        data = fetch_commodity_data(series_id, commodity_info)
        
        if data:
            all_data.extend(data)
            print(f"   ✅ Đã lấy {len(data)} bản ghi")
        else:
            print(f"   ⚠️  Không có dữ liệu")
    
    # Sắp xếp theo category, commodity, date
    all_data.sort(key=lambda x: (x["category"], x["commodity"], x["date"]))
    
    # Chuẩn bị output
    output_structure = {
        "source": "Federal Reserve Economic Data (FRED)",
        "description": "Monthly commodity prices from 2020 onwards",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(all_data),
        "categories": list(set(c["category"] for c in all_data)),
        "commodities": list(set(c["commodity"] for c in all_data)),
        "data": all_data
    }
    
    # Đảm bảo thư mục data tồn tại
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Lưu vào file JSON (ghi đè)
    try:
        with open(JSON_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu {len(all_data)} bản ghi vào {JSON_OUTPUT}")
        
        # Thống kê theo category
        print("\n📊 Thống kê theo danh mục:")
        for category in sorted(output_structure["categories"]):
            count = len([d for d in all_data if d["category"] == category])
            commodities = set([d["commodity"] for d in all_data if d["category"] == category])
            print(f"   - {category}: {len(commodities)} commodities, {count} records")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu: {e}")
    
    print("\n🏁 Hoàn thành!")


if __name__ == "__main__":
    main()
