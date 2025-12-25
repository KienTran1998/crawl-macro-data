# China Macro Economic Indicators Scraper (Hybrid)

## 📊 Tổng Quan

Scraper kết hợp (Hybrid) tự động thu thập các chỉ số kinh tế vĩ mô quan trọng của Trung Quốc từ hai nguồn uy tín nhất: **World Bank** (Lịch sử) và **NBS** (Mới nhất).

- **Nguồn**:
  1. **World Bank API**: Dữ liệu lịch sử tin cậy.
  2. **NBS (National Bureau of Statistics of China)**: Dữ liệu thời gian thực (2025).
- **Chỉ số**: GDP Growth, PMI, Investment (Credit Proxy).
- **Thời gian**: 1990 - 2025.
- **Tổng records**: ~39+ (Cập nhật liên tục).

**Trạng thái**: ✅ Production Ready (Hybrid Strategy)

---

## 🚀 Cách Sử Dụng

```bash
cd scrapers/china_macro
python3 scraper.py
```

Output: `data/china_macro_data.json`

---

## 📁 Cấu Trúc Dữ Liệu & Nghiệp Vụ

### 1. GDP Growth (Tăng trưởng GDP)
- **Nguồn Lịch sử (1990-2024)**: lấy từ World Bank API (Indicator: `NY.GDP.MKTP.KD.ZG`).
- **Nguồn 2025**: Scraping trực tiếp từ NBS Press Release (Quý gần nhất).
- **Ý nghĩa**: Đo lường tốc độ tăng trưởng của nền kinh tế lớn thứ 2 thế giới.

### 2. PMI (Purchasing Managers' Index)
- **Nguồn**: NBS Press Release (Latest Month).
- **Chỉ số**: Manufacturing PMI.
- **Ý nghĩa**: Chỉ số dẫn dắt (leading indicator) về sức khỏe ngành sản xuất.
  - `> 50`: Mở rộng.
  - `< 50`: Thu hẹp.

### 3. Credit Growth Proxy (Investment)
- **Nguồn Lịch sử (1990-2024)**: World Bank (Indicator: `NE.GDI.TOTL.KD.ZG` - Gross Capital Formation Growth).
- **Nguồn 2025**: NBS Press Release (Fixed Asset Investment YTD).
- **Tại sao lại dùng chỉ số này làm Credit Growth?**
  - Số liệu "Credit/Loans" chính thức (Total Social Financing) do PBOC phát hành riêng biệt.
  - **Gross Capital Formation** và **Fixed Asset Investment (FAI)** là các chỉ số độ trễ thấp, phản ánh trực tiếp dòng vốn tín dụng chảy vào nền kinh tế thực (đầu tư dự án, mua sắm tài sản).
  - Đây là proxy tiêu chuẩn để đánh giá hiệu quả của chính sách nới lỏng tín dụng.

### Format JSON

```json
{
  "metadata": {
    "description": "China Macro Economic Indicators (Historical + 2025)",
    "sources": ["World Bank", "NBS China"],
    "total_records": 39,
    "last_updated": "2025-12-26 00:08:49"
  },
  "data": [
    {
      "indicator": "gdp_growth",
      "date": "2024-12-31",
      "value": 4.98,
      "unit": "percent",
      "source": "World Bank",
      "note": "Annual GDP Growth"
    },
    {
      "indicator": "pmi_manufacturing",
      "date": "2025-11-30",
      "value": 50.3,
      "unit": "index",
      "source": "NBS",
      "note": "Manufacturing PMI"
    }
  ]
}
```

---

## 🔧 Kỹ Thuật (Hybrid Architecture)

Scraper sử dụng chiến lược 2 tầng để đảm bảo độ chính xác và tính kịp thời:

1.  **Tầng Lịch sử (World Bank API)**:
    -   Sử dụng `requests` gọi trực tiếp API JSON của World Bank.
    -   Ưu điểm: Dữ liệu đã được chuẩn hóa, chính xác tuyệt đối, coverage dài (1990+).

2.  **Tầng Real-time (NBS Playwright)**:
    -   Sử dụng `playwright` (headless browser) để truy cập `stats.gov.cn`.
    -   Xử lý JavaScript và HTML dynamic từ các bài Press Release mới nhất.
    -   Ưu điểm: Lấy được số liệu 2025 ngay khi vừa công bố (GDP Q3, PMI tháng mới nhất).

### Dependencies
- `playwright`: Cho việc cào NBS.
- `requests`: Cho việc gọi World Bank API.
- `asyncio`: Để chạy Playwright bất đồng bộ.

Cài đặt:
```bash
pip install playwright requests
python3 -m playwright install chromium
```

---

*Version: 2.0 - Hybrid Implementation*  
*Last Updated: 2025-12-26*
