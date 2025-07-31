
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "Noto Sans CJK JP"

st.title("キャッシュ生産性分析 + 製品別TP/LT傾向 + 感度分析 + 将来残高グラフ")

months = st.number_input("分析対象月数", min_value=1, max_value=24, value=6)
cash_balances = []
for i in range(months + 1):
    cash = st.number_input(f"{i+1}ヶ月目 期首現金残高（万円）", value=1000 if i == 0 else 0)
    cash_balances.append(cash)

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

# 製品別TP/LT傾向データ準備
all_products = []

results = []
for i in range(months):
    df = monthly_product_data[i]
    df = df[(df["TP（万円）"] > 0) & (df["LT（日）"] > 0) & (df["出荷数"] > 0)]

    df["TP/LT"] = df["TP（万円）"] / df["LT（日）"]
    df["月"] = f"{i+1}ヶ月目"
    all_products.append(df[["月", "製品名", "TP（万円）", "LT（日）", "TP/LT", "出荷数"]])

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

result_df = pd.DataFrame(results)
st.markdown("### 集計結果")
st.dataframe(result_df, use_container_width=True)

# 製品別TP/LT傾向グラフ
st.markdown("### 製品別TP/LT傾向")
if all_products:
    product_df = pd.concat(all_products, ignore_index=True)
    fig, ax = plt.subplots()
    for name, group in product_df.groupby("製品名"):
        ax.plot(group["月"], group["TP/LT"], marker="o", label=name)

    ax.set_title("製品別TP/LT推移")
    ax.set_xlabel("月")
    ax.set_ylabel("TP/LT（万円/日）")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

# 感度分析
st.markdown("### 感度分析シミュレーション")
improve_rate = st.slider("TP/LT 改善率（％アップ）", min_value=0, max_value=100, value=0)
cash_injection = st.number_input("一括現金注入（万円）", value=0)

adjusted_tp_lt = result_df["加重平均キャッシュ生産性（TP/LT）"] * (1 + improve_rate / 100)
adjusted_y = result_df["現金増減額（万円）"] + (cash_injection / months if months > 0 else 0)

# シミュレーション結果
st.markdown("#### シミュレーション結果")
sim_df = pd.DataFrame({
    "月": result_df["月"],
    "改善後キャッシュ生産性": adjusted_tp_lt.round(2),
    "改善後現金増減額（万円）": adjusted_y.round(2)
})
st.dataframe(sim_df, use_container_width=True)

# 将来残高の予測グラフ
st.markdown("### グラフ：将来現金残高（シミュレーション）")
future_balance = [cash_balances[-1]]
for i in range(12):
    future_balance.append(future_balance[-1] + adjusted_y.mean())

fig2, ax2 = plt.subplots()
ax2.plot(range(13), future_balance, marker="o")
ax2.set_xlabel("月")
ax2.set_ylabel("将来現金残高（万円）")
ax2.set_title("将来12ヶ月の現金残高推移（シミュレーション）")
ax2.grid(True)
st.pyplot(fig2)
