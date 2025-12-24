# Macro Indicators Scraper

Scraper tổng hợp để lấy các chỉ số kinh tế vĩ mô từ 3 nguồn và ghi vào **1 file JSON duy nhất**.

## Nguồn dữ liệu

### 1. WFP DATA (Market Level)
- **Source:** HDX CKAN API
- **Metric:** `mp_price` (Market Price)
- **Dimensions:** `cm_name` (Commodity), `adm0_name` (Country), `mp_year` (Time)
- **Period:** 1 năm gần nhất
- **Priority:** Vietnam, fallback: bất kỳ country nào có sẵn

### 2. FAO DATA (National Level)
- **Source:** FAOSTAT API
- **Domains:**
  - `CP`: Consumer Price Indices (Lạm phát)
  - `QCL`: Crops and livestock products (Sản lượng)
- **Period:** 1 năm gần nhất
- **Priority:** Vietnam (country code: 231), fallback: World/Asia

### 3. MARKET DATA (Real-time Global)
- **Source:** Yahoo Finance (via `yfinance`)
- **Tickers:** 
  - `CL=F` (Oil)
  - `HRC=F` (Steel)
  - `ZR=F` (Rice)
- **Period:** 1 tuần gần nhất

## Cài đặt

```bash
pip install aiohttp pandas yfinance
```

Hoặc từ thư mục root:
```bash
pip install -r ../../requirements.txt
```

## Sử dụng

```bash
python scraper_macro.py
```

## Output Format

Tất cả dữ liệu được ghi vào **1 file duy nhất**: `data/macro_indicators.json`

```json
{
    "last_updated": "2025-12-04 00:00:00",
    "total_records": 1500,
    "summary": {
        "wfp": 500,
        "fao_cp": 300,
        "fao_qcl": 400,
        "yahoo_finance": 21
    },
    "data": [
        {
            "source": "WFP",
            "data_type": "market_price",
            "country": "Vietnam",
            "commodity": "Rice",
            "price": 15000,
            "year": 2024,
            "date": "2024-12-01"
        },
        {
            "source": "FAO",
            "data_type": "consumer_price_index",
            "domain": "CP",
            "country": "Vietnam",
            "year": 2024,
            "item": "Consumer Price Index",
            "value": 105.2,
            "unit": "Index"
        },
        {
            "source": "Yahoo Finance",
            "data_type": "market_price",
            "ticker": "CL=F",
            "date": "2024-12-03",
            "close": 75.50
        }
    ]
}
```

## Cấu trúc dữ liệu

Tất cả records trong `data` array có các field chung:
- `source`: "WFP", "FAO", hoặc "Yahoo Finance"
- `data_type`: Loại dữ liệu (market_price, consumer_price_index, crops_livestock)

Các field khác tùy thuộc vào source:
- **WFP**: country, commodity, price, year, date
- **FAO**: domain, country_code, country, year, item, value, unit
- **Yahoo Finance**: ticker, date, close, open, high, low, volume

## Lưu ý

- Dữ liệu được tổng hợp vào 1 file duy nhất để dễ xử lý
- Ưu tiên lấy dữ liệu Vietnam, nếu không có thì tự động fallback sang country khác
- Script tự động delay giữa các request để tránh rate limit
- File được ghi đè mỗi lần chạy (không append)

