#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper for International Tourism Statistics to Vietnam
Source: https://thongke.tourism.vn/
"""

from playwright.sync_api import sync_playwright
import json
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://thongke.tourism.vn"
OUTPUT_FILE = "data/tourism_data.json"

# Years to scrape (2008-2025, as confirmed available)
YEARS = list(range(2008, 2026))
YEAR_PARAM = ",".join(map(str, YEARS))

# Define categories with correct parameters
CATEGORIES = {
    "by_transport": {
        "name_vn": "Phân theo phương tiện",
        "url": f"{BASE_URL}/index.php/statistic/stat/6?share=99&type=type1&rowcode=17&input-type=4&row-list=17_1701,17_1702,17_1703&nam={YEAR_PARAM}"
    },
    "by_market": {
        "name_vn": "Phân theo thị trường",
        "url": f"{BASE_URL}/index.php/statistic/stat/6?share=99&type=type1&rowcode=14&input-type=4&row-list=14_1401,14_1402,14_140102,14_140106,14_140108,14_140110,14_140111,14_140119,14_140122,14_140124,14_140128,14_140131,14_140134,14_140139,14_140141,14_140203,14_140206,14_140208,14_140214,14_140215,14_140231,14_140232,14_140233,14_140234,14_140241,14_140243,14_140244,14_140246,14_140247,14_140501,14_140507,14_140308,14_140321,14_140145,14_140248,14_140336,14_140455,14_140515,14_140146,14_140147,14_140249,14_1406&nam={YEAR_PARAM}"
    },
    "by_visitor_type": {
        "name_vn": "Phân theo đối tượng khách",
        "url": f"{BASE_URL}/index.php/statistic/stat/6?share=99&type=type1&rowcode=12&input-type=4&row-list=12_1201&nam={YEAR_PARAM}"
    },
    "by_visitor_group": {
        "name_vn": "Phân theo nhóm khách",
        "url": f"{BASE_URL}/index.php/statistic/stat/6?share=99&type=type1&rowcode=24&input-type=4&row-list=24_2401,24_2402&nam={YEAR_PARAM}"
    }
}


def extract_table_data(page) -> List[Dict[str, Any]]:
    """
    Extract data from the pivot table using JavaScript.
    """
    # Wait for table to load
    try:
        page.wait_for_selector('#output table.pvtTable', timeout=30000)
    except:
        print("   ⚠️  Table not found or timeout")
        return []
    
    # Extract table data using JavaScript
    js_code = """
    (() => {
        const table = document.querySelector('#output table.pvtTable');
        if (!table) return null;
        
        // Extract headers (years)
        const headers = [];
        const headerRow = table.querySelector('thead tr');
        if (headerRow) {
            const ths = headerRow.querySelectorAll('th');
            for (let i = 1; i < ths.length; i++) {  // Skip first column
                headers.push(ths[i].innerText.trim());
            }
        }
        
        // Extract data rows
        const rows = [];
        const tbody = table.querySelector('tbody');
        if (tbody) {
            const trs = tbody.querySelectorAll('tr');
            trs.forEach(tr => {
                const cells = tr.querySelectorAll('td, th');
                if (cells.length > 0) {
                    const rowData = {
                        label: cells[0].innerText.trim(),
                        values: []
                    };
                    for (let i = 1; i < cells.length; i++) {
                        rowData.values.push(cells[i].innerText.trim());
                    }
                    rows.push(rowData);
                }
            });
        }
        
        return { headers, rows };
    })()
    """
    
    result = page.evaluate(js_code)
    
    if not result or not result.get('headers'):
        return []
    
    # Convert to flat records
    records = []
    headers = result['headers']
    
    for row in result['rows']:
        label = row['label']
        values = row['values']
        
        for i, value in enumerate(values):
            if i >= len(headers):
                break
            
            # Parse value (remove commas/dots)
            value_text = value.replace(',', '').replace('.', '')
            try:
                numeric_value = int(value_text) if value_text and value_text.isdigit() else 0
            except ValueError:
                numeric_value = 0
            
            # Parse year
            try:
                year = int(headers[i])
            except ValueError:
                continue
            
            records.append({
                'subcategory': label,
                'year': year,
                'value': numeric_value
            })
    
    return records


def scrape_category(page, category_key: str, category_info: Dict) -> List[Dict[str, Any]]:
    """
    Scrape a single category.
    """
    print(f"\n📊 Scraping: {category_key} ({category_info['name_vn']})")
    print(f"   URL: {category_info['url'][:80]}...")
    
    try:
        # Navigate to the page
        page.goto(category_info['url'], wait_until='domcontentloaded', timeout=60000)
        
        # Wait a bit for JavaScript to render
        time.sleep(2)
        
        # Extract data
        records = extract_table_data(page)
        
        # Add category to each record
        for record in records:
            record['category'] = category_key
        
        print(f"   ✓ Extracted {len(records)} records")
        return records
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def scrape_all_categories() -> Dict[str, Any]:
    """
    Main scraping function.
    """
    print("=" * 60)
    print("VIETNAM TOURISM DATA SCRAPER")
    print("=" * 60)
    
    all_data = []
    
    with sync_playwright() as p:
        # Launch browser
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Set longer timeout
        page.set_default_timeout(60000)
        
        # Scrape each category
        for category_key, category_info in CATEGORIES.items():
            records = scrape_category(page, category_key, category_info)
            all_data.extend(records)
        
        # Close browser
        browser.close()
    
    # Create summary
    result = {
        'metadata': {
            'source': 'https://thongke.tourism.vn/',
            'description': 'International visitors to Vietnam',
            'categories': list(CATEGORIES.keys()),
            'year_range': f"{min(YEARS)}-{max(YEARS)}",
            'total_records': len(all_data)
        },
        'data': all_data
    }
    
    return result


def main():
    """
    Main execution function.
    """
    try:
        # Scrape data
        result = scrape_all_categories()
        
        # Save to JSON
        print(f"\n💾 Saving data to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ SCRAPING COMPLETED")
        print("=" * 60)
        print(f"Total records: {result['metadata']['total_records']}")
        print(f"Output file: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
