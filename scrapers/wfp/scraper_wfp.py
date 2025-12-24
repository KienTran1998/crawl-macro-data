"""
WFP Macro Data Scraper
Lấy các chỉ số kinh tế vĩ mô (Lạm phát, Giá cả thị trường, Tỷ giá) từ WFP thông qua HDX CKAN API
"""
import asyncio
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
import aiohttp
import pandas as pd
from io import StringIO

# Constants
HDX_API_BASE = "https://data.humdata.org/api/3/action"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "wfp_macro_data.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Keywords để tìm kiếm các chỉ số Macro
# Format: (search_query, priority_keywords_in_title)
# priority_keywords_in_title: Ưu tiên dataset có từ khóa này trong title
MACRO_KEYWORDS = [
    ("market monitor", ["Global", "WFP Global"]),  # Ưu tiên Global Market Monitor
    ("food price", ["Global"]),  # Ưu tiên Global Food Prices
    ("economic explorer", []),
    ("inflation", []),
    ("exchange rate", []),
]


async def search_wfp_macro(keyword: str, priority_keywords: List[str] = None, session: aiohttp.ClientSession = None) -> Optional[Dict[str, Any]]:
    """
    Tìm kiếm dataset WFP macro data mới nhất theo keyword.
    
    Args:
        keyword: Từ khóa tìm kiếm (ví dụ: "market monitor", "food price")
        priority_keywords: Danh sách từ khóa ưu tiên trong title (ví dụ: ["Global"])
        session: aiohttp session để thực hiện request
    
    Returns:
        Metadata của dataset mới nhất hoặc None nếu không tìm thấy
    """
    if priority_keywords is None:
        priority_keywords = []
    
    print(f"🔍 Searching for WFP dataset: '{keyword}'...")
    if priority_keywords:
        print(f"   Priority: datasets with '{', '.join(priority_keywords)}' in title")
    
    url = f"{HDX_API_BASE}/package_search"
    params = {
        "q": keyword,  # Chỉ tìm keyword, không cần thêm "organization:wfp" ở đây
        "fq": "organization:wfp",  # Filter theo WFP organization
        "rows": 20,  # Lấy nhiều kết quả hơn để có thể filter theo priority
        "sort": "metadata_modified desc",  # Sắp xếp theo ngày cập nhật mới nhất
    }
    
    try:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                print(f"   ⚠️ API returned status {response.status}")
                return None
            
            data = await response.json()
            
            if not data.get("success"):
                print(f"   ⚠️ API returned success=False: {data.get('error', {}).get('message', 'Unknown error')}")
                return None
            
            results = data.get("result", {}).get("results", [])
            
            if not results:
                print(f"   ⚠️ No datasets found for keyword: '{keyword}'")
                return None
            
            # Nếu có priority keywords, tìm dataset có chứa từ khóa đó trong title
            selected_dataset = None
            if priority_keywords:
                for dataset in results:
                    title = dataset.get('title', '').upper()
                    if any(priority.upper() in title for priority in priority_keywords):
                        selected_dataset = dataset
                        print(f"   ✅ Found priority dataset: '{dataset.get('title', 'N/A')}'")
                        break
            
            # Nếu không tìm thấy priority, lấy dataset mới nhất
            if selected_dataset is None:
                selected_dataset = results[0]
                print(f"   ✅ Found dataset: '{selected_dataset.get('title', 'N/A')}'")
            
            print(f"   📅 Last modified: {selected_dataset.get('metadata_modified', 'N/A')}")
            
            return selected_dataset
    
    except Exception as e:
        print(f"   ❌ Error searching for '{keyword}': {e}")
        return None


