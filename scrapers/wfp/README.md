# WFP Macro Data Scraper

Scraper để lấy các chỉ số kinh tế vĩ mô từ World Food Programme (WFP) thông qua HDX CKAN API.

## Chỉ số được theo dõi

- **Inflation / Economic Indicators**: Market Monitor, Economic Explorer
- **Food Prices**: Global Food Prices, Food Prices
- **Exchange Rates**: Tỷ giá chợ đen/thực tế từ các file Market

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install aiohttp pandas
```

Hoặc từ thư mục root:
```bash
pip install -r ../../requirements.txt
```

## Sử dụng

```bash
python scraper_wfp.py
```

## Cách hoạt động

1. **Search Strategy**: Tìm kiếm dataset WFP trên HDX API với các keywords:
   - "Market Monitor"
   - "Economic Explorer"
   - "Global Food Prices"
   - "Food Prices"
   - "Inflation"
   - "Exchange Rate"
   - "Market"

2. **Resource Extraction**: Tự động lọc và chọn file CSV/JSON tốt nhất:
   - Ưu tiên CSV > JSON > XLSX
   - Loại bỏ file metadata/readme
   - Chọn dataset mới nhất (sort by metadata_modified desc)

3. **Data Fetching**: Tải và parse file CSV:
   - Chỉ đọc 1000 dòng đầu để tránh memory issue
   - Tự động detect các cột quan trọng (price, inflation, exchange rate)

4. **Indicator Extraction**: Extract các chỉ số từ dữ liệu:
   - Giá cả (Price)
   - Lạm phát (Inflation)
   - Tỷ giá (Exchange Rate)
   - Thông tin địa lý (Country/Region)
   - Thời gian (Period)

## Output

Dữ liệu được lưu vào `data/wfp_macro_data.json` với format:

```json
{
    "last_updated": "YYYY-MM-DD HH:MM:SS",
    "total_datasets": 5,
    "indicators": [
        {
            "dataset": "WFP Market Monitor - November 2024",
            "extracted_at": "2024-12-04 00:00:00",
            "resource_url": "https://...",
            "resource_name": "market_monitor.csv",
            "resource_format": "CSV",
            "indicators": {
                "price_wheat": 250.5,
                "inflation_rate": 5.2,
                "exchange_rate_usd": 25000,
                "location_country": "Vietnam",
                "period": "2024-11"
            },
            "metadata": {
                "total_rows": 1000,
                "columns": ["country", "commodity", "price", ...],
                "price_columns": ["price", "cost"],
                "inflation_columns": ["inflation_rate"],
                "exchange_rate_columns": ["exchange_rate"]
            }
        }
    ]
}
```

## API Endpoint

- **Base URL**: `https://data.humdata.org/api/3/action`
- **Search Action**: `package_search`
- **Filter**: `organization:wfp` (bắt buộc)
- **Sort**: `metadata_modified desc` (lấy dữ liệu mới nhất)

## Tùy chỉnh

### Thêm keywords mới

Chỉnh sửa `MACRO_KEYWORDS` trong `scraper_wfp.py`:

```python
MACRO_KEYWORDS = [
    "Market Monitor",
    "Your New Keyword",
    ...
]
```

### Điều chỉnh số dòng đọc

Thay đổi `max_rows` trong hàm `fetch_csv_data()`:

```python
df = await fetch_csv_data(resource_info["url"], session, max_rows=5000)
```

## Lưu ý

- API không yêu cầu authentication cho dữ liệu công khai
- Script tự động delay 2 giây giữa các request để tránh rate limit
- Chỉ đọc 1000 dòng đầu của mỗi file để tránh memory issue
- Dữ liệu được sort theo `metadata_modified desc` để luôn lấy dataset mới nhất
