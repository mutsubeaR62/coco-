import streamlit as st

# 商品データ（仮）
products = [
    {"id": "R001", "name": "ロースカツ", "standard": 50, "stock": 30, "unit": {"box": 10}, "memo": ""},
    {"id": "C001", "name": "チキンカツ", "standard": 36, "stock": 30, "unit": {"box": 6}, "memo": ""},
    {"id": "CR001", "name": "クリームコロッケ", "standard": 12, "stock": 9, "unit": {"box": 4}, "memo": ""}
]

# 発注数計算
def calculate_order(product,stock):
    shortage = product["standard"] - stock
    if shortage > 0:
        return -(-shortage // product["unit"]["box"])  # 箱単位に切り上げ
    return 0

st.title("発注システム")

col1,col2=st.columns([3,1])
with col1:
    search=st.text_input("商品検索")
with col2:
    if st.button("全商品表示"):
        search=""



# 商品リスト表示
for p in products:
    if search in p["name"]:
        st.subheader(p["name"])
        
        # 在庫入力
        stock = st.number_input(f"{p['name']} 在庫数", value=0, step=1)
        
        
        # 発注数計算
        shortage = p["standard"] - stock
        order = calculate_order(p, stock)
        st.write(f"不足: {shortage}袋→ 発注: {order}箱")
        
        # メモ入力
        memo = st.text_area(f"{p['name']} メモ", value=p["memo"])
        p["memo"] = memo