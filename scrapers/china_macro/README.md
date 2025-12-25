# China Macro Economic Indicators Scraper

## 📊 Tổng Quan

Scraper tự động thu thập các chỉ số kinh tế vĩ mô của Trung Quốc.

- **Nguồn**: FRED (Federal Reserve Economic Data)
- **Chỉ số**: GDP (Real GDP at Constant Prices)
- **Thời gian**: 2015-2019 (Annual data)
- **Tổng records**: 5

**Trạng thái**: ⚠️ Partial - Chỉ có GDP data, PMI và Credit data không khả dụng qua FRED/World Bank API

---

## 🚀 Cách Sử Dụng

```bash
cd scrapers/china_macro
python3 scraper.py
```

Output: `data/china_macro_data.json`

---

## 📁 Cấu Trúc Dữ Liệu

### Chỉ Số Khả Dụng

1. **GDP** - Real GDP at Constant National Prices
   - FRED Series: `RGDPNACNA666NRUG`
   - Frequency: Annual
   - Unit: Millions of 2017 USD
   - Coverage: 2015-2019

### Chỉ Số Không Khả Dụng

2. **PMI Manufacturing** ❌
   - FRED không có series trực tiếp cho China PMI
   - Nguồn thay thế: NBS website (stats.gov.cn), Trading Economics

3. **Credit Growth / Total Social Financing** ❌
   - FRED không có series cập nhật
   - Nguồn thay thế: PBOC, Trading Economics

### Format JSON

```json
{
  "metadata": {
    "description": "China Macro Economic Indicators",
    "indicators": ["gdp", "gdp_growth"],
    "sources": ["FRED", "World Bank"],
    "period": "2015-01-01 to 2025-12-25",
    "total_records": 5,
    "note": "PMI and detailed credit data not available through these APIs..."
  },
  "data": [
    {
      "indicator": "gdp",
      "date": "2015-01-01",
      "value": 18379366.0,
      "source": "FRED"
    }
  ]
}
```

---

## ⚠️ Hạn Chế

### Dữ Liệu Thiếu
- **PMI**: FRED không republish NBS PMI data
- **Credit Growth**: Cần access trực tiếp PBOC hoặc manual input
- **2020-2025 GDP**: Penn World Table (nguồn của FRED) chưa cập nhật đến 2025

### Giải Pháp Thay Thế

1. **Manual Data Entry**: Cho PMI và Credit từ NBS/PBOC
2. **Trading Economics API** (Paid): Có tất cả 3 chỉ số với 2025 data
3. **Direct NBS Scraping**: Cần handle anti-bot (tương tự customs scraper)

---

## 🔧 Kỹ Thuật

### Dependencies
- `pandas_datareader`: FRED API access
- `pandas`: Data manipulation

### Why FRED?
- Nguồn miễn phí, không cần API key
- Dữ liệu đáng tin cậy (từ Penn World Table)
- Dễ integrate với Python

### Limitation
- Không phải tất cả chỉ số China đều có trên FRED
- Update chậm hơn so với official sources (NBS, PBOC)

---

## ✅ Verify Dữ Liệu

```bash
# Kiểm tra file
cat data/china_macro_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'Records: {len(data[\"data\"])}')"

# Xem metadata
cat data/china_macro_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(json.dumps(data['metadata'], indent=2))"
```

**Kết quả mong đợi**: 5 GDP records (2015-2019)

---

## 📊 Dữ Liệu Mẫu

| Year | GDP (Millions 2017 USD) |
|------|-------------------------|
| 2015 | 18,379,366 |
| 2016 | 19,132,416 |
| 2017 | 19,687,162 |
| 2018 | 19,841,296 |
| 2019 | 20,162,752 |

---

## 🔄 Recommendations

Để có dữ liệu đầy đủ hơn (PMI + Credit + 2025), consider:

1. **Subscribe Trading Economics API** (~$50-200/month)
2. **Manual scraping NBS** (cần implement anti-bot bypass như customs scraper)
3. **Manual data entry** từ các báo cáo NBS/PBOC quarterly

---

*Version: 1.0 - Partial Implementation*  
*Last Updated: 2025-12-25*  
*Note: This scraper provides basic GDP data. For comprehensive China macro data including PMI and credit, additional sources are required.*
