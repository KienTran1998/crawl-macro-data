# Trading Economics Vietnam Scraper

Mô-đun này chứa scraper Python để thu thập các chỉ số kinh tế vĩ mô của Việt Nam từ [Trading Economics](https://tradingeconomics.com/vietnam/indicators). Mục tiêu chính là lấy dữ liệu **mới nhất** cho các chỉ số kinh tế và lưu trữ dưới dạng JSON có cấu trúc.

## Thống kê dữ liệu hiện tại (Snapshot)

Dưới đây là thống kê từ lần chạy gần nhất:

*   **Tổng số chỉ số thu thập được:** **70**
*   **Nguồn dữ liệu:** Trading Economics
*   **Phân bố theo nhóm chỉ số:**
    *   **GDP:** 14 chỉ số
    *   **Thương mại (Trade):** 12 chỉ số
    *   **Giá cả (Prices):** 11 chỉ số
    *   **Lao động (Labour):** 10 chỉ số
    *   **Chính phủ (Government):** 10 chỉ số
    *   **Kinh doanh (Business):** 6 chỉ số
    *   **Tiền tệ (Money):** 3 chỉ số
    *   **Tổng quan (Overview):** 2 chỉ số
    *   **Tiêu dùng (Consumer):** 2 chỉ số
*   **Tính kịp thời:**
    *   Dữ liệu năm 2025: 56 chỉ số
    *   Dữ liệu năm 2024: 14 chỉ số

## Các tệp trong mô-đun

-   `scraper_te_vietnam.py`: Script chính thực hiện việc tải, phân tích và lưu dữ liệu.
-   `analyze_data.py`: Tiện ích phân tích nhanh dữ liệu đã cào (số lượng, phân loại, tính kịp thời).
-   `analyze_dimensions.py`: Tiện ích phân tích cấu trúc dữ liệu (các đơn vị đo lường, danh mục duy nhất).
-   `data/vietnam_te_latest.json`: Tệp chứa kết quả dữ liệu JSON.

## Quy trình thu thập dữ liệu

Script `scraper_te_vietnam.py` thực hiện các bước:
1.  **Tải trang**: Lấy HTML từ `https://tradingeconomics.com/vietnam/indicators`.
2.  **Phân tích**: Sử dụng `BeautifulSoup` để đọc các bảng dữ liệu trong từng tab danh mục.
3.  **Trích xuất**: Với mỗi chỉ số, lấy các thông tin:
    -   `name`: Tên chỉ số (ví dụ: GDP Annual Growth Rate).
    -   `category`: Nhóm chỉ số (ví dụ: GDP, Inflation).
    -   `last`: Giá trị mới nhất.
    -   `previous`: Giá trị kỳ trước.
    -   `unit`: Đơn vị tính.
    -   `date`: Thời gian công bố.
4.  **Lọc**: Chỉ giữ lại các dữ liệu của năm **2024** và **2025** để đảm bảo tính cập nhật.
5.  **Lưu trữ**: Ghi vào file `data/vietnam_te_latest.json`.

**Lưu ý**: Scraper này chỉ lấy giá trị *mới nhất* hiển thị trên bảng, **không** lấy chuỗi dữ liệu lịch sử (time series).

## Cách chạy

1.  Tại thư mục gốc `crawl-macro-data`.
2.  Chạy scraper:
    ```bash
    python3 scrapers/tradingeconomics/scraper_te_vietnam.py
    ```
3.  Xem thống kê phân tích:
    ```bash
    python3 scrapers/tradingeconomics/analyze_data.py
    ```

## Ví dụ dữ liệu đầu ra

```json
{
  "source": "Trading Economics",
  "total_indicators": 70,
  "data": {
    "gdp_annual_growth_rate": {
      "name": "GDP Annual Growth Rate",
      "last": "8.23",
      "unit": "percent",
      "date": "Sep/25"
    },
    "inflation_rate": {
      "name": "Inflation Rate",
      "last": "3.58",
      "unit": "percent",
      "date": "Nov/25"
    }
  }
}