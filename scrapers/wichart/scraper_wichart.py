import time
import pandas as pd
import os
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cấu hình
BASE_URL = "https://wichart.vn/vi-mo/vn"
OUTPUT_DIR = "scrapers/wichart/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "wichart_indicators_hybrid.csv")

TARGET_CATEGORIES = [
    "Tổng sản phẩm quốc nội",
    "Sản xuất và Dịch vụ",
    "Tiêu dùng",
    "Giá cả",
    "Thị trường hàng hoá",
    "Giao dịch quốc tế",
    "Đầu tư",
    "Hệ thống ngân hàng",
    "Thị trường tiền tệ",
    "Thị trường vốn",
    "Tài khóa",
    "Bất động sản",
    "Thị trường lao động"
]

def setup_driver():
    options = Options()
    # Kích hoạt Performance Logging để bắt URL API
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Tìm browser path (Brave/Chrome/Edge)
    possible_paths = [
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/CocCoc.app/Contents/MacOS/CocCoc", 
    ]
    binary_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if binary_path:
        print(f"ℹ️Sử dụng Binary: {binary_path}")
        options.binary_location = binary_path

    return webdriver.Chrome(options=options)

def get_api_url_from_logs(driver):
    """Quét log performance để tìm URL API JSON"""
    logs = driver.get_log("performance")
    candidates = []
    for entry in logs:
        try:
            message = json.loads(entry["message"])["message"]
            if message["method"] == "Network.responseReceived":
                url = message["params"]["response"]["url"]
                # Lọc URL tiềm năng
                if "wichart.vn" in url and ("api" in url or "data" in url or "getByCategoryID" in url):
                    candidates.append(url)
        except:
            pass
    return candidates

def scrape_wichart_hybrid():
    print(f"🚀 Bắt đầu Scraper (Hybrid Selenium + Requests)...")
    driver = setup_driver()
    collected_data = []

    try:
        print("⏳ Đang tải trang...")
        driver.get(BASE_URL)
        time.sleep(5) # Đợi init

        # Lấy session cookies và Headers chuẩn
        selenium_cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        session.headers.update({
            "User-Agent": driver.execute_script("return navigator.userAgent"),
            "Referer": "https://wichart.vn/",
            "Origin": "https://wichart.vn",
            "Accept": "application/json, text/plain, */*",
        })

        for category in TARGET_CATEGORIES:
            print(f"\n🔍 Đang xử lý nhóm: {category}")
            
            try:
                # Xóa log cũ
                driver.get_log("performance")
                
                # Logic Click cải tiến
                driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(0.5)

                xpath = f"//*[text()='{category}'] | //*[contains(text(), '{category}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                
                # Retry Scroll nếu không thấy
                if not elements:
                    print("   ...Không thấy ngay, thử scroll sâu hơn...")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    elements = driver.find_elements(By.XPATH, xpath)

                clicked = False
                for el in elements:
                    if len(el.text) > len(category) * 4: 
                        continue
                    
                    if el.is_displayed():
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            time.sleep(0.5)
                            el.click()
                            clicked = True
                            print(f"   🖱️ Click: {category}")
                            break
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", el)
                                clicked = True
                                break
                            except:
                                continue
                
                if not clicked:
                    print(f"❌ Không click được menu {category}")
                    continue

                # Wait logic: Chờ API xuất hiện trong log
                print("   ⏳ Đang chờ API response...")
                api_url = None
                time.sleep(2) 
                
                # Quét log tìm API chuẩn
                candidate_urls = get_api_url_from_logs(driver)
                
                # Logic chọn URL thông minh
                for url in reversed(candidate_urls): # Lấy mới nhất trước
                    if "getByCategoryID" in url:
                        api_url = url
                        break
                
                if not api_url and candidate_urls:
                    # Fallback lấy URL có vẻ giống API nhất
                    for url in reversed(candidate_urls):
                        if "wichartapi" in url:
                            api_url = url
                            break

                success_api = False
                if api_url:
                    print(f"   🔗 Bắt được API URL: {api_url}")
                    
                    try:
                        resp = session.get(api_url, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            items = []
                            if isinstance(data, list): items = data
                            elif isinstance(data, dict):
                                for k in ['data', 'result', 'items', 'rows']:
                                    if k in data and isinstance(data[k], list):
                                        items = data[k]
                                        break
                                if not items: items = [data]

                            count = 0
                            for item in items:
                                name = item.get('nameVi') or item.get('name') or item.get('indicatorName')
                                code = item.get('code') or item.get('indicatorCode')
                                unit = item.get('unit')
                                
                                if name:
                                    collected_data.append({
                                        "Category": category,
                                        "Indicator": name,
                                        "Code": code,
                                        "Unit": unit,
                                        "Type": "API_EXTRACTED"
                                    })
                                    count += 1
                            
                            if count > 0:
                                print(f"   ✅ Lấy được {count} chỉ số từ API.")
                                success_api = True
                            else:
                                print("   ⚠️ API trả về data rỗng hoặc không đúng cấu trúc.")
                        else:
                            print(f"   ⚠️ API request lỗi: {resp.status_code}")
                    except Exception as req_err:
                        print(f"   ⚠️ Lỗi request API: {req_err}")
                
                if not success_api:
                    print("   🔄 Fallback: Dùng DOM Scraping...")
                    # DOM FALLBACK
                    indicators = driver.execute_script('''
                        const items = [];
                        const allElements = document.querySelectorAll('div, span, p, td, li, a');
                        allElements.forEach(el => {
                            const rect = el.getBoundingClientRect();
                            const text = el.innerText ? el.innerText.trim() : "";
                            if (rect.left > 250 && rect.width > 0 && rect.height > 0 && text.length > 3 && text.length < 150) {
                                items.push(text);
                            }
                        });
                        return [...new Set(items)];
                    ''')
                    
                    count_dom = 0
                    for ind in indicators:
                        bad_keywords = ["báo cáo", "biểu đồ", "xuất excel", "chia sẻ", "đơn vị", "nguồn", "dữ liệu", "đang cập nhật", "wichart", "liên hệ", "về chúng tôi", "bản quyền", "mã chứng khoán", "đăng nhập", "đăng ký"]
                        if ind.lower() == category.lower(): continue
                        if any(k in ind.lower() for k in bad_keywords): continue
                        if ind.replace('.', '').replace(',', '').replace('/', '').replace('-', '').strip().isdigit(): continue
                        if len(ind) < 4 or ind in ["Giá trị", "Thay đổi", "Ngày cập nhật", "Tên chỉ số"]:
                            continue

                        collected_data.append({
                            "Category": category,
                            "Indicator": ind,
                            "Code": "DOM",
                            "Unit": "",
                            "Type": "DOM_FALLBACK"
                        })
                        count_dom += 1
                    print(f"   ✅ Lấy được {count_dom} chỉ số từ DOM.")

            except Exception as e:
                print(f"❌ Lỗi: {e}")

    except Exception as main_err:
        print(f"❌ Lỗi fatal: {main_err}")
    finally:
        driver.quit()

    if collected_data:
        df = pd.DataFrame(collected_data)
        df.drop_duplicates(subset=['Category', 'Indicator'], inplace=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Hoàn tất! Đã lưu {len(df)} dòng vào {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_wichart_hybrid()