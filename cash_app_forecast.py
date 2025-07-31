
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

# 日本語フォントの自動選択
jp_fonts = ["IPAexGothic", "Noto Sans CJK JP", "IPAGothic", "TakaoGothic"]
available_fonts = set(f.name for f in fm.fontManager.ttflist)
for font in jp_fonts:
    if font in available_fonts:
        plt.rcParams["font.family"] = font
        break

st.title("キャッシュ生産性分析 + 散布図 + 感度分析 + ゼロ月数予測")

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

result_df = pd.DataFrame(results)
st.markdown("### 集計結果")
st.dataframe(result_df, use_container_width=True)

# 感度分析
st.markdown("### 感度分析シミュレーション")
improve_rate = st.slider("TP/LT 改善率（％）", min_value=-100, max_value=100, value=0, step=1)
cash_injection = st.number_input("一括現金注入（万円）", value=0)

adjusted_tp_lt = result_df["加重平均キャッシュ生産性（TP/LT）"] * (1 + improve_rate / 100)
adjusted_y = result_df["現金増減額（万円）"] * (1 + improve_rate / 100) + (cash_injection / months if months > 0 else 0)

# 将来残高の予測グラフ（散布図）
st.markdown("### グラフ：加重平均キャッシュ生産性 vs 現金増減額（散布図）")
fig1, ax1 = plt.subplots()
ax1.scatter(adjusted_tp_lt, adjusted_y)
ax1.set_xlabel("加重平均キャッシュ生産性（TP/LT）")
ax1.set_ylabel("現金増減額（万円）")
ax1.set_title("月別 キャッシュ生産性と現金増減の関係")
ax1.grid(True)
st.pyplot(fig1)

# 将来残高予測
st.markdown("### 将来12ヶ月の現金残高（シミュレーション）")
future_balance = [cash_balances[-1]]
for i in range(12):
    future_balance.append(future_balance[-1] + adjusted_y.mean())

fig2, ax2 = plt.subplots()
ax2.plot(range(13), future_balance, marker="o")
ax2.set_xlabel("月")
ax2.set_ylabel("将来現金残高（万円）")
ax2.set_title("将来12ヶ月の現金残高推移")
ax2.grid(True)
st.pyplot(fig2)

# ゼロ残高月数の予測
zero_month = next((i for i, v in enumerate(future_balance) if v <= 0), None)
if zero_month is not None:
    st.error(f"⚠️ 将来 {zero_month} ヶ月目に現金残高がゼロ以下になる可能性があります。")
else:
    st.success("✅ 将来12ヶ月間で現金残高がゼロになることはありません。")
