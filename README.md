# Macro Data Crawlers

Dự án thu thập dữ liệu kinh tế vĩ mô từ các nguồn chính thức (IMF, FRED) để phục vụ phân tích tài chính.

## 📊 Tổng quan các chỉ số (Data Summary)

| STT | Tên Scraper | Nguồn (Source) | Phương pháp (Method) | Thời gian (Range) | Số lượng | Output Path |
|-----|-------------|----------------|----------------------|-------------------|----------|-------------|
| 1 | **IMF GDP & Growth** | IMF WEO API | REST API (JSON) | 2020 - 2030 (Forecast) | 66 | `scrapers/imf_gdp_growth/data/imf_data.json` |
| 2 | **Commodity Prices** | FRED | API (CSV to JSON) | 2020 - 2025 | 3,553 | `scrapers/commodity_prices/data/commodity_prices.json` |
| 3 | **Fed Policy** | FRED | API (CSV to JSON) | 2020 - 2025 | 6,545 | `scrapers/fed_policy/data/fed_policy.json` |
| 4 | **Commodity Cycles** | IMF via FRED | API (CSV to JSON) | 2020 - 2025 | 66 | `scrapers/commodity_cycles/data/commodity_cycles.json` |
| 5 | **DXY Index** | FRED | API (CSV to JSON) | 2020 - 2025 | 4,476 | `scrapers/dxy_index/data/dxy_index.json` |
| 6 | **Global Inflation Trends** | IMF WEO API | REST API (JSON) | 2020 - 2030 (Forecast) | 33 | `scrapers/global_inflation/data/global_inflation.json` |

---

## 📝 Chi tiết dữ liệu (Data Dictionary)

