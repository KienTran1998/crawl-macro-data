#!/usr/bin/env python3
"""
VietnamBiz Scraper - Alternative DOM Extraction Approach
Extract ALL visible text from popup to capture chart data
"""

import time
import os
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Inline config
TARGET_URL = "https://data.vietnambiz.vn/macro-economic"
OUTPUT_DIR = "data"
INDICATORS_LIST_FILE = os.path.join(OUTPUT_DIR, "vietnambiz_indicators_list.csv")
HISTORICAL_DATA_FILE = os.path.join(OUTPUT_DIR, "vietnambiz_historical_data.csv")
PAGE_LOAD_DELAY = 5
POPUP_LOAD_DELAY = 3
CLICK_DELAY = 1
TEST_LIMIT = 1
BROWSER_PATHS = [
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

class VietnamBizDOMScraper:
    def __init__(self, debug=False, test_mode=False):
        self.debug = debug
        self.test_mode = test_mode
        self.driver = None
        self.indicators_data = []
        self.historical_data = []
        
    def setup_driver(self):
        """Setup Selenium driver"""
        print("🚀 Khởi tạo browser...")
        
        options = Options()
        
        # Browser path
        for browser_path in BROWSER_PATHS:
            if os.path.exists(browser_path):
                options.binary_location = browser_path
                print(f"✅ Sử dụng: {browser_path}")
                break
        
        # Options
        if not self.debug:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def get_indicators_list(self):
        """Lấy danh sách indicators"""
        print(f"\n📊 Đang load trang {TARGET_URL}...")
        self.driver.get(TARGET_URL)
        time.sleep(PAGE_LOAD_DELAY)
        
        print("📋 Đang trích xuất danh sách chỉ số...")
        
        indicators = self.driver.execute_script("""
            const rows = [];
            const tableRows = document.querySelectorAll('tr.ant-table-row');
            
            tableRows.forEach((row, index) => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    const nameElement = cells[0].querySelector('[class*="name"], span, div');
                    const name = nameElement ? nameElement.textContent.trim() : '';
                    
                    if (name && name.length > 0) {
                        rows.push({
                            index: index,
                            name: name,
                            period: cells[1]?.textContent.trim() || '',
                            currentValue: cells[2]?.textContent.trim() || '',
                            previousValue: cells[3]?.textContent.trim() || '',
                        });
                    }
                }
            });
            
            return rows;
        """)
        
        print(f"✅ Tìm thấy {len(indicators)} chỉ số")
        self.indicators_data = indicators
        return indicators
    
    def extract_all_text_from_popup(self):
        """Extract ALL visible text from popup"""
        # Wait for popup to appear - try different selectors
        time.sleep(2)
        
        all_text = self.driver.execute_script("""
            // Find popup by various methods
            let popup = null;
            
            // Try different selectors
            const selectors = [
                '[role="dialog"]',
                '.ant-modal',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="Modal"]',
                '[style*="z-index"]'  // Often modals have high z-index
            ];
            
            for (const sel of selectors) {
                const found = document.querySelector(sel);
                if (found && found.offsetParent !== null) {  // visible check
                    popup = found;
                    break;
                }
            }
            
            if (!popup) {
                // Last resort: get all elements added recently with high z-index
                const highZElements = Array.from(document.querySelectorAll('div'))
                    .filter(el => {
                        const z = window.getComputedStyle(el).zIndex;
                        return z && parseInt(z) > 1000;
                    });
                if (highZElements.length > 0) {
                    popup = highZElements[highZElements.length - 1];
                }
            }
            
            if (!popup) {
                return {error: 'No popup found', allDivs: document.querySelectorAll('div').length};
            }
            
            // Extract ALL text from popup
            const allText = [];
            const textElements = popup.querySelectors('*');
            
            Array.from(textElements).forEach(el => {
                const text = el.textContent?.trim();
                if (text && text.length > 0 && text.length < 200) {
                    // Only direct text, not nested
                    const directText = Array.from(el.childNodes)
                        .filter(node => node.nodeType === 3)  // TEXT_NODE
                        .map(node => node.textContent.trim())
                        .filter(t => t.length > 0);
                    
                    allText.push(...directText);
                    
                    // Also get text from elements
                    if (el.children.length === 0 && text) {
                        allText.push(text);
                    }
                }
            });
            
            // Get SVG text elements (chart labels)
            const svgTexts = popup.querySelectorAll('svg text');
            Array.from(svgTexts).forEach(t => {
                const txt = t.textContent?.trim();
                if (txt) allText.push(txt);
            });
            
            return {
                found: true,
                popupClass: popup.className,
                textCount: allText.length,
                allText: [...new Set(allText)]  // Unique only
            };
        """)
        
        return all_text
    
    def parse_chart_data_from_text(self, text_data, indicator_name):
        """Parse data from extracted text"""
        if not text_data or 'error' in text_data:
            print(f"   ⚠️  {text_data.get('error', 'Unknown error')}")
            return []
        
        if not text_data.get('found'):
            print("   ⚠️  Popup không được tìm thấy")
            return []
        
        print(f"   ✅ Tìm thấy popup: {text_data['popupClass'][:50]}")
        print(f"   📝 Trích xuất {text_data['textCount']} đoạn text")
        
        all_text = text_data['allText']
        
        if self.debug:
            print(f"   Sample text: {all_text[:10]}")
        
        # Parse data points from text
        # Look for patterns like: "2024", "Mar '24", "Q1-2024", numbers with units
        time_series = []
        
        # Pattern matching for dates and values
        date_patterns = [
            r'(Q[1-4]-\d{4})',  # Q1-2024
            r'(Qu[ýy]\s*\d+/\d{4})',  # Quý 1/2024
            r'(Th[áa]ng\s*\d+/\d{4})',  # Tháng 1/2024
            r'(\w{3}\s*[\'′]\d{2})',  # Mar '24
            r'(\d{4})',  # 2024
        ]
        
        # Find all dates
        dates = []
        for text in all_text:
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                dates.extend(matches)
        
        # Find all numbers (potential values)
        numbers = []
        for text in all_text:
            # Match numbers with optional decimals and units
            num_matches = re.findall(r'([+-]?\d+[.,]\d+%?|[+-]?\d+%?)', text)
            numbers.extend(num_matches)
        
        # Try to pair dates with numbers
        # This is heuristic - assumes dates and numbers appear in order
        min_len = min(len(dates), len(numbers))
        for i in range(min_len):
            time_series.append({
                'Indicator': indicator_name,
                'Date': dates[i],
                'Value': numbers[i]
            })
        
        return time_series
    
    def click_indicator_and_extract(self, indicator):
        """Click indicator and extract data"""
        print(f"\n🖱️  Đang xử lý: {indicator['name']}")
        
        try:
            # Click on row
            row_index = indicator['index']
            row_element = self.driver.execute_script(f"""
                const rows = document.querySelectorAll('tr.ant-table-row');
                return rows[{row_index}];
            """)
            
            if not row_element:
                print(f"   ❌ Không tìm thấy row")
                return
            
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", 
                row_element
            )
            time.sleep(1)
            
            row_element.click()
            print("   ⏳ Đợi popup...")
            
            # Wait longer for popup
            time.sleep(POPUP_LOAD_DELAY + 2)
            
            # Extract all text
            print("   📡 Đang trích xuất text từ popup...")
            text_data = self.extract_all_text_from_popup()
            
            # Parse data
            time_series = self.parse_chart_data_from_text(text_data, indicator['name'])
            
            if time_series:
                print(f"   ✅ Trích xuất {len(time_series)} điểm dữ liệu")
                self.historical_data.extend(time_series)
                
                if self.debug and time_series:
                    print(f"   Sample: {time_series[0]}")
            else:
                print("   ⚠️  Không parse được data")
            
            # Close popup
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def save_results(self):
        """Save to CSV"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        if self.indicators_data:
            df = pd.DataFrame(self.indicators_data)
            df.to_csv(INDICATORS_LIST_FILE, index=False, encoding='utf-8-sig')
            print(f"\n💾 Lưu indicators: {INDICATORS_LIST_FILE}")
        
        if self.historical_data:
            df = pd.DataFrame(self.historical_data)
            df.to_csv(HISTORICAL_DATA_FILE, index=False, encoding='utf-8-sig')
            print(f"💾 Lưu historical data: {HISTORICAL_DATA_FILE}")
            print(f"   📊 Tổng: {len(df)} dòng")
        else:
            print("\n⚠️  Không có dữ liệu lịch sử")
    
    def run(self):
        """Main"""
        print("="*60)
        print("🚀 VIETNAMBIZ DOM SCRAPER")
        print("="*60)
        
        try:
            self.setup_driver()
            indicators = self.get_indicators_list()
            
            if not indicators:
                return
            
            if self.test_mode:
                indicators = indicators[:TEST_LIMIT]
                print(f"\n🧪 Test mode: {len(indicators)} chỉ số")
            
            for idx, indicator in enumerate(indicators, 1):
                print(f"\n[{idx}/{len(indicators)}]", end=" ")
                self.click_indicator_and_extract(indicator)
            
            self.save_results()
            print("\n" + "="*60)
            print("✅ HOÀN TẤT!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    scraper = VietnamBizDOMScraper(debug=args.debug, test_mode=args.test)
    scraper.run()
