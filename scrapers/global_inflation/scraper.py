import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "https://www.imf.org/external/datamapper/api/v1"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "global_inflation.json")

# Indicator: PCPIPCH = Inflation, average consumer prices (Annual percent change)
INDICATOR_CODE = "PCPIPCH"
INDICATOR_NAME = "Inflation, average consumer prices (Annual percent change)"

# Entity codes for global aggregates
ENTITIES = {
    "WEOWORLD": "World",
    "ADVEC": "Advanced economies",
    "OEMDC": "Emerging market and developing economies"
}


def get_inflation_data():
    """
    Lấy dữ liệu lạm phát toàn cầu từ IMF WEO API.
    """
    url = f"{BASE_URL}/{INDICATOR_CODE}"
    print(f"📥 Đang tải dữ liệu lạm phát từ IMF WEO API...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi tải dữ liệu: {e}")
        return None


def extract_entity_data(api_data):
    """
    Trích xuất dữ liệu cho các thực thể toàn cầu (World, Advanced, Emerging).
    """
    results = []
    
    if not api_data or "values" not in api_data:
        return results
    
    indicator_data = api_data["values"].get(INDICATOR_CODE, {})
    
    for entity_code, entity_name in ENTITIES.items():
        entity_data = indicator_data.get(entity_code, {})
        
        if entity_data:
            for year, value in entity_data.items():
                # Chỉ lấy dữ liệu từ năm 2020 trở đi
                try:
                    year_int = int(year)
                    if year_int >= 2020 and value is not None:
                        results.append({
                            "entity": entity_name,
                            "entity_code": entity_code,
                            "indicator": INDICATOR_NAME,
                            "indicator_code": INDICATOR_CODE,
                            "year": year_int,
                            "value": float(value),
                            "unit": "Percent"
                        })
                except (ValueError, TypeError):
                    continue
    
    return results


def main():
    print("--- Global Inflation Trends Scraper (IMF WEO API) ---\n")
    
    # Lấy dữ liệu từ API
    api_data = get_inflation_data()
    
    if not api_data:
        print("❌ Không thể lấy dữ liệu từ API")
        return
    
    # Trích xuất dữ liệu
    all_data = extract_entity_data(api_data)
    
    if not all_data:
        print("⚠️  Không tìm thấy dữ liệu phù hợp")
        return
    
    print(f"✅ Đã trích xuất {len(all_data)} bản ghi")
    
    # Sắp xếp theo thực thể và năm
    all_data.sort(key=lambda x: (x["entity_code"], x["year"]))
    
    # Chuẩn bị output
    output_structure = {
        "source": "IMF World Economic Outlook API (October 2025)",
        "base_url": BASE_URL,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": "Global inflation trends for World, Advanced economies, and Emerging markets from 2020 onwards (including 2025 forecasts)",
        "total_records": len(all_data),
        "entities": list(ENTITIES.values()),
        "data": all_data
    }
    
    # Đảm bảo thư mục data tồn tại
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Lưu vào file JSON (ghi đè)
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu {len(all_data)} bản ghi vào {OUTPUT_FILE}")
        print(f"📊 Tổng số bản ghi: {len(all_data)}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu: {e}")
        return
    
    print("\n🏁 Hoàn thành!")
    
    # In một vài mẫu dữ liệu
    if all_data:
        print("\n📋 Mẫu dữ liệu:")
        # In dữ liệu 2025 của mỗi thực thể
        for entity_code in ENTITIES.keys():
            record_2025 = next((r for r in all_data if r["entity_code"] == entity_code and r["year"] == 2025), None)
            if record_2025:
                print(f"  - {record_2025['entity']} (2025): {record_2025['value']}%")


if __name__ == "__main__":
    main()
