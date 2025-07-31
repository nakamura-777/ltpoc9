
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# フォント設定（日本語対応）
plt.rcParams["font.family"] = "Noto Sans CJK JP"

st.title("出荷量を加味したキャッシュフロー生産性と現金増減の関係分析")

# 1. 月数の入力と現金残高入力
months = st.number_input("分析対象月数", min_value=1, max_value=24, value=6)
cash_balances = []
for i in range(months + 1):
    cash = st.number_input(f"{i+1}ヶ月目 期首現金残高（万円）", value=1000 if i == 0 else 0)
    cash_balances.append(cash)

# 2. 製品データ入力（TP, LT, 出荷数）
st.markdown("### 月別 製品データ入力（TP・LT・出荷数）")
monthly_product_data = {}

for i in range(months):
    st.markdown(f"**{i+1}ヶ月目 製品データ**")
    df = st.data_editor(
        pd.DataFrame([{"製品名": "", "TP（万円）": 0.0, "LT（日）": 1, "出荷数": 0}],
                     columns=["製品名", "TP（万円）", "LT（日）", "出荷数"]),
        key=f"month_{i}",
        num_rows="dynamic"
    )
    monthly_product_data[i] = df

# 3. 集計処理
results = []

for i in range(months):
    df = monthly_product_data[i]
    df = df[(df["TP（万円）"] > 0) & (df["LT（日）"] > 0) & (df["出荷数"] > 0)]

    tp_total = (df["TP（万円）"] * df["出荷数"]).sum()
    lt_total = (df["LT（日）"] * df["出荷数"]).sum()
    weighted_tp_lt = tp_total / lt_total if lt_total > 0 else 0
    cash_change = cash_balances[i+1] - cash_balances[i]

    results.append({
        "月": f"{i+1}ヶ月目",
        "スループット総量（万円）": tp_total,
        "LT加重総和（日）": lt_total,
        "加重平均キャッシュ生産性（TP/LT）": round(weighted_tp_lt, 2),
        "現金増減額（万円）": cash_change
    })

# 4. 表形式で表示
st.markdown("### 集計結果")
result_df = pd.DataFrame(results)
st.dataframe(result_df, use_container_width=True)

# 5. グラフ表示
st.markdown("### グラフ：キャッシュフロー生産性 vs 現金増減")
fig, ax = plt.subplots()
x = result_df["加重平均キャッシュ生産性（TP/LT）"]
y = result_df["現金増減額（万円）"]
ax.scatter(x, y, s=100)

# 回帰直線
if len(x) >= 2:
    import numpy as np
    slope, intercept = np.polyfit(x, y, 1)
    ax.plot(x, slope * x + intercept, linestyle="--", color="gray", label="回帰直線")
    ax.legend()

# ラベル
for i, row in result_df.iterrows():
    ax.annotate(row["月"], (row["加重平均キャッシュ生産性（TP/LT）"], row["現金増減額（万円）"]))

ax.set_xlabel("加重平均キャッシュ生産性（TP/LT）")
ax.set_ylabel("現金増減額（万円）")
ax.set_title("月別：出荷量加味キャッシュ生産性と現金変動の関係")
ax.grid(True)
st.pyplot(fig)
