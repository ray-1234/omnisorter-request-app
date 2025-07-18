import streamlit as st
import requests
import json
from datetime import datetime
import os

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

# 翻訳辞書
TRANSLATE_CATEGORY = {
    'OS機種': 'Model',
    '本体構成': 'Main Configuration',
    '設置容器': 'Container',
    '仕分け商品': 'Sorting Product',
    'オプション': 'Options'
}

TRANSLATE_ITEM = {
    '段': 'Rows', '列': 'Columns', 'ブロック': 'Cells', '間口タイプ': 'Grid Type',
    '短スロープ長さ': 'Short Slope Length', 'スロープ長さ': 'Slope Length',
    '引き出し有無': 'Drawer Availability', '標準/個別': 'Container Type',
    '奥行': 'Depth', '幅': 'Width', '高さ': 'Height',
    '最大奥行': 'Max Depth', '最大幅': 'Max Width', '最大高さ': 'Max Height',
    'DAS': 'DAS', '満杯センサー': 'Full Sensor',
    '追加カート': 'Additional Cart', '追加トート': 'Additional Tote',
    '滑り止めベルト': 'Anti-slip Belt', '薄物対応': 'Thin Item Support',
    '間口数': 'Grid Count', '面数': 'Surface Count'
}

TRANSLATE_VALUE = {
    'S': 'S', 'M': 'M', 'L': 'L', 'mini': 'mini',
    'カート式': 'Cart Type', '固定（棚）式': 'Fixed (Shelf) Type', 'スロープ式': 'Slope Type',
    '標準トート': 'Standard Tote', '個別容器': 'Individual Container', '無し': 'None',
    '有': 'Yes', '無': 'No'
}

@st.cache_data(ttl=300)  # 5分間キャッシュ
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

