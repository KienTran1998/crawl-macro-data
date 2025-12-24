import httpx
from bs4 import BeautifulSoup
import json
import datetime
import os
import re

# Configuration
URL = "https://tradingeconomics.com/vietnam/indicators"
OUTPUT_DIR = "scrapers/tradingeconomics/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "vietnam_te_latest.json")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def normalize_key(text):
    return clean_text(text).lower().replace(" ", "_").replace("-", "_")

def is_recent_date(date_str):
    """
    Parses date string like 'Dec/25', 'Q4/24', '2024-12-31'
    Returns True if year is 2024 or 2025.
    """
    if not date_str:
        return False
    
    date_str = date_str.strip()
    
    # Try parsing 'Mmm/YY' (e.g. Dec/25)
    match_my = re.search(r'[A-Za-z]{3}/(\d{2})', date_str)
    if match_my:
        year = int(match_my.group(1))
        # 2024 or 2025
        return year in [24, 25]

    # Try parsing 'Qx/YY' (e.g. Q3/24)
    match_qy = re.search(r'Q\d/(\d{2})', date_str)
    if match_qy:
        year = int(match_qy.group(1))
        return year in [24, 25]

    # Try parsing YYYY in typical formats if available (though TE usually uses short format in tables)
    match_yyyy = re.search(r'(202[4-5])', date_str)
    if match_yyyy:
        return True
        
    return False

def scrape():
    print(f"Fetching {URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = httpx.get(URL, headers=headers, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all tab panes which represent categories
    # Based on inspection: <div role="tabpanel" class="tab-pane ..." id="category_name">
    tab_panes = soup.find_all("div", class_="tab-pane")
    
    extracted_data = {}
    
    print(f"Found {len(tab_panes)} category tabs.")
    
    for pane in tab_panes:
        category_id = pane.get("id", "unknown")
        
        # Skip 'overview' if we want to rely on specific categories, 
        # but overview might have things not in others. Let's process all and overwrite.
        
        tables = pane.find_all("table", class_="table-hover")
        for table in tables:
            # Skip header row
            rows = table.find_all("tr")
            if not rows:
                continue
                
            # Headers usually: Name, Last, Previous, Highest, Lowest, Unit, Date
            # But we rely on index from inspection.
            # Row 0: ['Currency', '26360', ..., 'Dec/25'] (Date is index 6)
            
            for row in rows[1:]:
                cols = row.find_all("td")
                if not cols:
                    continue
                
                cols_text = [clean_text(td.get_text()) for td in cols]
                
                # Check if we have enough columns
                if len(cols_text) < 7:
                    continue
                
                name = cols_text[0]
                last_value = cols_text[1]
                previous = cols_text[2]
                unit = cols_text[5] # Might be empty index 5, check strictly?
                date_str = cols_text[6]
                
                # Double check unit/date index logic
                # If index 5 is unit, index 6 is date.
                # Sometimes columns might shift if there's a sparkline or icon? 
                # Let's inspect the text content to be sure "date_str" looks like a date.
                if not re.search(r'\d', date_str):
                    # Maybe it's shifted?
                    pass

                if is_recent_date(date_str):
                    key = normalize_key(name)
                    
                    data_entry = {
                        "name": name,
                        "category": category_id,
                        "last": last_value,
                        "previous": previous,
                        "unit": unit,
                        "date": date_str,
                        "crawled_at": datetime.datetime.now().isoformat()
                    }
                    
                    # Store in dictionary (deduplicates by key)
                    extracted_data[key] = data_entry

    # Wrap in final JSON structure
    final_output = {
        "source": "Trading Economics",
        "url": URL,
        "generated_at": datetime.date.today().isoformat(),
        "total_indicators": len(extracted_data),
        "data": extracted_data
    }
    
    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    print(f"Scraping complete. Saved {len(extracted_data)} indicators to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape()
