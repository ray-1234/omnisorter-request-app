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
    {"大項目": "オプション", "小項目": "追加カート", "必要種別": "見積", "取り得る値": "(任意)", "備考": "台単位　※カート式の場合のみ"},
    {"大項目": "オプション", "小項目": "追加トート", "必要種別": "見積", "取り得る値": "(任意)", "備考": "個単位　※標準トートの場合のみ"},
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
    '滑り止めベルト': 'Anti-slip Belt', '薄物対応': 'Thin Item Support'
}

TRANSLATE_VALUE = {
    'S': 'S', 'M': 'M', 'L': 'L', 'mini': 'mini',
    'カート式': 'Cart Type', '固定（棚）式': 'Fixed (Shelf) Type', 'スロープ式': 'Slope Type',
    '標準トート': 'Standard Tote', '個別容器': 'Individual Container', '無し': 'None',
    '有': 'Yes', '無': 'No'
}

def save_to_notion(data):
    """Notionデータベースに保存"""
    notion_api_key = st.secrets.get("NOTION_API_KEY")
    database_id = st.secrets.get("NOTION_DATABASE_ID")
    
    if not notion_api_key or not database_id:
        st.error("Notion APIキーまたはデータベースIDが設定されていません。")
        return False
    
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "顧客名": {
                "title": [{"text": {"content": data["顧客名"]}}]
            },
            "案件名": {
                "rich_text": [{"text": {"content": data["案件名"]}}]
            },
            "依頼日": {
                "date": {"start": data["依頼日"]}
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
        st.error(f"Notion保存エラー: {str(e)}")
        return False

def generate_quotation_text(form_data):
    """見積依頼文生成"""
    quotation_items = [item for item in FORM_ITEMS if "見積" in item["必要種別"]]
    
    content = "OmniSorter見積依頼\n\n【基本仕様】\n"
    
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
    
    # セッション状態の初期化
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {}
    
    # タブ設定
    tab1, tab2, tab3 = st.tabs(["📝 入力フォーム", "💰 見積依頼文", "📐 図面依頼文"])
    
    with tab1:
        # 案件情報
        st.markdown('<div class="section-header"><h3>案件情報</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            customer_name = st.text_input("顧客名 *", value=st.session_state.project_info.get("顧客名", ""))
            st.session_state.project_info["顧客名"] = customer_name
        
        with col2:
            project_name = st.text_input("案件名 *", value=st.session_state.project_info.get("案件名", ""))
            st.session_state.project_info["案件名"] = project_name
        
        with col3:
            request_type = st.selectbox("依頼種別", ["両方", "見積のみ", "図面のみ"], 
                                      index=["両方", "見積のみ", "図面のみ"].index(st.session_state.project_info.get("依頼種別", "両方")))
            st.session_state.project_info["依頼種別"] = request_type
        
        notes = st.text_area("備考", value=st.session_state.project_info.get("備考", ""))
        st.session_state.project_info["備考"] = notes
        
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
                    
                    if item["取り得る値"] and item["取り得る値"] not in ["(任意)", ""]:
                        # 選択肢がある場合
                        options = [""] + item["取り得る値"].split(",")
                        current_value = st.session_state.form_data.get(key, "")
                        selected = st.selectbox(label, options, 
                                              index=options.index(current_value) if current_value in options else 0,
                                              key=key)
                        if selected:
                            st.session_state.form_data[key] = selected
                        elif key in st.session_state.form_data:
                            del st.session_state.form_data[key]
                    else:
                        # 自由入力の場合
                        input_type = "number" if any(unit in item["備考"] for unit in ["mm単位", "台単位", "個単位"]) else "text"
                        current_value = st.session_state.form_data.get(key, "")
                        
                        if input_type == "number":
                            value = st.number_input(label, value=int(current_value) if current_value and current_value.isdigit() else 0, key=key)
                            if value > 0:
                                st.session_state.form_data[key] = str(value)
                            elif key in st.session_state.form_data:
                                del st.session_state.form_data[key]
                        else:
                            value = st.text_input(label, value=current_value, key=key)
                            if value:
                                st.session_state.form_data[key] = value
                            elif key in st.session_state.form_data:
                                del st.session_state.form_data[key]
            
            col_index += 1
        
        # 保存ボタン
        st.markdown("---")
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
                    # フォームリセット
                    st.session_state.form_data = {}
                    st.session_state.project_info = {}
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

if __name__ == "__main__":
    main()