@st.cache_data(ttl=300)
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
    
    # 顧客でフィルター
    payload = {}
    if customer_id:
        payload = {
            "filter": {
                "property": "顧客",
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
                if page["properties"].get("案件名", {}).get("title"):
                    project_name = page["properties"]["案件名"]["title"][0]["text"]["content"]
                
                projects.append({
                    "id": page["id"],
                    "name": project_name
                })
            return projects
        else:
            st.error(f"案件情報の取得に失敗: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"案件情報取得エラー: {str(e)}")
        return []

def create_new_customer(company_name):
    """新規顧客を顧客企業マスタに作成"""
    customer_db_id = st.secrets.get("CUSTOMER_DB_ID")
    if not customer_db_id:
        return None
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_API_KEY']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    payload = {
        "parent": {"database_id": customer_db_id},
        "properties": {
            "会社名": {
                "title": [{"text": {"content": company_name}}]
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data["id"]
        else:
            st.error(f"顧客作成に失敗: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"顧客作成エラー: {str(e)}")
        return None

def create_new_project(project_name, customer_id):
    """新規案件を案件管理データベースに作成"""
    project_db_id = st.secrets.get("PROJECT_DB_ID")
    if not project_db_id:
        return None
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_API_KEY']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    payload = {
        "parent": {"database_id": project_db_id},
        "properties": {
            "案件名": {
                "title": [{"text": {"content": project_name}}]
            },
            "顧客": {
                "relation": [{"id": customer_id}]
            },
            "開始日": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "ステータス": {
                "select": {"name": "進行中"}
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data["id"]
        else:
            st.error(f"案件作成に失敗: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"案件作成エラー: {str(e)}")
        return None

def save_omnisorter_request(project_id, data):
    """OmniSorter依頼をデータベースに保存"""
    request_db_id = st.secrets.get("OMNISORTER_REQUEST_DB_ID")
    if not request_db_id:
        st.error("OmniSorter依頼データベースIDが設定されていません。")
        return False
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_API_KEY']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    payload = {
        "parent": {"database_id": request_db_id},
        "properties": {
            "案件": {
                "relation": [{"id": project_id}]
            },
            "依頼日": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "依頼種別": {
                "select": {"name": data["依頼種別"]}
            },
            "OS機種": {
                "select": {"name": data.get("OS機種", "未選択")}
            },
            "ステータス": {
                "select": {"name": "依頼中"}
            },
            "見積依頼文": {
                "rich_text": [{"text": {"content": data["見積依頼文"]}}]
            },
            "図面依頼文": {
                "rich_text": [{"text": {"content": data["図面依頼文"]}}]
            },
            "仕様詳細": {
                "rich_text": [{"text": {"content": json.dumps(data["仕様詳細"], ensure_ascii=False, indent=2)}}]
            },
            "備考": {
                "rich_text": [{"text": {"content": data.get("備考", "")}}]
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"OmniSorter依頼保存エラー: {str(e)}")
        return False
    """Notion API接続テスト"""
    try:
        notion_api_key = st.secrets.get("NOTION_API_KEY")
        database_id = st.secrets.get("NOTION_DATABASE_ID")
        
        if not notion_api_key:
            return False, "NOTION_API_KEYが設定されていません"
        if not database_id:
            return False, "NOTION_DATABASE_IDが設定されていません"
        
        # データベース情報を取得してテスト
        url = f"https://api.notion.com/v1/databases/{database_id}"
        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Notion-Version": "2022-06-28"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return True, "接続成功"
        elif response.status_code == 401:
            return False, "APIキーが無効です"
        elif response.status_code == 404:
            return False, "データベースが見つかりません"
        else:
            return False, f"エラー: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"接続エラー: {str(e)}"

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
    
    # プロパティを安全に構築
    properties = {}
    
    # 必須フィールド - 顧客名をタイトルに設定
    if data.get("顧客名"):
        properties["顧客名"] = {
            "title": [{"text": {"content": str(data["顧客名"])[:100]}}]
        }
    
    # その他のフィールド
    if data.get("案件名"):
        properties["案件名"] = {
            "rich_text": [{"text": {"content": str(data["案件名"])[:2000]}}]
        }
    
    if data.get("依頼日"):
        properties["依頼日"] = {
            "date": {"start": str(data["依頼日"])}
        }
    
    if data.get("依頼種別"):
        properties["依頼種別"] = {
            "select": {"name": str(data["依頼種別"])}
        }
    
    if data.get("OS機種"):
        properties["OS機種"] = {
            "select": {"name": str(data["OS機種"])}
        }
    
    properties["ステータス"] = {
        "select": {"name": "依頼中"}
    }
    
    # 長いテキストフィールドは分割して保存
    if data.get("見積依頼文"):
        text = str(data["見積依頼文"])[:2000]
        properties["見積依頼文"] = {
            "rich_text": [{"text": {"content": text}}]
        }
    
    if data.get("図面依頼文"):
        text = str(data["図面依頼文"])[:2000]
        properties["図面依頼文"] = {
            "rich_text": [{"text": {"content": text}}]
        }
    
    if data.get("仕様詳細"):
        specs_text = json.dumps(data["仕様詳細"], ensure_ascii=False, indent=2)[:2000]
        properties["仕様詳細"] = {
            "rich_text": [{"text": {"content": specs_text}}]
        }
    
    if data.get("備考"):
        properties["備考"] = {
            "rich_text": [{"text": {"content": str(data["備考"])[:2000]}}]
        }
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Notion API エラー: {response.status_code}")
            st.error(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        st.error("リクエストがタイムアウトしました")
        return False
    except Exception as e:
        st.error(f"保存エラー: {str(e)}")
        return False

def generate_quotation_text(form_data):
    """見積依頼文生成"""
    quotation_items = [item for item in FORM_ITEMS if "見積" in item["必要種別"]]
    
    content = "OmniSorter見積依頼\n\n【基本仕様】\n"
    
    # 自動計算値を追加
    grid_count = form_data.get("間口数")
    surface_count = form_data.get("面数")
    
    # カテゴリごとにグループ化
    groups = {}
    for item in quotation_items:
        key = f"{item['大項目']}-{item['小項目']}"
        if key in form_data and form_data[key]:
            category = item["大項目"]
            if category not in groups:
                groups[category] = []
            
            label = "" if item["小項目"] == "-" else item["小項目"]
            value = form_data[key]
            if "mm単位" in item["備考"]:
                value = f"{value}[mm]"
            
            groups[category].append({"label": label, "value": value})
    
    # 自動計算値を本体構成に追加
    if grid_count:
        if "本体構成" not in groups:
            groups["本体構成"] = []
        groups["本体構成"].append({"label": "間口数", "value": f"{grid_count}口"})
    
    for category, items in groups.items():
        content += f"{category}:\n"
        for item in items:
            if item["label"]:
                content += f"  {item['label']}: {item['value']}\n"
            else:
                content += f"  {item['value']}\n"
        content += "\n"
    
    content += "上記仕様にて見積をお願いいたします。\nよろしくお願いいたします。"
    return content

def generate_drawing_text(form_data):
    """図面依頼文生成（英語）"""
    drawing_items = [item for item in FORM_ITEMS if "図面" in item["必要種別"]]
    
    content = "OmniSorter Drawing Request\n\n【Specifications】\n"
    
    # 自動計算値を追加
    grid_count = form_data.get("間口数")
    
    # カテゴリごとにグループ化（英語）
    groups = {}
    for item in drawing_items:
        key = f"{item['大項目']}-{item['小項目']}"
        if key in form_data and form_data[key]:
            category = TRANSLATE_CATEGORY.get(item["大項目"], item["大項目"])
            if category not in groups:
                groups[category] = []
            
            label = "" if item["小項目"] == "-" else TRANSLATE_ITEM.get(item["小項目"], item["小項目"])
            value = TRANSLATE_VALUE.get(form_data[key], form_data[key])
            if "mm単位" in item["備考"]:
                value = f"{value}[mm]"
            
            groups[category].append({"label": label, "value": value})
    
    # 自動計算値を追加
    if grid_count:
        if "Main Configuration" not in groups:
            groups["Main Configuration"] = []
        groups["Main Configuration"].append({"label": "Grid Count", "value": f"{grid_count} grids"})
    
    for category, items in groups.items():
        content += f"{category}:\n"
        for item in items:
            if item["label"]:
                content += f"  {item['label']}: {item['value']}\n"
            else:
                content += f"  {item['value']}\n"
        content += "\n"
    
    content += "Please provide technical drawings based on the above specifications.\n"
    content += "Thank you for your cooperation.\n\nBest regards,"
    return content

def should_show_field(item, form_data):
    """条件付きフィールドの表示判定"""
    if "スロープタイプの場合のみ" in item["備考"]:
        return form_data.get("本体構成-間口タイプ") == "スロープ式"
    elif "カート式の場合のみ" in item["備考"]:
        return form_data.get("本体構成-間口タイプ") == "カート式"
    elif "標準トートの場合のみ" in item["備考"]:
        return form_data.get("設置容器-標準/個別") == "標準トート"
    return True

def main():
    st.markdown('<h1 class="main-header">📦 OmniSorter 見積・図面依頼システム</h1>', unsafe_allow_html=True)
    
    # Notion接続テスト
    with st.sidebar:
        st.header("🔧 システム状態")
        if st.button("接続テスト"):
            try:
                success, message = test_notion_connection()
                if success:
                    st.success("接続テスト結果:")
                    st.text(message)
                else:
                    st.error("接続テスト結果:")
                    st.text(message)
            except Exception as e:
                st.error(f"テスト実行エラー: {str(e)}")
        
        # 設定確認
        st.subheader("📋 設定確認")
        api_key = st.secrets.get("NOTION_API_KEY", "未設定")
        st.text(f"APIキー: {api_key[:10]}..." if api_key != "未設定" else "APIキー: 未設定")
        
        # データベースID確認
        db_ids = {
            "簡易版DB": st.secrets.get("NOTION_DATABASE_ID"),
            "顧客マスタ": st.secrets.get("CUSTOMER_DB_ID"),
            "案件マスタ": st.secrets.get("PROJECT_DB_ID"),
            "依頼DB": st.secrets.get("OMNISORTER_REQUEST_DB_ID")
        }
        
        for name, db_id in db_ids.items():
            status = "✅ 設定済み" if db_id else "❌ 未設定"
            st.text(f"{name}: {status}")
    
    # セッション状態の初期化
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {}
    
    # タブ設定
    tab1, tab2, tab3 = st.tabs(["📝 入力フォーム", "💰 見積依頼文", "📐 図面依頼文"])
    
    with tab1:
        # マスタ連携の設定
        use_master_sync = st.checkbox("既存マスタと連携する", value=False, 
                                    help="顧客企業マスタと案件管理データベースと連携します")
        
        if use_master_sync:
            # マスタ連携モード
            st.markdown('<div class="section-header"><h3>🏢 顧客・案件選択</h3></div>', unsafe_allow_html=True)
            
            # 顧客選択
            customers = fetch_customers()
            if not customers:
                st.warning("顧客企業マスタからデータを取得できません。接続設定を確認してください。")
                return
                
            customer_options = ["--- 新規顧客 ---"] + [f"{c['name']}" for c in customers]
            
            selected_customer_index = st.selectbox(
                "顧客選択（会社名）",
                range(len(customer_options)),
                format_func=lambda x: customer_options[x]
            )
            
            selected_customer = None
            if selected_customer_index == 0:
                # 新規顧客
                new_company_name = st.text_input("新規会社名", placeholder="株式会社○○")
                if new_company_name:
                    if st.button("💾 新規顧客を作成"):
                        customer_id = create_new_customer(new_company_name)
                        if customer_id:
                            st.success(f"顧客「{new_company_name}」を作成しました")
                            st.cache_data.clear()
                            st.rerun()
            else:
                selected_customer = customers[selected_customer_index - 1]
                st.info(f"選択された顧客: {selected_customer['name']}")
            
            # 案件選択
            selected_project = None
            if selected_customer:
                projects = fetch_projects(selected_customer['id'])
                project_options = ["--- 新規案件 ---"] + [f"{p['name']}" for p in projects]
                
                selected_project_index = st.selectbox(
                    "案件選択（案件名）",
                    range(len(project_options)),
                    format_func=lambda x: project_options[x]
                )
                
                if selected_project_index == 0:
                    # 新規案件
                    new_project_name = st.text_input("新規案件名", placeholder="○○倉庫OmniSorter導入")
                    if new_project_name:
                        if st.button("💾 新規案件を作成"):
                            project_id = create_new_project(new_project_name, selected_customer['id'])
                            if project_id:
                                st.success(f"案件「{new_project_name}」を作成しました")
                                st.cache_data.clear()
                                st.rerun()
                else:
                    selected_project = projects[selected_project_index - 1]
                    st.info(f"選択された案件: {selected_project['name']}")
            
            # 依頼種別と備考
            request_type = st.selectbox("依頼種別", ["両方", "見積のみ", "図面のみ"])
            notes = st.text_area("備考", placeholder="特記事項があれば記入してください")
            
        else:
            # 簡易モード
            st.markdown('<div class="section-header"><h3>案件情報</h3></div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                customer_name = st.text_input("顧客名 *")
            
            with col2:
                project_name = st.text_input("案件名 *")
            
            with col3:
                request_type = st.selectbox("依頼種別", ["両方", "見積のみ", "図面のみ"])
            
            notes = st.text_area("備考", placeholder="特記事項があれば記入してください")
        
        # 仕様入力
        st.markdown('<div class="section-header"><h3>仕様入力</h3></div>', unsafe_allow_html=True)
        
        # カテゴリごとに表示
        categories = {}
        for item in FORM_ITEMS:
            if item["大項目"] not in categories:
                categories[item["大項目"]] = []
            categories[item["大項目"]].append(item)
        
        cols = st.columns(2)
        col_index = 0
        
        for category, items in categories.items():
            with cols[col_index % 2]:
                st.subheader(category)
                
                for item in items:
                    if not should_show_field(item, st.session_state.form_data):
                        continue
                    
                    key = f"{item['大項目']}-{item['小項目']}"
                    label = item["大項目"] if item["小項目"] == "-" else item["小項目"]
                    
                    if item["備考"]:
                        label += f" ({item['備考']})"
                    
                    if item["取り得る値"] and item["取り得る値"] not in ["(任意)", "", "(選択)"]:
                        # 通常の選択肢
                        options = [""] + item["取り得る値"].split(",")
                        current_value = st.session_state.form_data.get(key, "")
                        selected = st.selectbox(label, options, 
                                              index=options.index(current_value) if current_value in options else 0,
                                              key=key)
                        if selected:
                            st.session_state.form_data[key] = selected
                        elif key in st.session_state.form_data:
                            del st.session_state.form_data[key]
                    
                    elif item["小項目"] == "追加カート":
                        # 追加カート特別処理
                        surface_count = calculate_surface_count(st.session_state.form_data.get("本体構成-ブロック"))
                        options = get_cart_options(surface_count)
                        
                        current_value = st.session_state.form_data.get(key, "")
                        selected = st.selectbox(label, options, 
                                              index=options.index(current_value) if current_value in options else 0,
                                              key=key)
                        
                        if selected == "自由入力":
                            custom_value = st.number_input("カート数を入力", min_value=0, key=f"{key}_custom")
                            if custom_value > 0:
                                st.session_state.form_data[key] = f"{custom_value}台"
                        elif selected:
                            st.session_state.form_data[key] = selected
                        elif key in st.session_state.form_data:
                            del st.session_state.form_data[key]
                    
                    elif item["小項目"] == "追加トート":
                        # 追加トート特別処理
                        grid_count = calculate_grid_count(
                            st.session_state.form_data.get("本体構成-段"),
                            st.session_state.form_data.get("本体構成-列"),
                            st.session_state.form_data.get("本体構成-ブロック")
                        )
                        options = get_tote_options(grid_count)
                        
                        current_value = st.session_state.form_data.get(key, "")
                        selected = st.selectbox(label, options, 
                                              index=options.index(current_value) if current_value in options else 0,
                                              key=key)
                        
                        if selected == "自由入力":
                            custom_value = st.number_input("トート数を入力", min_value=0, key=f"{key}_custom")
                            if custom_value > 0:
                                st.session_state.form_data[key] = f"{custom_value}個"
                        elif selected:
                            st.session_state.form_data[key] = selected
                        elif key in st.session_state.form_data:
                            del st.session_state.form_data[key]
                    
                    else:
                        # 自由入力の場合
                        input_type = "number" if any(unit in item["備考"] for unit in ["mm単位", "台単位", "個単位"]) else "text"
                        current_value = st.session_state.form_data.get(key, "")
                        
                        if input_type == "number":
                            # 空欄を許可する数値入力
                            value = st.text_input(label, value=current_value, key=key, 
                                                placeholder="数値を入力（空欄可）")
                            if value and value.isdigit():
                                st.session_state.form_data[key] = value
                            elif not value and key in st.session_state.form_data:
                                del st.session_state.form_data[key]
                        else:
                            value = st.text_input(label, value=current_value, key=key)
                            if value:
                                st.session_state.form_data[key] = value
                            elif key in st.session_state.form_data:
                                del st.session_state.form_data[key]
                
                # 自動計算値の表示
                if category == "本体構成":
                    # 間口数計算
                    rows = st.session_state.form_data.get("本体構成-段")
                    cols = st.session_state.form_data.get("本体構成-列")
                    blocks = st.session_state.form_data.get("本体構成-ブロック")
                    
                    grid_count = calculate_grid_count(rows, cols, blocks)
                    surface_count = calculate_surface_count(blocks)
                    
                    if grid_count > 0:
                        st.markdown(f'<div class="calculated-value">🔢 間口数: {grid_count}口（自動計算）</div>', 
                                  unsafe_allow_html=True)
                        st.session_state.form_data["間口数"] = grid_count
                    
                    if surface_count > 0:
                        st.markdown(f'<div class="calculated-value">📐 面数: {surface_count}面（自動計算）</div>', 
                                  unsafe_allow_html=True)
                        st.session_state.form_data["面数"] = surface_count
            
            col_index += 1
        
        # 保存ボタン
        st.markdown("---")
        
        if use_master_sync:
            # マスタ連携版の保存
            if st.button("💾 マスタ連携で保存", type="primary"):
                if not selected_project:
                    st.error("案件を選択してください。")
                else:
                    # 依頼文生成
                    quotation_text = generate_quotation_text(st.session_state.form_data)
                    drawing_text = generate_drawing_text(st.session_state.form_data)
                    
                    # 保存用データ
                    save_data = {
                        "依頼種別": request_type,
                        "OS機種": st.session_state.form_data.get("OS機種-", "未選択"),
                        "見積依頼文": quotation_text,
                        "図面依頼文": drawing_text,
                        "仕様詳細": st.session_state.form_data,
                        "備考": notes
                    }
                    
                    if save_omnisorter_request(selected_project['id'], save_data):
                        st.success("✅ マスタ連携でOmniSorter依頼が正常に保存されました！")
                        st.session_state.form_data = {}
                        st.rerun()
                    else:
                        st.error("❌ 保存に失敗しました。")
        else:
            # 簡易版の保存
            if st.button("💾 Notionに保存", type="primary"):
                if not customer_name or not project_name:
                    st.error("顧客名と案件名は必須です。")
                else:
                    # 依頼文生成
                    quotation_text = generate_quotation_text(st.session_state.form_data)
                    drawing_text = generate_drawing_text(st.session_state.form_data)
                    
                    # Notion保存用データ
                    notion_data = {
                        "顧客名": customer_name,
                        "案件名": project_name,
                        "依頼日": datetime.now().strftime("%Y-%m-%d"),
                        "依頼種別": request_type,
                        "OS機種": st.session_state.form_data.get("OS機種-", "未選択"),
                        "見積依頼文": quotation_text,
                        "図面依頼文": drawing_text,
                        "仕様詳細": st.session_state.form_data,
                        "備考": notes
                    }
                    
                    if save_to_notion(notion_data):
                        st.markdown('<div class="success-message">✅ Notionに正常に保存されました！</div>', unsafe_allow_html=True)
                        st.session_state.form_data = {}
                        st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ 保存に失敗しました。設定を確認してください。</div>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("見積依頼文")
        quotation_text = generate_quotation_text(st.session_state.form_data)
        st.text_area("", value=quotation_text, height=400, key="quotation_display")
        
        if st.button("📋 クリップボードにコピー", key="copy_quotation"):
            st.code(quotation_text)
            st.success("上記テキストをコピーしてご利用ください。")
    
    with tab3:
        st.subheader("図面依頼文（英語）")
        drawing_text = generate_drawing_text(st.session_state.form_data)
        st.text_area("", value=drawing_text, height=400, key="drawing_display")
        
        if st.button("📋 クリップボードにコピー", key="copy_drawing"):
            st.code(drawing_text)
            st.success("上記テキストをコピーしてご利用ください。")

    # デバッグ情報（開発用）
    with st.expander("🔍 デバッグ情報（開発用）"):
        st.write("フォームデータ:", st.session_state.form_data)
        st.write("案件情報:", st.session_state.project_info)

if __name__ == "__main__":
    main()