
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 日本語フォント設定
import matplotlib.font_manager as fm
jp_fonts = ["IPAexGothic", "Noto Sans CJK JP", "IPAGothic", "TakaoGothic"]
available_fonts = set(f.name for f in fm.fontManager.ttflist)
for font in jp_fonts:
    if font in available_fonts:
        plt.rcParams["font.family"] = font
        break

st.title("キャッシュフロー感度分析＆資金ショート警告")

st.sidebar.header("入力")
months = st.sidebar.number_input("期間（月）", min_value=1, max_value=24, value=6)

# 月別データ入力
data = []
for i in range(months):
    st.subheader(f"{i+1}ヶ月目の入力")
    col1, col2, col3 = st.columns(3)
    with col1:
        cash_start = st.number_input(f"{i+1}ヶ月目: 期首現金", key=f"start_{i}")
    with col2:
        cash_end = st.number_input(f"{i+1}ヶ月目: 期末現金", key=f"end_{i}")
    with col3:
        weighted_tp_lt = st.number_input(f"{i+1}ヶ月目: 加重平均TP/LT", key=f"tp_lt_{i}", min_value=0.0)

    data.append({
        "期首現金": cash_start,
        "期末現金": cash_end,
        "加重平均TP/LT": weighted_tp_lt,
        "現金増減": cash_end - cash_start
    })

df = pd.DataFrame(data)

# グラフ表示
st.subheader("グラフ：加重平均TP/LT × 現金増減")
fig, ax = plt.subplots()
x = df["加重平均TP/LT"]
y = df["現金増減"]
ax.scatter(x, y)

ax.set_xlabel("加重平均キャッシュ生産性 (TP/LT)")
ax.set_ylabel("現金増減額")
st.pyplot(fig)

# 資金ショート予測
st.subheader("資金ショートの予測")

future_balance = df["期末現金"].tolist()
zero_month = None
for i, val in enumerate(future_balance):
    if val < 0:
        zero_month = i
        break

# 画像パス関数
def show_image_and_message(image_file, message, color="info"):
    st.image(f"images/{image_file}", width=120)
    getattr(st, color)(message)

# 警告表示
if zero_month is not None:
    if zero_month == 0:
        show_image_and_message("danger.png", "💥 今月中に資金がショートします。即時対応が必要です。", "error")
    elif zero_month == 1:
        show_image_and_message("warning.png", "⚠️ 1ヶ月以内に資金ショートの可能性あり。今すぐ対策を。", "error")
    elif 2 <= zero_month <= 3:
        show_image_and_message("alarm.png", f"🚨 {zero_month}ヶ月以内に現金が枯渇予測。TP/LT見直しを。", "warning")
    elif 4 <= zero_month <= 11:
        show_image_and_message("info.png", f"ℹ️ {zero_month}ヶ月後にショートの予測。今のうちに改善を。", "info")
else:
    show_image_and_message("safe.png", "✅ 今後12ヶ月以内に資金ショートの心配はありません。", "success")
