"""
Macro Indicators Scraper - Tổng hợp tất cả dữ liệu vào 1 file
Lấy dữ liệu từ 3 nguồn: WFP (Market), FAO (National), Yahoo Finance (Global)
Output: Tách thành 3 file riêng
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import aiohttp
import pandas as pd
from io import StringIO
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
WFP_OUTPUT_FILE = os.path.join(DATA_DIR, "wfp_data.json")
FAO_OUTPUT_FILE = os.path.join(DATA_DIR, "fao_data.json")
MARKET_OUTPUT_FILE = os.path.join(DATA_DIR, "market_data.json")

# Country codes - Ưu tiên Vietnam, nếu không có thì lấy bất kỳ
VIETNAM_CODES = {
    "wfp": "Vietnam",
    "fao": "231",  # FAO country code cho Vietnam
    "iso3": "VNM"
}

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


# ==================== WFP DATA (Market Level) ====================

async def fetch_wfp_food_prices(session: aiohttp.ClientSession, country: str = "Vietnam") -> List[Dict]:
    """
    Lấy WFP Food Prices với metric mp_price - CHỈ LẤY NGÀY MỚI NHẤT
    Dimensions: cm_name (Commodity), adm0_name (Country), mp_year (Time)
    """
    print(f"\n{'='*60}")
    print(f"📊 WFP FOOD PRICES DATA")
    print(f"{'='*60}")
    print(f"Country: {country} (fallback: any available)")
    print(f"Period: Latest date only")
    
    # Tìm dataset WFP Food Prices hoặc Market Monitor
    hdx_api = "https://data.humdata.org/api/3/action/package_search"
    
    # Thử nhiều query để tìm dataset phù hợp - Ưu tiên tìm Vietnam
    queries = [
        {"q": f"{country} Food Prices", "fq": "organization:wfp", "rows": 20},
        {"q": "Vietnam Food Prices", "fq": "organization:wfp", "rows": 20},
        {"q": "VNM Food Prices", "fq": "organization:wfp", "rows": 20},
        {"q": "Food Prices", "fq": "organization:wfp", "rows": 30},
        {"q": "Global Market Monitor", "fq": "organization:wfp", "rows": 10},
        {"q": "Market Monitor", "fq": "organization:wfp", "rows": 20},
    ]
    
    selected_dataset = None
    
    for query_params in queries:
        try:
            async with session.get(hdx_api, params=query_params) as response:
                if response.status != 200:
                    continue
                
                data = await response.json()
                results = data.get("result", {}).get("results", [])
                
                if not results:
                    continue
                
                # Tìm dataset có chứa price data thực sự
                for dataset in results:
                    title = dataset.get("title", "").lower()
                    resources = dataset.get("resources", [])
                    
                    # Check nếu có CSV resource
                    csv_resource = None
                    for res in resources:
                        if res.get("format", "").upper() == "CSV":
                            csv_resource = res
                            break
                    
                    if csv_resource:
                        # Ưu tiên dataset có country name hoặc Global/Market Monitor
                        if country.lower() in title:
                            selected_dataset = dataset
                            print(f"   ✅ Found country-specific dataset: {dataset.get('title')}")
                            break
                        elif ("global" in title or "market monitor" in title) and not selected_dataset:
                            selected_dataset = dataset
                            print(f"   ✅ Found dataset: {dataset.get('title')}")
                
                if selected_dataset:
                    break
        
        except Exception as e:
            continue
    
    if not selected_dataset:
        print("   ⚠️ No suitable datasets found")
        return []
    
    # Lấy resource CSV
    resources = selected_dataset.get("resources", [])
    csv_resource = None
    for res in resources:
        if res.get("format", "").upper() == "CSV":
            csv_resource = res
            break
    
    if not csv_resource:
        print("   ⚠️ No CSV resource found")
        return []
    
    csv_url = csv_resource.get("url")
    print(f"   📥 Downloading CSV...")
    
    # Download CSV
    try:
        async with session.get(csv_url) as csv_response:
            if csv_response.status != 200:
                print(f"   ⚠️ Failed to download CSV: {csv_response.status}")
                return []
            
            content = await csv_response.text()
            df = pd.read_csv(StringIO(content))
            
            print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Bỏ qua header rows (thường bắt đầu bằng #)
            for col in df.columns:
                if len(df) > 0:
                    first_val = str(df[col].iloc[0])
                    if first_val.startswith('#'):
                        # Skip first row nếu là header
                        df = df.iloc[1:].reset_index(drop=True)
                        print(f"   ⚠️ Skipped header row")
                        break
            
            # Tìm các cột quan trọng
            country_col = None
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['adm0_name', 'country', 'location', 'countryname']):
                    country_col = col
                    break
            
            year_col = None
            date_col = None
            for col in df.columns:
                col_lower = col.lower()
                if 'mp_year' in col_lower or ('year' in col_lower and 'date' not in col_lower):
                    year_col = col
                    break
                elif 'date' in col_lower:
                    date_col = col
                    break
            
            price_col = None
            # Ưu tiên tìm mp_price, sau đó tìm các cột price khác
            for col in df.columns:
                col_lower = col.lower()
                if 'mp_price' in col_lower:
                    price_col = col
                    break
            
            if not price_col:
                # Tìm cột có tên chính xác là "price" hoặc "usdprice"
                for col in df.columns:
                    col_lower = col.lower()
                    if col_lower == 'price' or col_lower == 'usdprice':
                        # Kiểm tra xem có phải là số không (đã skip header ở trên)
                        try:
                            sample_vals = df[col].dropna()
                            if len(sample_vals) > 0:
                                # Lấy giá trị đầu tiên không phải header
                                for val in sample_vals:
                                    if isinstance(val, str) and val.startswith('#'):
                                        continue
                                    if isinstance(val, (int, float)):
                                        price_col = col
                                        break
                                    elif isinstance(val, str):
                                        cleaned = val.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '')
                                        if cleaned.isdigit():
                                            price_col = col
                                            break
                                    if price_col:
                                        break
                        except:
                            continue
                    if price_col:
                        break
            
            if not price_col:
                # Tìm các cột khác có chứa price nhưng không phải flag/type/trend/change
                for col in df.columns:
                    col_lower = col.lower()
                    if ('price' in col_lower and 
                        'flag' not in col_lower and 
                        'type' not in col_lower and 
                        'trend' not in col_lower and
                        'change' not in col_lower and
                        'share' not in col_lower):
                        # Kiểm tra xem có phải là số không
                        try:
                            sample_vals = df[col].dropna()
                            if len(sample_vals) > 0:
                                sample_val = sample_vals.iloc[0]
                                # Skip header rows
                                if isinstance(sample_val, str) and sample_val.startswith('#'):
                                    continue
                                if isinstance(sample_val, (int, float)) or \
                                   (isinstance(sample_val, str) and sample_val.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '').isdigit()):
                                    price_col = col
                                    break
                        except:
                            continue
            
            # Nếu không tìm thấy price, tìm các cột change có thể dùng làm inflation
            change_cols = []
            if not price_col:
                for col in df.columns:
                    col_lower = col.lower()
                    if ('change' in col_lower or 'yoy' in col_lower) and 'code' not in col_lower:
                        change_cols.append(col)
            
            commodity_col = None
            for col in df.columns:
                col_lower = col.lower()
                if ('cm_name' in col_lower or 
                    'commodity' in col_lower or 
                    'mainstaplefood' in col_lower or
                    ('food' in col_lower and 'price' not in col_lower and 'basket' not in col_lower)):
                    commodity_col = col
                    break
            
            print(f"   🔍 Detected columns:")
            print(f"      Country: {country_col}")
            print(f"      Year: {year_col}")
            print(f"      Date: {date_col}")
            print(f"      Price: {price_col}")
            print(f"      Commodity: {commodity_col}")
            if change_cols:
                print(f"      Change columns: {change_cols[:3]}")
            
            # Filter data
            filtered_df = df.copy()
            actual_country = None
            
            if country_col:
                # Bỏ qua header rows (thường bắt đầu bằng #)
                filtered_df = filtered_df[~filtered_df[country_col].astype(str).str.startswith('#')]
                
                # Ưu tiên tìm Vietnam với nhiều cách viết
                country_values = filtered_df[country_col].astype(str).str.lower()
                vietnam_variants = ['vietnam', 'viet nam', 'vnm', 'việt nam']
                found_vietnam = False
                
                for variant in vietnam_variants:
                    if variant in country_values.values:
                        filtered_df = filtered_df[country_values == variant]
                        actual_country = filtered_df[country_col].iloc[0] if len(filtered_df) > 0 else variant
                        found_vietnam = True
                        print(f"   ✅ Found Vietnam data: {actual_country}")
                        break
                
                if not found_vietnam:
                    # Lấy country đầu tiên có dữ liệu (bỏ qua header)
                    valid_countries = filtered_df[country_col][~filtered_df[country_col].astype(str).str.startswith('#')]
                    if len(valid_countries) > 0:
                        actual_country = str(valid_countries.iloc[0])
                        filtered_df = filtered_df[filtered_df[country_col] == actual_country]
                        print(f"   ⚠️ Vietnam not found, using: {actual_country}")
                    else:
                        print(f"   ⚠️ No valid country data found")
            
            # CHỈ LẤY NGÀY MỚI NHẤT
            if date_col:
                try:
                    filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
                    # Tìm ngày mới nhất
                    latest_date = filtered_df[date_col].max()
                    if pd.notna(latest_date):
                        filtered_df = filtered_df[filtered_df[date_col] == latest_date]
                        print(f"   ✅ Filtered by latest date: {latest_date.date()}")
                    else:
                        print(f"   ⚠️ Could not determine latest date")
                except Exception as e:
                    print(f"   ⚠️ Error filtering by date: {e}")
            elif year_col:
                try:
                    filtered_df[year_col] = pd.to_numeric(filtered_df[year_col], errors='coerce')
                    # Lấy năm mới nhất
                    latest_year = filtered_df[year_col].max()
                    if pd.notna(latest_year):
                        filtered_df = filtered_df[filtered_df[year_col] == latest_year]
                        print(f"   ✅ Filtered by latest year: {int(latest_year)}")
                    else:
                        print(f"   ⚠️ Could not determine latest year")
                except Exception as e:
                    print(f"   ⚠️ Error filtering by year: {e}")
            
            # Extract data
            wfp_data = []
            
            # Nếu có price column, extract price data
            if price_col:
                for _, row in filtered_df.iterrows():
                    try:
                        price_val = row.get(price_col)
                        # Skip nếu price là NaN hoặc không phải số
                        if pd.isna(price_val):
                            continue
                        
                        # Thử convert sang float
                        try:
                            price_float = float(price_val)
                        except (ValueError, TypeError):
                            continue
                        
                        record = {
                            "source": "WFP",
                            "data_type": "market_price",
                            "country": str(row.get(country_col, actual_country or "Unknown")) if country_col else (actual_country or "Unknown"),
                            "commodity": str(row.get(commodity_col, "Unknown")) if commodity_col else "Unknown",
                            "price": price_float,
                        }
                        
                        if year_col and pd.notna(row.get(year_col)):
                            try:
                                record["year"] = int(row[year_col])
                            except:
                                pass
                        
                        if date_col and pd.notna(row.get(date_col)):
                            try:
                                date_val = row[date_col]
                                if isinstance(date_val, pd.Timestamp):
                                    record["date"] = str(date_val.date())
                                    record["year"] = date_val.year
                                else:
                                    record["date"] = str(date_val)
                            except:
                                pass
                        
                        wfp_data.append(record)
                    except Exception as e:
                        continue
            
            # Nếu không có price nhưng có change columns, extract làm inflation indicators
            elif change_cols:
                print(f"   💡 No price column found, extracting change/inflation indicators instead")
                for _, row in filtered_df.iterrows():
                    try:
                        # Lấy giá trị từ change columns đầu tiên có giá trị
                        change_value = None
                        change_col_used = None
                        for col in change_cols[:3]:  # Lấy 3 cột đầu
                            val = row.get(col)
                            if pd.notna(val):
                                try:
                                    change_value = float(val)
                                    change_col_used = col
                                    break
                                except:
                                    continue
                        
                        if change_value is None:
                            continue
                        
                        record = {
                            "source": "WFP",
                            "data_type": "price_change",  # Dùng làm inflation proxy
                            "country": str(row.get(country_col, actual_country or "Unknown")) if country_col else (actual_country or "Unknown"),
                            "commodity": str(row.get(commodity_col, "Unknown")) if commodity_col else "Unknown",
                            "change_percentage": change_value,
                            "change_type": change_col_used,
                        }
                        
                        if date_col and pd.notna(row.get(date_col)):
                            try:
                                date_val = row[date_col]
                                if isinstance(date_val, pd.Timestamp):
                                    record["date"] = str(date_val.date())
                                    record["year"] = date_val.year
                                else:
                                    record["date"] = str(date_val)
                            except:
                                pass
                        
                        wfp_data.append(record)
                    except Exception as e:
                        continue
            else:
                print(f"   ⚠️ Could not find price or change columns. Available columns: {list(df.columns)}")
            
            print(f"   ✅ Extracted {len(wfp_data)} records")
            return wfp_data
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==================== FAO DATA (National Level) ====================

async def fetch_fao_data(session: aiohttp.ClientSession, domain: str, country_code: str) -> List[Dict]:
    """
    Lấy FAO data từ FAOSTAT API - CHỈ LẤY NĂM MỚI NHẤT
    Domains: CP (Consumer Price Indices), QCL (Crops and livestock products)
    """
    print(f"\n{'='*60}")
    print(f"📊 FAO DATA - Domain: {domain}")
    print(f"{'='*60}")
    
    current_year = datetime.now().year
    
    # Thử nhiều endpoint khác nhau để bypass Cloudflare
    fao_endpoints = [
        f"https://fenixservices.fao.org/faostat/api/v1/en/data/{domain}",
        f"https://www.fao.org/faostat/en/#data/{domain}",
    ]
    
    params = {
        "area": country_code,
        "year": str(current_year),  # Chỉ lấy năm hiện tại
    }
    
    fao_data = None  # Khởi tạo trước
    
    try:
        print(f"   🔍 Querying FAO API...")
        print(f"   Country code: {country_code}")
        print(f"   Year: {current_year} (latest only)")
        
        # Thử dùng requests với session để bypass Cloudflare
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Tạo session với retry strategy
            req_session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504, 521],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            req_session.mount("http://", adapter)
            req_session.mount("https://", adapter)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.fao.org/",
            }
            
            response = req_session.get(fao_endpoints[0], params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Successfully fetched using requests")
            else:
                print(f"   ⚠️ Requests method failed: {response.status_code}")
                # Thử với country code khác nếu Vietnam không có
                if country_code == VIETNAM_CODES["fao"]:
                    print(f"   💡 Trying alternative country codes...")
                    for alt_code in ["5000", "41", "1"]:  # World, Asia, etc.
                        alt_params = params.copy()
                        alt_params["area"] = alt_code
                        alt_response = req_session.get(fao_endpoints[0], params=alt_params, headers=headers, timeout=30)
                        if alt_response.status_code == 200:
                            response = alt_response
                            params = alt_params
                            data = response.json()
                            print(f"   ✅ Using country code: {alt_code}")
                            break
                    else:
                        # Nếu vẫn lỗi, thử không filter country
                        print(f"   💡 Trying without country filter...")
                        no_country_params = {k: v for k, v in params.items() if k != "area"}
                        no_country_response = req_session.get(fao_endpoints[0], params=no_country_params, headers=headers, timeout=30)
                        if no_country_response.status_code == 200:
                            response = no_country_response
                            data = response.json()
                            print(f"   ✅ Using data without country filter")
                        else:
                            print(f"   Response: {no_country_response.text[:200]}")
                            raise Exception("All requests methods failed")
                else:
                    raise Exception("Requests method failed")
            
            # Kiểm tra data sau khi fetch thành công (cho cả requests và aiohttp)
            if "data" not in data:
                print(f"   ⚠️ No data field in response")
                print(f"   Response keys: {list(data.keys())}")
                return []
            
            fao_data = data.get("data", [])
            print(f"   ✅ Received {len(fao_data)} records")
                
        except Exception as req_error:
            print(f"   💡 Requests method failed, trying aiohttp method...")
            print(f"   Error: {req_error}")
            # Fallback to aiohttp
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            
            async with session.get(fao_endpoints[0], params=params, headers=headers, timeout=30) as response:
                if response.status != 200:
                    print(f"   ⚠️ API error: {response.status}")
                    # Thử với country code khác nếu Vietnam không có
                    if country_code == VIETNAM_CODES["fao"]:
                        print(f"   💡 Trying alternative country codes...")
                        for alt_code in ["5000", "41", "1"]:  # World, Asia, etc.
                            alt_params = params.copy()
                            alt_params["area"] = alt_code
                            async with session.get(fao_endpoints[0], params=alt_params, headers=headers, timeout=30) as alt_response:
                                if alt_response.status == 200:
                                    response = alt_response
                                    params = alt_params
                                    print(f"   ✅ Using country code: {alt_code}")
                                    break
                        else:
                            # Nếu vẫn lỗi, thử không filter country
                            print(f"   💡 Trying without country filter...")
                            no_country_params = {k: v for k, v in params.items() if k != "area"}
                            async with session.get(fao_endpoints[0], params=no_country_params, headers=headers, timeout=30) as no_country_response:
                                if no_country_response.status == 200:
                                    response = no_country_response
                                    print(f"   ✅ Using data without country filter")
                                else:
                                    text = await no_country_response.text()
                                    print(f"   Response: {text[:200]}")
                                    return []
                    else:
                        return []
                
                data = await response.json()
            
            # Kiểm tra data sau khi fetch thành công
            if "data" not in data:
                print(f"   ⚠️ No data field in response")
                print(f"   Response keys: {list(data.keys())}")
                return []
            
            fao_data = data.get("data", [])
            print(f"   ✅ Received {len(fao_data)} records")
        except Exception as aio_error:
            print(f"   ❌ All methods failed: {aio_error}")
            return []
        
        # Filter chỉ lấy năm mới nhất (áp dụng cho cả requests và aiohttp)
        if fao_data is None or len(fao_data) == 0:
            print(f"   ⚠️ No data received")
            return []
        
        if fao_data:
            years_in_data = [int(r.get("year", 0)) for r in fao_data if r.get("year")]
            if years_in_data:
                latest_year = max(years_in_data)
                fao_data = [r for r in fao_data if int(r.get("year", 0)) == latest_year]
                print(f"   ✅ Filtered to latest year: {latest_year} ({len(fao_data)} records)")
        
        # Transform to our format
        records = []
        for record in fao_data:
            try:
                transformed = {
                    "source": "FAO",
                    "data_type": "consumer_price_index" if domain == "CP" else "crops_livestock",
                    "domain": domain,
                    "country_code": record.get("area_code"),
                    "country": record.get("area"),
                    "year": int(record.get("year", 0)) if record.get("year") else None,
                    "item": record.get("item"),
                    "value": float(record.get("value", 0)) if record.get("value") and str(record.get("value")).lower() != "null" else None,
                    "unit": record.get("unit"),
                }
                if transformed["value"] is not None and transformed["year"]:
                    records.append(transformed)
            except:
                continue
            
            print(f"   ✅ Extracted {len(records)} valid records")
            return records
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==================== MARKET DATA (Yahoo Finance) ====================

def fetch_yahoo_finance_data(tickers: List[str], period: str = "1wk") -> List[Dict]:
    """
    Lấy dữ liệu từ Yahoo Finance - CHỈ LẤY NGÀY MỚI NHẤT
    Tickers: CL=F (Oil), HRC=F (Steel), ZR=F (Rice), ZW=F (Wheat), ZC=F (Corn), 
             ZS=F (Soybean), SB=F (Sugar), KC=F (Coffee), NG=F (Gas), GC=F (Gold)
    Period: 1wk (1 tuần) cho market data
    """
    print(f"\n{'='*60}")
    print(f"📊 YAHOO FINANCE MARKET DATA")
    print(f"{'='*60}")
    print(f"Period: {period} (latest date only)")
    
    try:
        import yfinance as yf
        
        market_data = []
        
        for ticker_symbol in tickers:
            print(f"   📈 Fetching {ticker_symbol}...")
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period=period)
                
                if hist.empty:
                    print(f"      ⚠️ No data for {ticker_symbol}")
                    continue
                
                # CHỈ LẤY NGÀY MỚI NHẤT
                latest_row = hist.iloc[-1]
                latest_date = hist.index[-1]
                
                record = {
                    "source": "Yahoo Finance",
                    "data_type": "market_price",
                    "ticker": ticker_symbol,
                    "date": str(latest_date.date()),
                    "close": float(latest_row["Close"]),
                    "open": float(latest_row["Open"]),
                    "high": float(latest_row["High"]),
                    "low": float(latest_row["Low"]),
                    "volume": int(latest_row["Volume"]) if pd.notna(latest_row["Volume"]) else 0,
                }
                market_data.append(record)
                
                print(f"      ✅ {ticker_symbol}: ${latest_row['Close']:.2f} ({latest_date.date()})")
            
            except Exception as e:
                print(f"      ❌ Error fetching {ticker_symbol}: {e}")
                continue
        
        print(f"   ✅ Extracted {len(market_data)} records (latest date only)")
        return market_data
    
    except ImportError:
        print("   ⚠️ yfinance not installed. Install with: pip install yfinance")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


# ==================== MAIN FUNCTION ====================

async def main():
    """
    Main function để crawl tất cả macro indicators và ghi vào 3 file riêng biệt
    """
    print("🚀 Starting Macro Indicators Scraper")
    print(f"📁 Output files:")
    print(f"   - {WFP_OUTPUT_FILE}")
    print(f"   - {FAO_OUTPUT_FILE}")
    print(f"   - {MARKET_OUTPUT_FILE}")
    print(f"🎯 Target: Vietnam (fallback: any available)")
    print(f"📅 Period: Latest date/year only")
    print()
    
    async with aiohttp.ClientSession() as session:
        # 1. WFP Food Prices (latest date only, priority Vietnam)
        wfp_data = await fetch_wfp_food_prices(session, country=VIETNAM_CODES["wfp"])
        
        await asyncio.sleep(2)  # Rate limiting
        
        # 2. FAO Consumer Price Indices (latest year only, priority Vietnam)
        fao_cp = await fetch_fao_data(session, domain="CP", country_code=VIETNAM_CODES["fao"])
        
        await asyncio.sleep(2)
        
        # 3. FAO Crops and Livestock (latest year only, priority Vietnam)
        fao_qcl = await fetch_fao_data(session, domain="QCL", country_code=VIETNAM_CODES["fao"])
    
    # 4. Yahoo Finance Market Data (latest date only)
    # Thêm nhiều tickers: Oil, Steel, Rice, Wheat, Corn, Soybean, Sugar, Coffee, Gas, Gold
    market_tickers = [
        "CL=F",   # Crude Oil
        "HRC=F",  # Hot Rolled Coil Steel
        "ZR=F",   # Rice Futures
        "ZW=F",   # Wheat Futures
        "ZC=F",   # Corn Futures
        "ZS=F",   # Soybean Futures
        "SB=F",   # Sugar Futures
        "KC=F",   # Coffee Futures
        "NG=F",   # Natural Gas
        "GC=F",   # Gold Futures
    ]
    market_data = fetch_yahoo_finance_data(market_tickers, period="1wk")
    
    # Tách và lưu thành 3 file riêng
    # 1. WFP Data
    wfp_output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "WFP",
        "total_records": len(wfp_data),
        "data": wfp_data
    }
    
    # 2. FAO Data (gộp CP và QCL)
    fao_all = fao_cp + fao_qcl
    fao_output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "FAO",
        "total_records": len(fao_all),
        "summary": {
            "cp": len(fao_cp),
            "qcl": len(fao_qcl),
        },
        "data": fao_all
    }
    
    # 3. Market Data
    market_output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Yahoo Finance",
        "total_records": len(market_data),
        "data": market_data
    }
    
    # Save to 3 separate JSON files
    try:
        with open(WFP_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(wfp_output, f, indent=4, ensure_ascii=False)
        print(f"\n💾 WFP data saved to {WFP_OUTPUT_FILE}")
        
        with open(FAO_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(fao_output, f, indent=4, ensure_ascii=False)
        print(f"💾 FAO data saved to {FAO_OUTPUT_FILE}")
        
        with open(MARKET_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(market_output, f, indent=4, ensure_ascii=False)
        print(f"💾 Market data saved to {MARKET_OUTPUT_FILE}")
        
        print(f"\n📊 Summary:")
        print(f"   WFP Data: {len(wfp_data)} records")
        print(f"   FAO CP Data: {len(fao_cp)} records")
        print(f"   FAO QCL Data: {len(fao_qcl)} records")
        print(f"   Yahoo Finance: {len(market_data)} records")
        print(f"   Total: {len(wfp_data) + len(fao_all) + len(market_data)} records")
    except Exception as e:
        print(f"\n❌ Error saving data: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Scraper finished.")


if __name__ == "__main__":
    asyncio.run(main())

