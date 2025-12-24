import json
import os
import re

# Load data
FILE_PATH = "scrapers/tradingeconomics/data/vietnam_te_latest.json"

def analyze_dimensions():
    if not os.path.exists(FILE_PATH):
        print("File not found.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = json.load(f)

    data = content.get("data", {})
    
    print(f"=== PHÂN TÍCH CẤU TRÚC DỮ LIỆU ===")
    print(f"Nguồn dữ liệu: {content.get('source')}")
    print(f"Ngày phân tích: {content.get('generated_at')}")
    print("-" * 40)

    # 1. Số lượng "datasets" / "series" (Chỉ số kinh tế)
    num_indicators = len(data)
    print(f"1. Tổng số chỉ số kinh tế (có thể coi là 'datasets' hoặc 'series' đơn lẻ): {num_indicators}")
    print("   (Lưu ý: Scraper hiện tại chỉ thu thập giá trị MỚI NHẤT của mỗi chỉ số, không phải chuỗi thời gian lịch sử.)")
    print("-" * 40)

    # 2. Số lượng và giá trị duy nhất của các "dimension values"
    unique_categories = set()
    unique_units = set()
    unique_years = set()

    for item in data.values():
        # Category
        if 'category' in item and item['category']:
            unique_categories.add(item['category'])
        
        # Unit
        if 'unit' in item and item['unit']:
            unique_units.add(item['unit'])
            
        # Year from date string (e.g., Dec/25, Q4/24)
        date_str = item.get('date', '')
        match_year = re.search(r'(\d{2})$', date_str) # Matches YY at end (e.g. 25 in Dec/25)
        if match_year:
            full_year = int(match_year.group(1))
            if full_year < 100: # Assuming 2-digit year
                full_year += 2000 if full_year <= datetime.date.today().year % 100 else 1900 # Crude conversion
            unique_years.add(str(full_year))
        elif re.search(r'20(24|25)', date_str): # Match full 2024 or 2025
             match_full_year = re.search(r'20(24|25)', date_str)
             unique_years.add(match_full_year.group(0))


    print(f"2. Phân tích các giá trị chiều (Dimension Values):")
    print(f"   a. Số lượng Danh mục (Category) duy nhất: {len(unique_categories)}")
    print(f"      Các Danh mục: {', '.join(sorted(list(unique_categories)))}")
    print(f"   b. Số lượng Đơn vị (Unit) duy nhất: {len(unique_units)}")
    print(f"      Các Đơn vị: {', '.join(sorted(list(unique_units)))}")
    print(f"   c. Số lượng Năm (Year) duy nhất trong dữ liệu: {len(unique_years)}")
    print(f"      Các Năm: {', '.join(sorted(list(unique_years)))}")
    print("-" * 40)

if __name__ == "__main__":
    import datetime
    analyze_dimensions()
