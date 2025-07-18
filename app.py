import streamlit as st
import requests
import json
from datetime import datetime

# Streamlit設定
st.set_page_config(
    page_title="OmniSorter 見積・図面依頼システム",
    page_icon="📦",
    layout="wide"
)

# スタイル設定
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #1f2937;
    margin-bottom: 2rem;
}
.section-header {
    background-color: #f3f4f6;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    color: #374151;
}
.calculated-value {
    background-color: #e0f2fe;
    padding: 0.5rem;
    border-radius: 0.25rem;
    border: 1px solid #81d4fa;
    color: #01579b;
    font-weight: bold;
}
.success-message {
    background-color: #d1fae5;
    border: 1px solid #34d399;
    padding: 1rem;
    border-radius: 0.5rem;
    color: #065f46;
}
.error-message {
    background-color: #fee2e2;
    border: 1px solid #f87171;
    padding: 1rem;
    border-radius: 0.5rem;
    color: #991b1b;
}
</style>
""", unsafe_allow_html=True)

# API関数群
def test_database_connection(db_name, db_id, api_key):
    """個別データベース接続テスト"""
    url = f"https://api.notion.com/v1/databases/{db_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            properties = list(data.get("properties", {}).keys())
            return f"✅ {db_name}: 接続成功\nプロパティ: {properties}"
        elif response.status_code == 401:
            return f"❌ {db_name}: APIキーが無効"
        elif response.status_code == 404:
            return f"❌ {db_name}: データベースが見つかりません"
        else:
            return f"❌ {db_name}: エラー {response.status_code}"
    except Exception as e:
        return f"❌ {db_name}: 接続エラー - {str(e)}"

def test_notion_connection():
    """Notion API接続テスト"""
    try:
        notion_api_key = st.secrets.get("NOTION_API_KEY")
        
        if not notion_api_key:
            return False, "NOTION_API_KEYが設定されていません"
        
        results = []
        
        # 簡易版DB
        simple_db_id = st.secrets.get("NOTION_DATABASE_ID")
        if simple_db_id:
            results.append(test_database_connection("OmniSorter依頼DB", simple_db_id, notion_api_key))
        else:
            results.append("❌ OmniSorter依頼DB: 未設定")
        
        # マスタ連携用DB
        customer_db_id = st.secrets.get("CUSTOMER_DB_ID")
        if customer_db_id:
            results.append(test_database_connection("顧客企業マスタ", customer_db_id, notion_api_key))
        else:
            results.append("⚠️ 顧客企業マスタ: 未設定")
        
        project_db_id = st.secrets.get("PROJECT_DB_ID")
        if project_db_id:
            results.append(test_database_connection("案件管理データベース", project_db_id, notion_api_key))
        else:
            results.append("⚠️ 案件管理データベース: 未設定")
        
        has_success = any("✅" in result for result in results)
        return has_success, "\n\n".join(results)
            
    except Exception as e:
        return False, f"全体エラー: {str(e)}"

def fetch_customers():
    """顧客企業マスタから顧客一覧を取得"""
    customer_db_id = st.secrets.get("CUSTOMER_DB_ID")
    if not customer_db_id:
        return []
    
    url = f"https://api.notion.com/v1/databases/{customer_db_id}/query"
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_API_KEY']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200:
            data = response.json()
            customers = []
            for page in data.get("results", []):
                company_name = ""
                if page["properties"].get("会社名", {}).get("title"):
                    company_name = page["properties"]["会社名"]["title"][0]["text"]["content"]
                
                customers.append({
                    "id": page["id"],
                    "name": company_name
                })
            return customers
        else:
            st.error(f"顧客情報の取得に失敗: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"顧客情報取得エラー: {str(e)}")
        return []

def fetch_projects(customer_id=None):
    """案件管理データベースから案件一覧を取得"""
    project_db_id = st.secrets.get("PROJECT_DB_ID")
    if not project_db_id:
        return []
    
    url = f"https://api.notion.com/v1/databases/{project_db_id}/query"
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_API_KEY']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 顧客でフィルター（正しいプロパティ名「顧客企業」を使用）
    payload = {}
    if customer_id:
        payload = {
            "filter": {
                "property": "顧客企業",
                "relation": {
                    "contains": customer_id
                }
            }
        }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            projects = []
            for page in data.get("results", []):
                project_name = ""
                
                # タイトルプロパティを自動検出
                for prop_name, prop_data in page["properties"].items():
                    if prop_data.get("type") == "title":
                        if prop_data.get("title") and len(prop_data["title"]) > 0:
                            project_name = prop_data["title"][0]["text"]["content"]
                            break
                
                if project_name:
                    projects.append({
                        "id": page["id"],
                        "name": project_name
                    })
            
            return projects
        else:
            st.error(f"案件情報の取得に失敗: {response.status_code}")
            st.error(f"レスポンス: {response.text}")
            return []
    except Exception as e:
        st.error(f"案件情報取得エラー: {str(e)}")
        return []

# フォーム項目データ
FORM_ITEMS = [
    {"大項目": "OS機種", "小項目": "-", "必要種別": "見積,図面", "取り得る値": "S,M,L,mini", "備考": ""},
    {"大項目": "本体構成", "小項目": "段", "必要種別": "見積,図面", "取り得る値": "2,3,4,5", "備考": ""},
    {"大項目": "本体構成", "小項目": "列", "必要種別": "見積,図面", "取り得る値": "3,4,5", "備考": ""},
    {"大項目": "本体構成", "小項目": "ブロック", "必要種別": "見積,図面", "取り得る値": "(任意)", "備考": "最大10"},
    {"大項目": "本体構成", "小項目": "間口タイプ", "必要種別": "見積,図面", "取り得る値": "カート式,固定（棚）式,スロープ式", "備考": ""},
    {"大項目": "本体構成", "小項目": "短スロープ長さ", "必要種別": "見積,図面", "取り得る値": "", "備考": "mm単位"},
    {"大項目": "本体構成", "小項目": "スロープ長さ", "必要種別": "見積,図面", "取り得る値": "", "備考": "mm単位　※スロープタイプの場合のみ"},
    {"大項目": "本体構成", "小項目": "引き出し有無", "必要種別": "見積,図面", "取り得る値": "有,無", "備考": "※スロープタイプの場合のみ"},
    {"大項目": "設置容器", "小項目": "標準/個別", "必要種別": "見積,図面", "取り得る値": "標準トート,個別容器,無し", "備考": ""},
    {"大項目": "設置容器", "小項目": "奥行", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "設置容器", "小項目": "幅", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "設置容器", "小項目": "高さ", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "仕分け商品", "小項目": "最大奥行", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "仕分け商品", "小項目": "最大幅", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "仕分け商品", "小項目": "最大高さ", "必要種別": "図面", "取り得る値": "(任意)", "備考": "mm単位"},
    {"大項目": "オプション", "小項目": "DAS", "必要種別": "見積,図面", "取り得る値": "有,無", "備考": ""},
    {"大項目": "オプション", "小項目": "満杯センサー", "必要種別": "見積,図面", "取り得る値": "有,無", "備考": ""},
    {"大項目": "オプション", "小項目": "追加カート", "必要種別": "見積", "取り得る値": "(選択)", "備考": "※カート式の場合のみ"},
    {"大項目": "オプション", "小項目": "追加トート", "必要種別": "見積", "取り得る値": "(選択)", "備考": "※標準トートの場合のみ"},
    {"大項目": "オプション", "小項目": "滑り止めベルト", "必要種別": "見積", "取り得る値": "有,無", "備考": ""},
    {"大項目": "オプション", "小項目": "薄物対応", "必要種別": "見積,図面", "取り得る値": "有,無", "備考": ""}
]

# 計算関数
def calculate_grid_count(rows, cols, blocks):
    """間口数を計算（段×列×2×ブロック数）"""
    if rows and cols and blocks:
        try:
            return int(rows) * int(cols) * 2 * int(blocks)
        except (ValueError, TypeError):
            return 0
    return 0

def calculate_surface_count(blocks):
    """面数を計算（ブロック数×2）"""
    if blocks:
        try:
            return int(blocks) * 2
        except (ValueError, TypeError):
            return 0
    return 0

def get_cart_options(surface_count):
    """追加カート選択肢を生成"""
    if surface_count <= 0:
        return [""]
    
    options = [""]
    for multiplier in [0.5, 1, 1.5, 2]:
        value = int(surface_count * multiplier)
        options.append(f"{value}台 ({multiplier}倍)")
    options.append("自由入力")
    return options

def get_tote_options(grid_count):
    """追加トート選択肢を生成"""
    if grid_count <= 0:
        return [""]
    
    options = [""]
    for multiplier in [0.5, 1, 1.5, 2]:
        value = int(grid_count * multiplier)
        options.append(f"{value}個 ({multiplier}倍)")
    options.append("自由入力")
    return options

def save_to_notion(data):
    """Notionデータベースに保存（簡易版）"""
    notion_api_key = st.secrets.get("NOTION_API_KEY")
    database_id = st.secrets.get("NOTION_DATABASE_ID")
    
    if not notion_api_key or not database_id:
        st.error("Notion設定が不完全です。NOTION_API_KEYとNOTION_DATABASE_IDを設定してください。")
        return False
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    properties = {}
    
    if data.get("顧客名