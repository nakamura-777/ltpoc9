
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# フォント設定（日本語対応）
import matplotlib.font_manager as fm
jp_fonts = ["IPAexGothic", "Noto Sans CJK JP", "IPAGothic", "TakaoGothic"]
available_fonts = set(f.name for f in fm.fontManager.ttflist)
for font in jp_fonts:
    if font in available_fonts:
        plt.rcParams["font.family"] = font
        break

st.title("キャッシュフロー分析アプリ（完全版）")

st.sidebar.header("分析期間と感度分析")
months = st.sidebar.number_input("分析月数", min_value=1, max_value=24, value=6)
tp_lt_change = st.sidebar.slider("TP/LT変化率（%）", -100, 100, 0) / 100.0

# 月別データ入力
monthly_data = []
for i in range(months):
    st.subheader(f"{i+1}ヶ月目データ")
    cash_start = st.number_input(f"期首現金（{i+1}ヶ月目）", key=f"start_{i}")
    cash_end = st.number_input(f"期末現金（{i+1}ヶ月目）", key=f"end_{i}")
    products = st.number_input(f"製品数（{i+1}ヶ月目）", min_value=1, max_value=10, value=3, key=f"pcount_{i}")

    tp_lt_values = []
    for j in range(products):
        st.markdown(f"📦 製品{j+1}")
        tp = st.number_input(f"スループット（TP）", min_value=0.0, key=f"tp_{i}_{j}")
        lt = st.number_input(f"リードタイム（LT）", min_value=0.1, key=f"lt_{i}_{j}")
        qty = st.number_input(f"出荷数", min_value=0, key=f"qty_{i}_{j}")
        tp_lt = (tp / lt) * (1 + tp_lt_change)
        tp_lt_values.append({"tp": tp, "lt": lt, "qty": qty, "tp_lt": tp_lt})

    # 加重平均TP/LTの算出
    total_tp = sum(p["tp"] * p["qty"] for p in tp_lt_values)
    total_qty = sum(p["qty"] for p in tp_lt_values)
    weighted_tp_lt = sum((p["tp_lt"] * p["qty"]) for p in tp_lt_values) / total_qty if total_qty else 0

    monthly_data.append({
        "期首現金": cash_start,
        "期末現金": cash_end,
        "現金増減": cash_end - cash_start,
        "スループット合計": total_tp,
        "加重平均TP/LT": weighted_tp_lt
    })

df = pd.DataFrame(monthly_data)

# グラフ：加重平均キャッシュ生産性 × 現金増減
st.subheader("加重平均キャッシュ生産性 × 現金増減の関係")
fig, ax = plt.subplots()
x = df["加重平均TP/LT"]
y = df["現金増減"]
ax.scatter(x, y)
ax.set_xlabel("加重平均キャッシュ生産性 (TP/LT)")
ax.set_ylabel("現金増減額")
st.pyplot(fig)

# 将来予測
st.subheader("資金ショート時期の予測")
future_balance = df["期末現金"].tolist()
zero_month = None
for i, val in enumerate(future_balance):
    if val < 0:
        zero_month = i
        break

# メッセージ＆イラスト表示

def show_image_and_message(image_file, message, color="info"):
    image_path = os.path.join("images", image_file)
    if os.path.exists(image_path):
        st.image(image_path, width=120)
    getattr(st, color)(message)


if zero_month is not None:
    if zero_month == 0:
        show_image_and_message("danger.png", "💥 今月中に資金ショートの恐れがあります。即時対応を！", "error")
    elif zero_month == 1:
        show_image_and_message("warning.png", "⚠️ 1ヶ月以内に資金ショートの可能性があります。", "warning")
    elif 2 <= zero_month <= 3:
        show_image_and_message("alarm.png", f"🚨 {zero_month}ヶ月以内に現金枯渇が予測されます。", "warning")
    elif 4 <= zero_month <= 11:
        show_image_and_message("info.png", f"ℹ️ {zero_month}ヶ月後にショートが予測されます。", "info")
else:
    show_image_and_message("safe.png", "✅ 今後12ヶ月以内に資金ショートの心配はありません。", "success")

# ダウンロード用データ
st.subheader("データ出力")
st.dataframe(df)
st.download_button("📥 CSVとしてダウンロード", df.to_csv(index=False), file_name="cash_flow_analysis.csv")



def estimate_shortage_month(results):
    balances = []
    current_cash = None
    for res in results:
        cash_end = res["現金増減"]
        balances.append(cash_end)

    total_cash = 0
    shortage_month = None
    for i, res in enumerate(results):
        total_cash += res["現金増減"]
        if total_cash < 0:
            shortage_month = res["月"]
            break
    return shortage_month



# 各月のデータを処理
metrics = calculate_metrics(monthly_data)

# アプリ内でショート時期をチェックしてアラートを表示
shortage_month = estimate_shortage_month(metrics)
if shortage_month:
    st.error(f"⚠️ 資金ショート（倒産リスク）は {shortage_month} に予測されます。至急の対応が必要です。")
else:
    st.success("✅ 現在の収支ペースでは、資金ショートの心配はありません。")