def get_resource_url(dataset_json: Dict[str, Any], preferred_formats: List[str] = None) -> Optional[Dict[str, str]]:
    """
    Tìm resource URL của file dữ liệu sạch nhất từ dataset.
    
    Args:
        dataset_json: JSON metadata của dataset từ API
        preferred_formats: Danh sách format ưu tiên (mặc định: ['CSV', 'JSON'])
    
    Returns:
        Dict chứa url, format, name của resource hoặc None nếu không tìm thấy
    """
    if preferred_formats is None:
        preferred_formats = ['CSV', 'JSON', 'XLSX', 'XLS']
    
    resources = dataset_json.get("resources", [])
    
    if not resources:
        print("   ⚠️ No resources found in dataset")
        return None
    
    print(f"   📦 Found {len(resources)} resources, filtering...")
    
    # Lọc resources theo format và loại bỏ metadata/readme files
    valid_resources = []
    
    for resource in resources:
        resource_format = resource.get("format", "").upper()
        resource_name = resource.get("name", "").lower()
        resource_url = resource.get("url", "")
        
        # Bỏ qua file metadata, readme, hoặc không có URL
        if not resource_url or any(skip in resource_name for skip in ["metadata", "readme", "guide"]):
            continue
        
        # Ưu tiên format CSV, JSON
        if resource_format in preferred_formats:
            priority = preferred_formats.index(resource_format) if resource_format in preferred_formats else 999
            valid_resources.append({
                "url": resource_url,
                "format": resource_format,
                "name": resource.get("name", "Unknown"),
                "description": resource.get("description", ""),
                "priority": priority,
                "size": resource.get("size", 0),
            })
    
    if not valid_resources:
        print("   ⚠️ No valid data resources found (CSV/JSON)")
        return None
    
    # Sắp xếp theo priority (CSV > JSON > XLSX > XLS) và size (file lớn hơn thường chứa nhiều data hơn)
    valid_resources.sort(key=lambda x: (x["priority"], -x["size"]))
    
    best_resource = valid_resources[0]
    print(f"   ✅ Selected resource: {best_resource['name']} ({best_resource['format']})")
    print(f"   🔗 URL: {best_resource['url'][:80]}...")
    
    return {
        "url": best_resource["url"],
        "format": best_resource["format"],
        "name": best_resource["name"],
    }


async def fetch_csv_data(url: str, session: aiohttp.ClientSession, max_rows: int = 1000) -> Optional[pd.DataFrame]:
    """
    Tải và đọc CSV data từ URL.
    Chỉ đọc một phần file để tránh tải quá nhiều dữ liệu.
    
    Args:
        url: URL của file CSV
        session: aiohttp session
        max_rows: Số dòng tối đa để đọc (mặc định 1000 dòng đầu)
    
    Returns:
        DataFrame hoặc None nếu lỗi
    """
    print(f"   📥 Downloading CSV data...")
    
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"   ⚠️ Failed to download: HTTP {response.status}")
                return None
            
            # Đọc file theo chunks để tránh memory issue
            content = await response.text()
            
            # Đọc CSV với pandas
            df = pd.read_csv(StringIO(content), nrows=max_rows)
            
            print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            print(f"   📊 Columns: {', '.join(df.columns[:5].tolist())}...")
            
            return df
    
    except Exception as e:
        print(f"   ❌ Error fetching CSV: {e}")
        return None


async def extract_macro_indicators(df: pd.DataFrame, dataset_title: str) -> List[Dict[str, Any]]:
    """
    Extract các chỉ số macro từ DataFrame.
    
    Args:
        df: DataFrame chứa dữ liệu
        dataset_title: Tên của dataset
    
    Returns:
        List các chỉ số đã extract
    """
    indicators = []
    
    # Tìm các cột quan trọng
    columns_lower = [col.lower() for col in df.columns]
    
    # Tìm cột giá cả
    price_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['price', 'cost', 'value'])]
    
    # Tìm cột lạm phát (bao gồm cả change/trend columns)
    inflation_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['inflation', 'change', 'trend', 'yoy'])]
    
    # Tìm cột tỷ giá
    exchange_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['exchange', 'rate', 'usd', 'currency'])]
    
    # Tìm cột quốc gia/khu vực
    country_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['country', 'location', 'region', 'market'])]
    
    # Tìm cột thời gian
    date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'month', 'year', 'period'])]
    
    print(f"   🔍 Found columns:")
    print(f"      - Price: {price_cols[:3]}")
    print(f"      - Inflation: {inflation_cols[:3]}")
    print(f"      - Exchange Rate: {exchange_cols[:3]}")
    print(f"      - Country: {country_cols[:3]}")
    print(f"      - Date: {date_cols[:3]}")
    
    # Sort theo cột Date nếu có để lấy dữ liệu mới nhất
    if len(df) > 0:
        # Tìm cột date để sort
        date_col = None
        for col in date_cols:
            if col in df.columns:
                try:
                    # Thử convert sang datetime để sort
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    date_col = col
                    break
                except:
                    continue
        
        # Sort theo date nếu tìm thấy
        if date_col:
            df_sorted = df.sort_values(by=date_col, na_position='last')
            latest_row = df_sorted.iloc[-1].to_dict()
        else:
            # Nếu không có date column, lấy row cuối cùng
            latest_row = df.iloc[-1].to_dict()
        
        indicator = {
            "dataset": dataset_title,
            "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": {}
        }
        
        # Extract giá cả
        if price_cols:
            for col in price_cols[:3]:  # Lấy 3 cột đầu
                value = latest_row.get(col)
                if pd.notna(value):
                    indicator["indicators"][f"price_{col.lower().replace(' ', '_')}"] = float(value) if isinstance(value, (int, float)) else str(value)
        
        # Extract lạm phát
        if inflation_cols:
            for col in inflation_cols[:2]:
                value = latest_row.get(col)
                if pd.notna(value):
                    indicator["indicators"][f"inflation_{col.lower().replace(' ', '_')}"] = float(value) if isinstance(value, (int, float)) else str(value)
        
        # Extract tỷ giá
        if exchange_cols:
            for col in exchange_cols[:2]:
                value = latest_row.get(col)
                if pd.notna(value):
                    indicator["indicators"][f"exchange_rate_{col.lower().replace(' ', '_')}"] = float(value) if isinstance(value, (int, float)) else str(value)
        
        # Extract thông tin quốc gia/khu vực
        if country_cols:
            for col in country_cols[:2]:
                value = latest_row.get(col)
                if pd.notna(value):
                    indicator["indicators"][f"location_{col.lower().replace(' ', '_')}"] = str(value)
        
        # Extract thời gian
        if date_cols:
            for col in date_cols[:1]:
                value = latest_row.get(col)
                if pd.notna(value):
                    indicator["indicators"]["period"] = str(value)
        
        # Thêm metadata về dataset
        indicator["metadata"] = {
            "total_rows": len(df),
            "columns": df.columns.tolist(),
            "price_columns": price_cols,
            "inflation_columns": inflation_cols,
            "exchange_rate_columns": exchange_cols,
        }
        
        indicators.append(indicator)
    
    return indicators


