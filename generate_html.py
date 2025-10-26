import pandas as pd
from datetime import timedelta

# CSV読み込み
df = pd.read_csv("boku_ao_latest.csv", encoding="utf-8-sig")
df["取得日"] = pd.to_datetime(df["取得日"])

# 最新日と前日を取得
latest_date = df["取得日"].max()
prev_date = latest_date - timedelta(days=1)

# 最新日と前日のデータを抽出
latest_df = df[df["取得日"] == latest_date].copy()
prev_df = df[df["取得日"] == prev_date].copy()

# タイトルでマージ
merged = pd.merge(
    latest_df,
    prev_df[["タイトル", "再生数", "高評価", "コメント数"]],
    on="タイトル",
    how="left",
    suffixes=("", "_前日")
)

# 差分計算（NaNは "—" に置換）
for col in ["再生数", "高評価", "コメント数"]:
    diff_col = f"{col}差分"
    merged[diff_col] = merged.apply(
        lambda row: "—" if pd.isna(row[f"{col}_前日"]) else row[col] - row[f"{col}_前日"],
        axis=1
    )

# 表示列の並び替え
display_df = merged[[
    "タイトル", "投稿日", "再生数", "再生数差分",
    "高評価", "高評価差分",
    "コメント数", "コメント数差分",
]]

# 日付を文字列に変換
latest_str = latest_date.strftime('%Y-%m-%d')
prev_str = prev_date.strftime('%Y-%m-%d')

# HTML生成
html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>僕青 前日差一覧</title>
    <style>
        body { font-family: sans-serif; padding: 2em; background: #f9f9f9; }
        h1 { text-align: center; }
        table {
    border-collapse: collapse;
    background: white;
    width: max-content;     /* ← 内容に合わせて横幅を決定 */
    min-width: 700px;       /* ← 最小幅を保証（任意） */
}
    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; font-size: 14px; white-space: nowrap;}
        th { background-color: #f0f0f0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>僕が見たかった青空 - 前日差一覧</h1>
    <p style="text-align:center;">最新日: """ + latest_str + " ／ 前日: " + prev_str + """</p>

    <div style="overflow-x:auto; max-width:100vw;">   
    <table>
        <thead>
            <tr>
                <th>番号</th>
""" + "".join([f"<th>{col}</th>" for col in display_df.columns]) + "</tr></thead><tbody>\n"

for i, row in enumerate(display_df.itertuples(index=False), start=1):
    html += f"<tr><td>{i}</td>" + "".join([f"<td>{getattr(row, col)}</td>" for col in display_df.columns]) + "</tr>\n"

html += """
        </tbody>
    </table>
    </div>
</body>
</html>
"""

# 保存
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ index.html を出力しました（前日差付き）。")
