import os
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 環境変数からAPIキーを読み込む
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UC-_iQWdEZY66nGGaHH0Ygmg"

# YouTube APIクライアントの初期化
youtube = build("youtube", "v3", developerKey=API_KEY)

# アップロード動画プレイリストIDを取得
channel_response = youtube.channels().list(
    part="contentDetails",
    id=CHANNEL_ID
).execute()

uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# プレイリストから最新20件の動画IDを取得
playlist_response = youtube.playlistItems().list(
    part="contentDetails",
    playlistId=uploads_playlist_id,
    maxResults=20  # ← ここを10から20に変更
).execute()

video_ids = [item["contentDetails"]["videoId"] for item in playlist_response["items"]]

# 各動画の詳細情報を取得
video_response = youtube.videos().list(
    part="snippet,statistics",
    id=",".join(video_ids)
).execute()

# 今日の日付（取得日）を追加
today_str = datetime.now().strftime("%Y-%m-%d")

video_data = []

# 動画ごとの処理
for item in video_response["items"]:
    title = item["snippet"]["title"]
    published_at = item["snippet"]["publishedAt"][:10]  # YYYY-MM-DD形式

    # 今日公開された動画は除外（反映遅延対策）
    if published_at == today_str:
        continue

    view_count = int(item["statistics"].get("viewCount", 0))
    like_count = int(item["statistics"].get("likeCount", 0))
    comment_count = int(item["statistics"].get("commentCount", 0))
    video_data.append({
        "タイトル": title,
        "投稿日": published_at,
        "再生数": view_count,
        "高評価": like_count,
        "コメント数": comment_count,
        "取得日": today_str
    })

# DataFrame化
df = pd.DataFrame(video_data)

# 保存ファイル名（固定）
csv_path = "boku_ao_latest.csv"

# 既存ファイルがあれば読み込み、結合
if os.path.exists(csv_path):
    old_df = pd.read_csv(csv_path, encoding="utf-8-sig")
    
    # 取得日をdatetimeに変換
    old_df["取得日"] = pd.to_datetime(old_df["取得日"])
    df["取得日"] = pd.to_datetime(df["取得日"])
    
    # 重複（タイトル＋取得日）を除外してから結合
    old_df = old_df[~old_df.set_index(["タイトル", "取得日"]).index.isin(
        df.set_index(["タイトル", "取得日"]).index
    )]
    
    combined_df = pd.concat([old_df, df], ignore_index=True)
else:
    df["取得日"] = pd.to_datetime(df["取得日"])
    combined_df = df

# 取得日が6日以上前の行を削除
combined_df["取得日"] = pd.to_datetime(combined_df["取得日"])
cutoff_date = datetime.now() - timedelta(days=5)
filtered_df = combined_df[combined_df["取得日"] >= cutoff_date]

# CSVに上書き保存（最新5日分のみ）
filtered_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("✅ boku_ao_latest.csv を更新しました（最新20件＋高評価・コメント数付き）。")
