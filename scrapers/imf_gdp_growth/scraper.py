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
OUTPUT_FILE = os.path.join(DATA_DIR, "imf_data.json")

# Indicator codes từ IMF API
INDICATORS = {
    "NGDP_RPCH": "Real GDP growth (Annual percent change)",
    "NGDPD": "Gross domestic product, current prices (U.S. dollars, Billions)"
}

# Country codes
COUNTRIES = {
    "CHN": "China",
    "USA": "United States", 
    "EURO": "Euro Area"  # Euro Area code trong IMF là EURO
}



def get_indicator_data(indicator_code):
    """
    Lấy dữ liệu cho một indicator cụ thể từ IMF API.
    """
    url = f"{BASE_URL}/{indicator_code}"
    print(f"📥 Đang tải dữ liệu cho {INDICATORS.get(indicator_code, indicator_code)}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi tải {indicator_code}: {e}")
        return None


def extract_country_data(api_data, indicator_code, indicator_name):
    """
    Trích xuất dữ liệu cho các quốc gia cần thiết.
    """
    results = []
    
    if not api_data or "values" not in api_data:
        return results
    
    indicator_data = api_data["values"].get(indicator_code, {})
    
    for country_code, country_name in COUNTRIES.items():
        country_data = indicator_data.get(country_code, {})
        
        if country_data:
            for year, value in country_data.items():
                # Chỉ lấy dữ liệu từ năm 2020 trở đi
                try:
                    year_int = int(year)
                    if year_int >= 2020 and value is not None:
                        results.append({
                            "country": country_name,
                            "country_code": country_code,
                            "indicator": indicator_name,
                            "indicator_code": indicator_code,
                            "year": year_int,
                            "value": float(value)
                        })
                except (ValueError, TypeError):
                    continue
    
    return results


def main():
    print("--- IMF GDP & Growth Data Scraper (API) ---\n")
    
    all_data = []
    
    # Lấy dữ liệu cho từng indicator
    for ind_code, ind_name in INDICATORS.items():
        api_data = get_indicator_data(ind_code)
        
        if api_data:
            country_data = extract_country_data(api_data, ind_code, ind_name)
            all_data.extend(country_data)
            print(f"   ✅ Đã lấy {len(country_data)} bản ghi")
        else:
            print(f"   ⚠️  Không có dữ liệu cho {ind_name}")
    
    # Sắp xếp theo quốc gia, chỉ số, năm
    all_data.sort(key=lambda x: (x["country"], x["indicator_code"], x["year"]))
    
    # Chuẩn bị output
    output_structure = {
        "source": "IMF World Economic Outlook API",
        "base_url": BASE_URL,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": "GDP data for China, United States, and Euro Area from 2020 onwards",
        "total_records": len(all_data),
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
    
    print("\n🏁 Hoàn thành!")
    
    # In một vài mẫu dữ liệu
    if all_data:
        print("\n📋 Mẫu dữ liệu:")
        for record in all_data[:5]:
            print(f"  - {record['country']} | {record['indicator'][:30]}... | {record['year']}: {record['value']}")


if __name__ == "__main__":
    main()
