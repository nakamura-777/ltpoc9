
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 日本語フォント設定
plt.rcParams['font.family'] = 'Noto Sans CJK JP'

st.title("キャッシュ生産性と現金増減の分析")

# --- 入力：月ごとの現金残高 ---
st.markdown("### 1. 月別 現金残高入力")
months = st.number_input("対象月数", min_value=1, max_value=24, value=6)
cash_data = []
for i in range(months + 1):
    cash = st.number_input(f"{i+1}ヶ月目 期首現金残高（万円）", value=1000 if i == 0 else 0)
    cash_data.append(cash)

# --- 入力：月ごとの製品データ（TP, LT） ---
st.markdown("### 2. 月別 製品データ入力（TP・LT）")
monthly_product_data = {}

for i in range(months):
    st.markdown(f"**{i+1}ヶ月目 製品データ**")
    df = st.data_editor(
        pd.DataFrame([{"製品名": "", "TP（万円）": 0.0, "LT（日）": 1}],
                     columns=["製品名", "TP（万円）", "LT（日）"]),
        key=f"month_{i}",
        num_rows="dynamic"
    )
    monthly_product_data[i] = df

# --- 計算処理 ---
results = []

for i in range(months):
    df = monthly_product_data[i]
    df = df[(df["TP（万円）"] > 0) & (df["LT（日）"] > 0)]
    tp_total = df["TP（万円）"].sum()
    weighted_avg = (df["TP（万円）"] / df["LT（日）"]).sum()
    cash_diff = cash_data[i+1] - cash_data[i]
    results.append({
        "月": f"{i+1}ヶ月目",
        "TP合計（万円）": tp_total,
        "加重平均キャッシュ生産性（TP/LT）": weighted_avg,
        "現金増減額（万円）": cash_diff
    })

# --- 表示 ---
st.markdown("### 3. 分析結果")
result_df = pd.DataFrame(results)
st.dataframe(result_df, use_container_width=True)

# --- グラフ表示 ---
st.markdown("### 4. グラフ分析")
fig, ax = plt.subplots()
ax.scatter(result_df["加重平均キャッシュ生産性（TP/LT）"], result_df["現金増減額（万円）"], s=100)

for i, row in result_df.iterrows():
    ax.annotate(row["月"], (row["加重平均キャッシュ生産性（TP/LT）"], row["現金増減額（万円）"]))

ax.set_xlabel("加重平均キャッシュ生産性")
ax.set_ylabel("現金増減額")
ax.set_title("月別：加重平均キャッシュ生産性と現金増減額の関係")
ax.grid(True)
st.pyplot(fig)
