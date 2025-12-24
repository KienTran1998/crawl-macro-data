import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "commodity_prices_yahoo.json")

# Yahoo Finance Tickers for Commodities
# Continuous Futures provide historical + current data (2020-2025)
COMMODITIES = {
    # Năng lượng / Energy
    "CL=F": {
        "name": "Crude Oil - WTI",
        "category": "Energy",
        "unit": "USD per Barrel"
    },
    "BZ=F": {
        "name": "Crude Oil - Brent",
        "category": "Energy",
        "unit": "USD per Barrel"
    },
    
    # Kim loại / Metals
    "HG=F": {
        "name": "Copper",
        "category": "Metals",
        "unit": "USD per Pound"
    },
    "HRC=F": {
        "name": "Steel (Hot-Rolled Coil)",
        "category": "Metals",
        "unit": "USD per Short Ton"
    },
    
    # Nông sản / Agriculture
    "ZR=F": {
        "name": "Rough Rice",
        "category": "Agriculture",
        "unit": "USD per Hundredweight"
    },
    "KC=F": {
        "name": "Coffee",
        "category": "Agriculture",
        "unit": "USD per Pound"
    },
    
    # Phân bón / Fertilizer (ETF/Stock proxy)
    "SOIL": {
        "name": "Global X Fertilizers/Potash ETF",
        "category": "Fertilizer",
        "unit": "USD (ETF Price)"
    },
    "NTR": {
        "name": "Nutrien Ltd (Stock)",
        "category": "Fertilizer",
        "unit": "USD (Stock Price)"
    }
}


def fetch_commodity_data(ticker, commodity_info, start_date="2020-01-01"):
    """
    Lấy dữ liệu commodity từ Yahoo Finance.
    """
    print(f"📥 Đang tải {commodity_info['name']} ({ticker})...")
    
    try:
        # Download data từ Yahoo Finance
        data = yf.download(ticker, start=start_date, progress=False)
        
        if data.empty:
            print(f"   ⚠️  Không có dữ liệu cho {ticker}")
            return []
        
        # Reset index để có cột 'Date'
        data.reset_index(inplace=True)
        
        # Chọn cột cần thiết (Date và Close price)
        records = []
        for _, row in data.iterrows():
            if pd.notna(row['Close']):
                records.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "year": row['Date'].year,
                    "month": row['Date'].month,
                    "day": row['Date'].day,
                    "value": round(float(row['Close']), 2),
                    "commodity": commodity_info["name"],
                    "category": commodity_info["category"],
                    "unit": commodity_info["unit"],
                    "ticker": ticker
                })
        
        print(f"   ✅ Đã lấy {len(records)} bản ghi")
        return records
    
    except Exception as e:
        print(f"   ❌ Lỗi khi tải {ticker}: {e}")
        return []


def main():
    print("--- Commodity Prices Scraper (Yahoo Finance) ---\n")
    
    all_data = []
    
    for ticker, commodity_info in COMMODITIES.items():
        data = fetch_commodity_data(ticker, commodity_info)
        
        if data:
            all_data.extend(data)
    
    # Sắp xếp theo category, commodity, date
    all_data.sort(key=lambda x: (x["category"], x["commodity"], x["date"]))
    
    # Chuẩn bị output
    output_structure = {
        "source": "Yahoo Finance",
        "description": "Daily commodity prices from 2020 onwards (including 2025 data)",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(all_data),
        "categories": sorted(list(set(c["category"] for c in all_data))),
        "commodities": sorted(list(set(c["commodity"] for c in all_data))),
        "data": all_data
    }
    
    # Đảm bảo thư mục data tồn tại
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Lưu vào file JSON (ghi đè)
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_structure, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu {len(all_data)} bản ghi vào {OUTPUT_FILE}")
        
        # Thống kê theo category
        print("\n📊 Thống kê theo danh mục:")
        for category in output_structure["categories"]:
            count = len([d for d in all_data if d["category"] == category])
            commodities = set([d["commodity"] for d in all_data if d["category"] == category])
            print(f"   - {category}: {len(commodities)} commodities, {count:,} records")
        
        # In mẫu dữ liệu 2025
        print("\n📋 Mẫu dữ liệu 2025 (tháng gần nhất):")
        data_2025 = [d for d in all_data if d["year"] == 2025]
        if data_2025:
            # Lấy record mới nhất của mỗi commodity
            latest_by_commodity = {}
            for record in data_2025:
                commodity = record["commodity"]
                if commodity not in latest_by_commodity or record["date"] > latest_by_commodity[commodity]["date"]:
                    latest_by_commodity[commodity] = record
            
            for commodity, record in sorted(latest_by_commodity.items()):
                print(f"   - {commodity}: {record['value']} {record['unit']} ({record['date']})")
        else:
            print("   ⚠️  Chưa có dữ liệu 2025")
        
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu: {e}")
    
    print("\n🏁 Hoàn thành!")


if __name__ == "__main__":
    main()
