# US Macro Economic Indicators Scraper

## 📊 Tổng Quan

Scraper tự động thu thập các chỉ số kinh tế vĩ mô quan trọng của Mỹ.

- **Nguồn**: FRED (Federal Reserve Economic Data)
- **Chỉ số**: Fed Funds Rate, US 10Y Yield, DXY Index
- **Thời gian**: 2020-2025 (5 năm dữ liệu)
- **Tổng records**: ~3,057

**Trạng thái**: ✅ Hoàn thành và production ready

---

## 🚀 Cách Sử Dụng

```bash
cd scrapers/us_macro
python3 scraper.py
```

Output: `data/us_macro_data.json`

---

## 📁 Cấu Trúc Dữ Liệu

### 3 Chỉ Số

1. **Fed Funds Rate** - Lãi suất chính sách của FED
   - FRED Series: `FEDFUNDS`
   - Frequency: Monthly
   - Unit: Percent

2. **US 10Y Yield** - Lợi suất trái phiếu chính phủ Mỹ kỳ hạn 10 năm
   - FRED Series: `DGS10`
   - Frequency: Daily
   - Unit: Percent

3. **DXY** - Chỉ số Dollar Mỹsớ dollar-weighted
   - FRED Series: `DTWEXBGS` (Trade Weighted U.S. Dollar Index)
   - Frequency: Daily
   - Unit: Index (Base = 100)

### Format JSON

```json
{
  "metadata": {
    "description": "US Macro Economic Indicators",
    "indicators": ["fed_funds_rate", "us_10y_yield", "dxy"],
    "sources": ["FRED"],
    "period": "2020-01-01 to 2025-12-25",
    "total_records": 3057,
    "last_updated": "2025-12-25 22:55:51"
  },
  "data": [
    {
      "indicator": "fed_funds_rate",
      "date": "2020-01-01",
      "value": 1.55,
      "source": "FRED"
    },
    ...
  ]
}
```

### Các Trường Dữ Liệu

| Trường | Mô Tả |
|--------|-------|
| `indicator` | Tên chỉ số (fed_funds_rate, us_10y_yield, dxy) |
| `date` | Ngày (YYYY-MM-DD) |
| `value` | Giá trị |
| `source` | Nguồn dữ liệu (FRED) |

---

## 🔧 Kỹ Thuật

### Dependencies
- `pandas_datareader`: Để truy cập FRED API
- `pandas`: Data manipulation
- `yfinance`: (Dự phòng, không dùng do API issues)

### Tại sao dùng FRED thay vì Yahoo Finance?

1. **Độ tin cậy cao**: FRED là nguồn chính thức từ Federal Reserve
2. **Dữ liệu đầy đủ**: Yahoo Finance API thường gặp vấn đề với một số symbols
3. **Miễn phí & ổn định**: Không cần API key, truy cập trực tiếp

### Logic

1. Import `pandas_datareader`
2. For each indicator, gọi `pdr.DataReader(series_id, 'fred', start, end)`
3. Parse DataFrame → flat JSON records
4. Lưu vào file

---

## ✅ Verify Dữ Liệu

```bash
# Kiểm tra tổng số records
cat data/us_macro_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'Records: {len(data[\"data\"])}')"

# Xem metadata
cat data/us_macro_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(json.dumps(data['metadata'], indent=2))"

# Kiểm tra dữ liệu mới nhất
tail -n 30 data/us_macro_data.json
```

**Kết quả mong đợi**: ~3,057 records

---

## 📊 Dữ Liệu Mẫu (2025)

### Fed Funds Rate (Tháng 10/2024)
- Value: 4.83%

### US 10Y Yield (25/12/2024)
- Value: ~4.5-4.6%

### DXY Index (25/12/2024)
- Value: ~107-108

*(Số liệu thực tế sẽ cập nhật theo thời gian thực)*

---

## 🔄 Cập Nhật Dữ Liệu

Chạy lại scraper để lấy dữ liệu mới nhất:

```bash
python3 scraper.py
```

FRED cập nhật:
- **Fed Funds Rate**: Hàng tháng (sau mỗi cuộc họp FOMC)
- **US 10Y Yield**: Hàng ngày (business days)
- **DXY**: Hàng ngày (business days)

---

## 📈 Use Cases

1. **Phân tích vĩ mô**: Theo dõi chính sách tiền tệ FED
2. **Dự báo thị trường**: Mối quan hệ giữa lãi suất và chứng khoán
3. **Forex trading**: DXY ảnh hưởng đến tỷ giá các đồng tiền
4. **Risk management**: US 10Y yield là proxy cho risk-free rate

---

*Version: 1.0 - Production Ready*  
*Last Updated: 2025-12-25*
