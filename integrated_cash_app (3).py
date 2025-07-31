
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# --- 共通設定 ---
st.set_page_config(layout="wide")
st.title("キャッシュ生産性 × 現金増減 × 資金ショート予測アプリ")
mode = st.radio("モード選択", ["CSVファイルから分析", "月別手入力で分析"])

# --- モード1: CSVファイルアップロードによる分析 ---
if mode == "CSVファイルから分析":
    with st.sidebar:
        st.header("操作パネル")
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding="shift-jis")

            df["生産開始日"] = pd.to_datetime(df["生産開始日"], errors="coerce")
            df["出荷日"] = pd.to_datetime(df["出荷日"], errors="coerce")
            df["リードタイム"] = (df["出荷日"] - df["生産開始日"]).dt.days.clip(lower=1)

            df["スループット"] = df["売上単価"] - df["材料費"] - df["外注費"]
            df["TP/LT"] = df["スループット"] / df["リードタイム"]

            st.subheader("アップロードデータ")
            st.dataframe(df)

            st.subheader("製品別統計情報")
            stats_df = df.groupby("品名")[["スループット", "TP/LT"]].agg(["mean", "max", "min", "std"])
            st.dataframe(stats_df)

            st.subheader("キャッシュ生産性バブルチャート")
            fig = px.scatter(df, x="TP/LT", y="スループット", color="品名", size="出荷数",
                            hover_data=["品名", "スループット", "TP/LT", "リードタイム"])
            st.plotly_chart(fig, use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("結果をCSVでダウンロード", csv, "result.csv", "text/csv")

# --- モード2: 月別手入力による分析 ---
else:
    months = st.multiselect("分析対象の月（例: 2024-01）を選択", options=[
        "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08"
    ], default=["2024-01", "2024-02", "2024-03"])
    
    monthly_data = {}
    for month in months:
        st.markdown(f"### 📦 {month}")
        with st.expander(f"{month} の製品データ入力"):
            df = st.data_editor(
                pd.DataFrame([{"製品名": "", "TP（万円）": 0.0, "LT（日）": 1}], columns=["製品名", "TP（万円）", "LT（日）"]),
                key=month,
                num_rows="dynamic"
            )
            cash_start = st.number_input(f"{month}の期首現金残高（万円）", key=f"{month}_start", value=0.0)
            cash_end = st.number_input(f"{month}の期末現金残高（万円）", key=f"{month}_end", value=0.0)
            monthly_data[month] = {"df": df, "start": cash_start, "end": cash_end}

    results = []
    monthly_cash_diff = []

    for month, data in monthly_data.items():
        df = data["df"].dropna()
        df["TP/LT"] = df["TP（万円）"] / df["LT（日）"]
        df["TP²/LT"] = df["TP（万円）"]**2 / df["LT（日）"]
        total_tp = df["TP（万円）"].sum()
        weighted_tp_lt = df["TP²/LT"].sum() / total_tp if total_tp > 0 else 0
        cash_diff = data["end"] - data["start"]
        results.append({
            "月": month,
            "加重平均TP/LT": weighted_tp_lt,
            "現金増減額（万円）": cash_diff
        })
        monthly_cash_diff.append(cash_diff)

    if results:
        result_df = pd.DataFrame(results)
        st.markdown("## グラフ：加重平均キャッシュ生産性 vs 現金増減額")
        fig, ax = plt.subplots()
        ax.scatter(result_df["加重平均TP/LT"], result_df["現金増減額（万円）"], color='blue')
        for i, row in result_df.iterrows():
            ax.annotate(row["月"], (row["加重平均TP/LT"], row["現金増減額（万円）"]),
                        textcoords="offset points", xytext=(5, 5), ha='left')
        ax.set_xlabel("加重平均キャッシュ生産性")
        ax.set_ylabel("現金増減額")
        ax.set_title("月別：加重平均キャッシュ生産性と現金増減額の関係")
        ax.grid(True)
        st.pyplot(fig)

        st.markdown("## 資金ショート時期予測")
        try:
            total_months = len(results)
            total_cash_diff = sum(monthly_cash_diff)
            avg_monthly_cash_diff = total_cash_diff / total_months if total_months > 0 else 0
            latest_cash = list(monthly_data.values())[-1]["end"]

            if avg_monthly_cash_diff < 0:
                months_until_short = latest_cash / abs(avg_monthly_cash_diff)
                future_months = [i+1 for i in range(12)]
                future_cash = [latest_cash + avg_monthly_cash_diff * m for m in future_months]

                st.write(f"📉 現在の期末現金残高: {latest_cash:.1f}万円")
                st.write(f"📉 平均月間現金減少: {avg_monthly_cash_diff:.1f}万円")
                st.write(f"🚨 資金ショート予測: 約 {months_until_short:.1f} ヶ月後")

                fig2, ax2 = plt.subplots()
                ax2.plot(future_months, future_cash, marker='o', linestyle='-')
                ax2.axhline(0, color='red', linestyle='--')
                ax2.set_title("将来の現金残高予測")
                ax2.set_xlabel("現在からの月数")
                ax2.set_ylabel("予測現金残高（万円）")
                ax2.grid(True)
                st.pyplot(fig2)
            else:
                st.success("現在は資金ショートの兆候は見られません。")
        except Exception as e:
            st.error("資金ショート予測でエラーが発生しました。")

        st.markdown("## 結果表")
        st.dataframe(result_df)
        csv = result_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSVをダウンロード", csv, "cash_summary.csv", "text/csv")

        st.markdown("## 感度分析：TP/LT改善シナリオによる収支改善効果")
        if total_months > 0 and avg_monthly_cash_diff < 0:
            scenarios = {
                "現状維持 (0%)": 0.00,
                "軽度改善 (+10%)": 0.10,
                "中度改善 (+20%)": 0.20,
                "高度改善 (+30%)": 0.30,
            }

            base_tp_lt = result_df["加重平均TP/LT"].mean()
            fig3, ax3 = plt.subplots()
            future_months = list(range(1, 13))

            for label, improve_rate in scenarios.items():
                improved_tp_lt = base_tp_lt * (1 + improve_rate)
                adjusted_cash_diff = avg_monthly_cash_diff * (1 + improve_rate)
                future_cash = [latest_cash + adjusted_cash_diff * m for m in future_months]
                ax3.plot(future_months, future_cash, marker='o', label=label)

            ax3.axhline(0, color='black', linestyle='--')
            ax3.set_title("TP/LT改善シナリオ別：将来の現金残高予測")
            ax3.set_xlabel("現在からの月数")
            ax3.set_ylabel("予測現金残高（万円）")
            ax3.legend()
            ax3.grid(True)
            st.pyplot(fig3)
