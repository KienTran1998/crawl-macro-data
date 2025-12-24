#!/bin/bash

# ============================================================
# SCRIPT TỰ ĐỘNG CÀO DỮ LIỆU HẢI QUAN VIỆT NAM
# ============================================================

echo "============================================================"
echo "HƯỚNG DẪN CÀO DỮ LIỆU TỰ ĐỘNG"
echo "============================================================"
echo ""
echo "Do website Hải quan có anti-bot protection, cần chạy script"
echo "trong browser console để có kết quả tốt nhất."
echo ""
echo "BƯỚC 1: Mở trang Hải quan"
echo "----------------------------------------"
echo "URL: https://www.customs.gov.vn/index.jsp?pageId=444&group=C%C3%B4ng%20b%E1%BB%91%20v"
echo ""

# Tự động mở browser
echo "Đang mở browser..."
open "https://www.customs.gov.vn/index.jsp?pageId=444&group=C%C3%B4ng%20b%E1%BB%91%20v"

sleep 3

echo ""
echo "BƯỚC 2: Mở Developer Console"
echo "----------------------------------------"
echo "Nhấn: Cmd + Option + I (Mac) hoặc F12 (Windows/Linux)"
echo ""

echo "BƯỚC 3: Copy script vào clipboard"
echo "----------------------------------------"

# Xác định đường dẫn script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy script vào clipboard
cat "${SCRIPT_DIR}/browser_scraper.js" | pbcopy

echo "✓ Script đã được copy vào clipboard!"
echo ""

echo "BƯỚC 4: Paste và chạy"
echo "----------------------------------------"
echo "1. Chuyển sang tab Console trong Developer Tools"
echo "2. Nhấn Cmd+V (Mac) hoặc Ctrl+V (Windows) để paste"
echo "3. Nhấn Enter để chạy"
echo ""

echo "BƯỚC 5: Chờ download"
echo "----------------------------------------"
echo "- Script sẽ tự động chạy ~2-3 phút"
echo "- File customs_data.json sẽ tự động download"
echo "- Di chuyển file vào: scrapers/customs_vn/data/"
echo ""

echo "============================================================"
echo "TIP: Script đã ở trong clipboard, chỉ cần paste vào Console!"
echo "============================================================"
