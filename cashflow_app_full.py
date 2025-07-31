
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="キャッシュフロー倒産予測", layout="wide")
st.title("🏭 月別キャッシュフロー生産性・倒産予測・感度分析")

st.markdown("""
このアプリでは以下を実行します：

1. アップロードしたCSVから **加重平均 TP/LT** を月ごとに算出  
2. **現金の増減**をもとに将来の現金残高を予測  
3. **資金ショート（倒産）時期の予測**  
4. TP/LT感度分析シミュレーション  
""")

uploaded_file = st.file_uploader("📥 CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ ファイルを読み込みました")
    st.dataframe(df)

    df['現金残高（期末）'] = pd.to_numeric(df['現金残高（期末）'], errors='coerce')
    df['スループット（TP）'] = pd.to_numeric(df['スループット（TP）'], errors='coerce')
    df['リードタイム（LT）'] = pd.to_numeric(df['リードタイム（LT）'], errors='coerce')
    df['出荷数'] = pd.to_numeric(df['出荷数'], errors='coerce')

    results = []
    months = sorted(df['月（YYYY-MM）'].unique())
    prev_cash = None

    for month in months:
        sub_df = df[df['月（YYYY-MM）'] == month]
        sub_df['TP/LT'] = sub_df['スループット（TP）'] / sub_df['リードタイム（LT）']
        sub_df['weighted'] = sub_df['TP/LT'] * sub_df['出荷数']
        total_shipped = sub_df['出荷数'].sum()
        weighted_avg = sub_df['weighted'].sum() / total_shipped if total_shipped else 0
        cash = sub_df['現金残高（期末）'].dropna().values
        cash = cash[0] if len(cash) > 0 else None
        cash_diff = cash - prev_cash if prev_cash is not None and cash is not None else None
        prev_cash = cash if cash is not None else prev_cash
        results.append({
            "月": month,
            "加重平均TP/LT": round(weighted_avg, 2),
            "期末現金残高": cash,
            "現金増減": cash_diff
        })

    result_df = pd.DataFrame(results)
    st.subheader("📈 月別指標")
    st.dataframe(result_df)

    # グラフ1：散布図（加重平均TP/LT vs 現金増減）
    st.subheader("📉 散布図：加重平均キャッシュ生産性 vs 現金増減額")
    chart_df = result_df.dropna()
    fig, ax = plt.subplots()
    ax.scatter(chart_df["加重平均TP/LT"], chart_df["現金増減"])
    ax.set_xlabel("加重平均TP/LT")
    ax.set_ylabel("現金増減額")
    st.pyplot(fig)

    # 倒産時期予測
    st.subheader("⚠️ 倒産（資金ショート）時期の予測")
    current_cash = result_df.iloc[-1]["期末現金残高"]
    avg_diff = result_df["現金増減"].dropna().mean()
    if avg_diff < 0:
        months_until_shortage = int(current_cash / abs(avg_diff))
        st.warning(f"❌ 資金ショートまで約 {months_until_shortage} ヶ月です（平均減少額: {int(avg_diff)}円/月）")
    else:
        st.success("✅ 資金ショートの懸念は今のところありません。")

    # 感度分析
    st.subheader("📊 感度分析：TP/LTの改善による現金への影響")
    rate_change = st.slider("TP/LT改善率（-100%〜+100%）", -1.0, 1.0, 0.0, 0.1)
    sim_df = chart_df.copy()
    sim_df["仮想TP/LT"] = sim_df["加重平均TP/LT"] * (1 + rate_change)

    slope, intercept = np.polyfit(sim_df["加重平均TP/LT"], sim_df["現金増減"], 1)
    sim_df["仮想現金増減"] = sim_df["仮想TP/LT"] * slope + intercept

    fig2, ax2 = plt.subplots()
    ax2.scatter(sim_df["仮想TP/LT"], sim_df["仮想現金増減"], color="green", label="仮想現金増減")
    ax2.set_xlabel("仮想TP/LT")
    ax2.set_ylabel("仮想現金増減額")
    ax2.axhline(0, color="gray", linestyle="--")
    ax2.legend()
    st.pyplot(fig2)

else:
    st.info("💡 CSVファイルをアップロードしてください。")