async def process_keyword(keyword_tuple: tuple, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """
    Xử lý một keyword: tìm dataset, lấy resource, download và extract data.
    
    Args:
        keyword_tuple: Tuple (keyword, priority_keywords) hoặc string keyword
        session: aiohttp session
    
    Returns:
        List các chỉ số đã extract
    """
    # Parse keyword tuple hoặc string
    if isinstance(keyword_tuple, tuple):
        keyword, priority_keywords = keyword_tuple
    else:
        keyword = keyword_tuple
        priority_keywords = []
    
    print(f"\n{'='*60}")
    print(f"Processing keyword: '{keyword}'")
    if priority_keywords:
        print(f"Priority keywords: {priority_keywords}")
    print(f"{'='*60}")
    
    # Bước 1: Tìm dataset
    dataset = await search_wfp_macro(keyword, priority_keywords, session)
    
    if not dataset:
        return []
    
    # Bước 2: Lấy resource URL
    resource_info = get_resource_url(dataset)
    
    if not resource_info:
        return []
    
    # Bước 3: Download và parse data
    if resource_info["format"] == "CSV":
        df = await fetch_csv_data(resource_info["url"], session, max_rows=1000)
        
        if df is not None and len(df) > 0:
            # Bước 4: Extract indicators
            indicators = await extract_macro_indicators(df, dataset.get("title", keyword))
            
            # Thêm thông tin về resource
            for indicator in indicators:
                indicator["resource_url"] = resource_info["url"]
                indicator["resource_name"] = resource_info["name"]
                indicator["resource_format"] = resource_info["format"]
            
            return indicators
    
    return []


def save_to_json(all_indicators: List[Dict[str, Any]]):
    """
    Lưu tất cả indicators vào file JSON.
    """
    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_datasets": len(all_indicators),
        "indicators": all_indicators
    }
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Data saved to {OUTPUT_FILE}")
        print(f"📊 Total indicators extracted: {len(all_indicators)}")
    except Exception as e:
        print(f"\n❌ Error saving data: {e}")


async def main():
    """
    Main function để crawl WFP macro data.
    """
    print("🚀 Starting WFP Macro Data Scraper...")
    print(f"📁 Output directory: {DATA_DIR}")
    keyword_list = [kw[0] if isinstance(kw, tuple) else kw for kw in MACRO_KEYWORDS]
    print(f"🔍 Keywords to search: {', '.join(keyword_list)}")
    print()
    
    all_indicators = []
    
    async with aiohttp.ClientSession() as session:
        # Xử lý từng keyword
        for keyword_config in MACRO_KEYWORDS:
            try:
                indicators = await process_keyword(keyword_config, session)
                all_indicators.extend(indicators)
                
                # Delay giữa các request để tránh rate limit
                await asyncio.sleep(2)
            
            except Exception as e:
                keyword_str = keyword_config[0] if isinstance(keyword_config, tuple) else keyword_config
                print(f"❌ Error processing keyword '{keyword_str}': {e}")
                continue
    
    # Lưu kết quả
    if all_indicators:
        save_to_json(all_indicators)
    else:
        print("\n⚠️ No indicators extracted. Please check the keywords or API availability.")
    
    print("\n🏁 Scraper finished.")


if __name__ == "__main__":
    asyncio.run(main())