### 1. IMF GDP & Growth
- **Mô tả**: Dữ liệu tăng trưởng GDP thực và GDP danh nghĩa.
- **Nguồn gốc (Source URL)**: [IMF DataMapper](https://www.imf.org/external/datamapper/NGDP_RPCH@WEO/CHN/USA/EURO)
- **API Endpoint**: `https://www.imf.org/external/datamapper/api/v1/{indicator}/{country}`
- **Trường dữ liệu**: `country`, `country_code`, `indicator`, `year`, `value`
- **Ví dụ**:
  ```json
  {"country": "China", "indicator": "Real GDP growth", "year": 2024, "value": 5.0}
  ```

### 2. Commodity Prices
- **Mô tả**: Giá hàng hóa cơ bản (Dầu, Kim loại, Nông sản, Phân bón).
- **Nguồn gốc (Source URL)**: [FRED Commodities](https://fred.stlouisfed.org/tags/series?t=commodities)
- **API Endpoint**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}`
- **Series IDs** (11 commodities):
  - **Energy**: Crude Oil WTI ([`DCOILWTICO`](https://fred.stlouisfed.org/series/DCOILWTICO)), Brent ([`DCOILBRENTEU`](https://fred.stlouisfed.org/series/DCOILBRENTEU)), Natural Gas ([`PNGASEUUSDM`](https://fred.stlouisfed.org/series/PNGASEUUSDM))
  - **Metals**: Copper ([`PCOPPUSDM`](https://fred.stlouisfed.org/series/PCOPPUSDM)), Steel ([`WPU101`](https://fred.stlouisfed.org/series/WPU101))
  - **Agriculture**: Wheat ([`PWHEAMTUSDM`](https://fred.stlouisfed.org/series/PWHEAMTUSDM)), Corn ([`PMAIZMTUSDM`](https://fred.stlouisfed.org/series/PMAIZMTUSDM)), Soybeans ([`PSOYBUSDQ`](https://fred.stlouisfed.org/series/PSOYBUSDQ)), Coffee ([`PCOFFOTMUSDM`](https://fred.stlouisfed.org/series/PCOFFOTMUSDM)), Sugar ([`PSUGAISAUSDM`](https://fred.stlouisfed.org/series/PSUGAISAUSDM))
  - **Fertilizer**: Nitrogenous ([`PCU325311325311P`](https://fred.stlouisfed.org/series/PCU325311325311P))
- **Trường dữ liệu**: `date`, `value`, `commodity`, `category`, `unit`, `series_id`
- **Ví dụ**:
  ```json
  {"date": "2025-12-15", "commodity": "Crude Oil - WTI", "value": 56.97, "unit": "USD per Barrel"}
  ```

### 3. Fed Policy Indicators
- **Mô tả**: Lãi suất điều hành của FED (Lãi suất thực tế & Mục tiêu).
- **Nguồn gốc (Source URL)**: [FRED Interest Rates](https://fred.stlouisfed.org/categories/22)
- **API Endpoint**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}`
- **Series IDs**:
  - Effective Funds Rate: [`DFF`](https://fred.stlouisfed.org/series/DFF)
  - Target Range Upper: [`DFEDTARU`](https://fred.stlouisfed.org/series/DFEDTARU)
- **Trường dữ liệu**: `date`, `value`, `indicator`, `category`, `unit`, `description`
- **Ví dụ**:
  ```json
  {"date": "2025-12-18", "indicator": "Effective Federal Funds Rate", "value": 3.64, "unit": "Percent"}
  ```

### 4. Commodity Cycles
- **Mô tả**: Chỉ số chu kỳ giá hàng hóa toàn cầu.
- **Nguồn gốc (Source URL)**: [IMF Global Price Index (FRED)](https://fred.stlouisfed.org/series/PALLFNFINDEXM)
- **API Endpoint**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=PALLFNFINDEXM`
- **Trường dữ liệu**: `date`, `value`, `indicator`, `category`, `unit`
- **Ví dụ**:
  ```json
  {"date": "2024-12-01", "indicator": "Global Price Index of All Commodities", "value": 166.63, "unit": "Index 2016=100"}
  ```

### 5. DXY Index (US Dollar Index)
- **Mô tả**: Sức mạnh đồng USD so với các nhóm tiền tệ khác nhau.
- **Nguồn gốc (Source URL)**: [FRED Exchange Rate Indices](https://fred.stlouisfed.org/categories/94)
- **API Endpoint**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}`
- **Series IDs (Chi tiết)**:
  - Advanced Foreign Economies: [`DTWEXAFEGS`](https://fred.stlouisfed.org/series/DTWEXAFEGS) (Major Currencies)
  - Emerging Markets: [`DTWEXEMEGS`](https://fred.stlouisfed.org/series/DTWEXEMEGS) (EM Impact)
  - Broad Index: [`DTWEXBGS`](https://fred.stlouisfed.org/series/DTWEXBGS)
- **Trường dữ liệu**: `date`, `value`, `indicator`, `category`, `unit`, `description`, `series_id`
- **Ví dụ**:
  ```json
  {
    "date": "2024-12-20",
    "value": 118.5,
    "indicator": "Trade Weighted U.S. Dollar Index: Emerging Market Economies",
    "category": "Emerging Markets",
    "unit": "Index 2006=100",
    "description": "A weighted average of the foreign exchange value of the U.S. dollar against currencies of emerging market economies."
  }\n  ```

### 6. Global Inflation Trends
- **Mô tả**: Xu hướng lạm phát toàn cầu, bao gồm Thế giới, Các nền kinh tế phát triển, và Các thị trường mới nổi.
- **Nguồn gốc (Source URL)**: [IMF World Economic Outlook - Inflation](https://www.imf.org/external/datamapper/PCPIPCH@WEO/WEOWORLD/ADVEC/OEMDC)
- **API Endpoint**: `https://www.imf.org/external/datamapper/api/v1/PCPIPCH`
- **Entity Codes**:
  - World: [`WEOWORLD`](https://www.imf.org/external/datamapper/PCPIPCH@WEO/WEOWORLD)
  - Advanced economies: [`ADVEC`](https://www.imf.org/external/datamapper/PCPIPCH@WEO/ADVEC)
  - Emerging market and developing economies: [`OEMDC`](https://www.imf.org/external/datamapper/PCPIPCH@WEO/OEMDC)
- **Trường dữ liệu**: `entity`, `entity_code`, `indicator`, `year`, `value`, `unit`
- **Ví dụ**:
  ```json
  {
    "entity": "World",
    "entity_code": "WEOWORLD",
    "indicator": "Inflation, average consumer prices (Annual percent change)",
    "indicator_code": "PCPIPCH",
    "year": 2025,
    "value": 4.2,
    "unit": "Percent"
  }
  ```


---

## 🚀 Cách chạy (How to Run)

1. **Cài đặt môi trường**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Chạy từng Scraper**:
   ```bash
   python scrapers/imf_gdp_growth/scraper.py
   python scrapers/commodity_prices/scraper.py
   python scrapers/fed_policy/scraper.py
   python scrapers/commodity_cycles/scraper.py
   python scrapers/dxy_index/scraper.py
   python scrapers/global_inflation/scraper.py
   ```

3. **Cập nhật tất cả**:
   Các file JSON output sẽ được ghi đè (overwrite) mỗi lần chạy script để đảm bảo dữ liệu mới nhất.

---

## 🗂️ Cấu trúc dự án

```
crawl-macro-data/
├── scrapers/
│   ├── imf_gdp_growth/
│   ├── commodity_prices/
│   ├── fed_policy/
│   ├── commodity_cycles/
│   ├── dxy_index/
│   └── global_inflation/
│       ├── scraper.py
│       └── data/
│           └── global_inflation.json
├── requirements.txt
└── README.md
```

---

## 📦 Cài đặt

1. **Tạo virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# hoặc
.venv\Scripts\activate  # Windows
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

---

## 📋 Dependencies

- `requests` - HTTP requests
- `pandas` - Data processing
- `python-dotenv` - Environment variables
- `crawl4ai` - Web crawling framework (optional)

---

## 📝 Lưu ý

- Mỗi scraper **ghi đè** file JSON mỗi lần chạy
- Dữ liệu được lưu dưới dạng JSON với cấu trúc chuẩn
- Không cần API key cho các nguồn hiện tại
- Tất cả scrapers có thể chạy độc lập
