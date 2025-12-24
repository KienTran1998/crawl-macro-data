import json
from collections import Counter
import os

# Load data
FILE_PATH = "scrapers/tradingeconomics/data/vietnam_te_latest.json"

def analyze():
    if not os.path.exists(FILE_PATH):
        print("File not found.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = json.load(f)

    data = content.get("data", {})
    total = len(data)
    
    print(f"=== TỔNG QUAN ===")
    print(f"Tổng số chỉ số: {total}")
    print(f"Nguồn: {content.get('source')}")
    print(f"Cập nhật ngày: {content.get('generated_at')}")
    print("-" * 30)

    # 1. Phân tích theo Danh mục (Category)
    categories = [item['category'] for item in data.values()]
    cat_counts = Counter(categories)
    
    print(f"=== PHÂN BỐ THEO DANH MỤC ===")
    for cat, count in cat_counts.most_common():
        print(f"- {cat.capitalize()}: {count} chỉ số")
    print("-" * 30)

    # 2. Phân tích theo Thời gian (Date)
    dates = [item['date'] for item in data.values()]
    # Extract Year roughly
    years = []
    for d in dates:
        if "/25" in d or "2025" in d: years.append("2025")
        elif "/24" in d or "2024" in d: years.append("2024")
        else: years.append("Khác")
    
    year_counts = Counter(years)
    print(f"=== TÍNH KỊP THỜI (RECENCY) ===")
    for year, count in year_counts.most_common():
        print(f"- Dữ liệu năm {year}: {count} chỉ số")
    print("-" * 30)

    # 3. Các chỉ số quan trọng (Sample Check)
    key_indicators = [
        "gdp_annual_growth_rate", "inflation_rate", "interest_rate", 
        "unemployment_rate", "balance_of_trade", "currency", "stock_market", 
        "foreign_exchange_reserves", "government_debt_to_gdp"
    ]

    print(f"=== CÁC CHỈ SỐ TRỌNG YẾU (SAMPLE) ===")
    print(f"{'Tên chỉ số':<30} | {'Giá trị':<10} | {'Đơn vị':<10} | {'Ngày':<10}")
    print("-" * 70)
    
    found_keys = 0
    for key in key_indicators:
        if key in data:
            item = data[key]
            found_keys += 1
            print(f"{item['name']:<30} | {item['last']:<10} | {item['unit']:<10} | {item['date']:<10}")
        else:
            # Try finding partial match if key mismatch
            pass
    
    print("-" * 30)
    if found_keys > 5:
        print("ĐÁNH GIÁ: Dữ liệu bao phủ tốt các chỉ số vĩ mô quan trọng.")
    else:
        print("ĐÁNH GIÁ: Thiếu một số chỉ số quan trọng.")

if __name__ == "__main__":
    analyze()
