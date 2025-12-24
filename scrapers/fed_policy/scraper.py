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
JSON_OUTPUT = os.path.join(DATA_DIR, "fed_policy.json")

# FRED Series IDs for Fed Policy Indicators
FED_INDICATORS = {
    "DFF": {
        "name": "Effective Federal Funds Rate",
        "category": "Interest Rate",
        "unit": "Percent",
        "description": "The interest rate at which depository institutions lend reserve balances to other depository institutions overnight"
    },
    "DFEDTARU": {
        "name": "Federal Funds Target Range - Upper Limit",
        "category": "Policy Rate",
        "unit": "Percent",
        "description": "Upper limit of the target range for the federal funds rate"
    },
    "DFEDTARL": {
        "name": "Federal Funds Target Range - Lower Limit",
        "category": "Policy Rate",
        "unit": "Percent",
        "description": "Lower limit of the target range for the federal funds rate"
    }
}


def fetch_fed_data(series_id, indicator_info, start_year=2020):
    """
    Lấy dữ liệu Fed Policy từ FRED API.
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
            if pd.notna(row['value']) and row['value'] != '.':
                records.append({
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "year": row['date'].year,
                    "month": row['date'].month,
                    "day": row['date'].day,
                    "value": float(row['value']),
                    "indicator": indicator_info["name"],
                    "category": indicator_info["category"],
                    "unit": indicator_info["unit"],
                    "description": indicator_info["description"],
                    "series_id": series_id
                })
        
        return records
    
    except Exception as e:
        print(f"   ❌ Lỗi khi tải {series_id}: {e}")
        return []


def main():
    print("--- Fed Policy Indicators Scraper (FRED) ---\n")
    
    all_data = []
    
    for series_id, indicator_info in FED_INDICATORS.items():
        print(f"📥 Đang tải {indicator_info['name']}...")
        
        data = fetch_fed_data(series_id, indicator_info)
        
        if data:
            all_data.extend(data)
            print(f"   ✅ Đã lấy {len(data)} bản ghi")
        else:
            print(f"   ⚠️  Không có dữ liệu")
    
    # Sắp xếp theo category, indicator, date
    all_data.sort(key=lambda x: (x["category"], x["indicator"], x["date"]))
    
    # Chuẩn bị output
    output_structure = {
        "source": "Federal Reserve Economic Data (FRED)",
        "description": "Federal Reserve Policy Indicators from 2020 onwards",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(all_data),
        "categories": list(set(c["category"] for c in all_data)),
        "indicators": list(set(c["indicator"] for c in all_data)),
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
            indicators = set([d["indicator"] for d in all_data if d["category"] == category])
            print(f"   - {category}: {len(indicators)} indicators, {count} records")
        
        # Hiển thị giá trị mới nhất
        print("\n📈 Giá trị mới nhất:")
        for series_id, info in FED_INDICATORS.items():
            series_data = [d for d in all_data if d["series_id"] == series_id]
            if series_data:
                latest = series_data[-1]
                print(f"   - {info['name']}: {latest['value']}% (ngày {latest['date']})")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu: {e}")
    
    print("\n🏁 Hoàn thành!")


if __name__ == "__main__":
    main()
