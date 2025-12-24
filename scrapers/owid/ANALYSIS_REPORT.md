# Phân tích khả năng thu thập dữ liệu từ Our World in Data (Vietnam)

**Ngày phân tích:** 08/12/2025
**Nguồn:** https://ourworldindata.org/search?countries=Vietnam&resultType=all
**Phương pháp:** Reverse Engineering Algolia API của OWID.

## 1. Tổng quan về số lượng

Để tránh nhầm lẫn về thuật ngữ, chúng tôi phân chia thành hai cấp độ:

*   **Loại chỉ số (Topics/Categories):** Là các nhóm chủ đề lớn (ví dụ: Y tế, Năng lượng, Giáo dục).
    *   **Kết quả:** Có tổng cộng **130 loại chỉ số** khác nhau có dữ liệu về Việt Nam.
*   **Biểu đồ/Chỉ số cụ thể (Charts/Indicators):** Là các biểu đồ dữ liệu đơn lẻ trong từng loại (ví dụ: "Tỷ lệ tiêm chủng sởi", "Lượng khí thải CO2 bình quân đầu người").
    *   **Kết quả:** Tìm thấy khoảng **6,945** biểu đồ. Đã tải và phân tích chi tiết mẫu **3,000** biểu đồ đầu tiên.
    *   **Độ liên quan:** Qua kiểm tra mẫu, **99.8%** (2993/3000) chỉ số đều cho phép chọn quốc gia là **Vietnam** để xem dữ liệu.

## 2. Chi tiết về 130 Loại chỉ số (Topics)

Dưới đây là danh sách các loại chỉ số chính và số lượng biểu đồ con trong mỗi loại (dựa trên mẫu 3000 biểu đồ):

*   **Health (Sức khỏe):** 921 biểu đồ
*   **Energy and Environment (Năng lượng & Môi trường):** 595 biểu đồ
*   **Poverty and Economic Development (Nghèo đói & Phát triển kinh tế):** 424 biểu đồ
*   **Education and Knowledge (Giáo dục & Tri thức):** 365 biểu đồ
*   **Global Education (Giáo dục toàn cầu):** 338 biểu đồ
*   **Food and Agriculture (Thực phẩm & Nông nghiệp):** 296 biểu đồ
*   **Population and Demographic Change (Dân số & Nhân khẩu học):** 270 biểu đồ
*   **Human Rights and Democracy (Nhân quyền & Dân chủ):** 225 biểu đồ
*   **Causes of Death (Nguyên nhân tử vong):** 199 biểu đồ
*   **Energy (Năng lượng):** 184 biểu đồ
*   **CO2 & Greenhouse Gas Emissions (Khí thải nhà kính):** 147 biểu đồ
*   **Living Conditions (Điều kiện sống & An sinh):** 129 biểu đồ
*   **Violence and War (Bạo lực & Chiến tranh):** 111 biểu đồ
*   **Child & Infant Mortality (Tử vong ở trẻ em):** 109 biểu đồ
*   **Democracy (Dân chủ):** 107 biểu đồ
*   **Global Health (Sức khỏe toàn cầu):** 98 biểu đồ
*   **Economic Growth (Tăng trưởng kinh tế):** 92 biểu đồ
*   **Vaccination (Tiêm chủng):** 80 biểu đồ
*   **COVID-19:** 79 biểu đồ
*   **Innovation and Technological Change (Đổi mới & Công nghệ):** 64 biểu đồ
*   **Clean Water & Sanitation (Nước sạch & Vệ sinh):** 55 biểu đồ
*   **Air Pollution (Ô nhiễm không khí):** 48 biểu đồ
*   **Trade & Globalization (Thương mại & Toàn cầu hóa):** 43 biểu đồ
*   **Urbanization (Đô thị hóa):** 43 biểu đồ
*   **Mental Health (Sức khỏe tâm thần):** 41 biểu đồ
*   **Agricultural Production (Sản xuất nông nghiệp):** 52 biểu đồ
*   ... và nhiều loại khác.

## 3. Đánh giá về tính kịp thời của dữ liệu

**Quan trọng:** Cần phân biệt giữa "Ngày cập nhật Metadata" và "Năm dữ liệu mới nhất".

*   **Ngày cập nhật Metadata (Updated At):** Là thời gian đội ngũ Our World in Data cập nhật cấu hình biểu đồ (sửa lỗi, đổi nguồn, cập nhật mô tả).
    *   Kết quả phân tích: **2,180** chỉ số được cập nhật Metadata trong năm 2025.
*   **Năm dữ liệu thực tế (Latest Data Year):** Là năm cuối cùng có giá trị số liệu thực tế.
    *   Thường có độ trễ từ **1-2 năm** tùy nguồn dữ liệu gốc (World Bank, UN, WHO...).
    *   **Thực tế:** Mặc dù hệ thống ghi nhận cập nhật năm 2025, nhưng đa số dữ liệu kinh tế vĩ mô và xã hội sẽ có số liệu thực tế đến năm **2023 hoặc 2024**. Chỉ một số ít dữ liệu tần suất cao (như khí tượng, thị trường) mới có số liệu 2025.

## 4. File danh sách chi tiết

Danh sách toàn bộ 3,000 chỉ số đã tìm thấy (bao gồm tên, đường dẫn, ngày cập nhật) được lưu tại:
`scrapers/owid/data/all_vietnam_indicators.json`
