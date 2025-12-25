# Scraper Dữ Liệu Du Lịch Việt Nam

## 📊 Tổng Quan

Scraper tự động cào số liệu khách quốc tế đến Việt Nam từ Cơ sở dữ liệu trực tuyến thống kê du lịch.

- **Nguồn**: https://thongke.tourism.vn/
- **Dữ liệu**: 4 danh mục phân loại
- **Thời gian**: 2008-2025
- **Tổng records**: ~796

**Trạng thái**: ✅ Hoàn thành và đã test (796 records verified)

---

## 🚀 Cách Sử Dụng

```bash
cd scrapers/tourism_vn
python3 scraper.py
```

Output: `data/tourism_data.json`

---

## 📁 Cấu Trúc Dữ Liệu

### 4 Danh Mục Phân Loại

1. **by_transport** (Phân theo phương tiện)
   - Đường không (Air)
   - Đường bộ (Land)
   - Đường biển (Sea)

2. **by_market** (Phân theo thị trường)
   - Các quốc gia/khu vực (40+ markets)
   - Ví dụ: Hàn Quốc, Trung Quốc, Mỹ, Nhật Bản, v.v.

3. **by_visitor_type** (Phân theo đối tượng khách)
   - Các loại khách du lịch

4. **by_visitor_group** (Phân theo nhóm khách)
   - Khách đi công tác
   - Khách du lịch

### Format JSON

```json
{
  "metadata": {
    "source": "https://thongke.tourism.vn/",
    "description": "International visitors to Vietnam",
    "categories": ["by_transport", "by_market", "by_visitor_type", "by_visitor_group"],
    "year_range": "2008-2025",
    "total_records": 796
  },
  "data": [
    {
      "subcategory": "Đường biển",
      "year": 2008,
      "value": 67024,
      "category": "by_transport"
    },
    ...
  ]
}
```

### Các Trường Dữ Liệu

| Trường | Mô Tả |
|--------|-------|
| `category` | Danh mục chính (by_transport, by_market, v.v.) |
| `subcategory` | Danh mục con (Đường không, Hàn Quốc, v.v.) |
| `year` | Năm (2008-2025) |
| `value` | Số lượng khách (lượt người) |

---

## 🔧 Kỹ Thuật

### Công cụ sử dụng
- **Playwright**: Để xử lý JavaScript-rendered table
- **Python 3**: Core language

### Tại sao dùng Playwright?

Website sử dụng JavaScript để render bảng dữ liệu động (pivot table). 
- `requests`/`BeautifulSoup` không thấy được bảng
- Playwright mở browser thật, chờ JavaScript load, rồi extract data

### Logic

1. Khởi động browser (headless mode)
2. Navigate đến 4 URL categories với tham số `nam=2008,2009,...,2025`
3. Đợi table render (`#output table.pvtTable`)
4. Extract data qua JavaScript:
   - Headers = Years
   - Rows = Subcategories  
   - Values = Visitor numbers
5. Chuyển pivot table → flat records
6. Lưu JSON

---

## ✅ Verify Dữ Liệu

```bash
# Kiểm tra tổng số records
cat data/tourism_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'Records: {len(data[\"data\"])}')"

# Xem metadata
cat data/tourism_data.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(json.dumps(data['metadata'], indent=2, ensure_ascii=False))"

# Xem mẫu
head -n 50 data/tourism_data.json
```

**Kết quả mong đợi**: ~796 records

---

##Dependencies

Đảm bảo đã cài đặt:
```bash
pip install playwright
python3 -m playwright install chromium
```

---

## 📊 Số Liệu Mẫu

### Theo Phương Tiện (2024)
- Đường không: 14,844,120 khách
- Đường bộ: 2,491,731 khách  
- Đường biển: 248,050 khách
- **Tổng**: 17,583,901 khách

### Top Markets (2024)
- Hàn Quốc: ~3.5 triệu
- Trung Quốc: ~3.4 triệu
- Các thị trường khác...

---

*Version: 1.0 - Production Ready*  
*Last Updated: 2025-12-25*
