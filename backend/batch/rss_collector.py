#!/usr/bin/env python3
"""
記事データ収集モジュール (RSS)
- 指定されたRSSフィードを巡回
- 記事の画像は utils.py で補完
"""

import feedparser
from typing import List
from urllib.parse import urlparse
# 共通ヘルパーをインポート
from .utils import get_main_image, parse_published


# --- ★ 収集対象のRSSフィードリスト ---
# (例: 動物園、動物ニュースサイトなど)
RSS_FEEDS = [
    "https://www.tokyo-zoo.net/rss/news.xml",      # 東京ズーネット (上野動物園など)
    "https://www.kobe-oukoku.com/feed/",           # 神戸どうぶつ王国
    "https://www.aws-s.com/feed",                 # アドベンチャーワールド (ブログ)
    "https://news.yahoo.co.jp/rss/topics/env.xml" # Yahoo!ニュース (環境・科学) - パンダ以外も多く混ざる
]

def fetch_from_rss() -> List[dict]:
    """
    RSSフィードリストを巡回し、記事辞書のリストを返す。
    """
    
    print(f"--- RSSフィード巡回開始 ({len(RSS_FEEDS)} 件) ---")
    all_articles = []
    
    for url in RSS_FEEDS:
        print(f"[RSS] {url} を巡回中...")
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.get("title", urlparse(url).netloc)
            
            for entry in feed.entries:
                article_url = entry.get("link")
                title = entry.get("title")
                
                # 必須項目チェック
                if not article_url or not title:
                    continue
                
                # ★ パンダ関連のキーワードが含まれる記事のみを対象
                keywords = ["panda", "パンダ", "香香", "シャンシャン", "リーリー", "シンシン", "旦旦", "タンタン"]
                if not any(kw in title.lower() for kw in keywords):
                    # print(f"  [RSS スキップ] キーワードなし: {title}")
                    continue

                # 公開日時を取得 (utils.py の共通パーサーを使用)
                dt_struct = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = parse_published(dt_struct).isoformat()
                
                # ★ 共通ヘルパーで画像を取得
                print(f"  [RSS] 記事発見: {title}")
                print(f"    画像を取得中 (スクレイピング)...")
                image_url = get_main_image(article_url)

                all_articles.append({
                    "title": title,
                    "article_url": article_url,
                    "image_url": image_url,
                    "source_name": source_title,
                    "published_at": published_at
                })

        except Exception as e:
            print(f" [RSS エラー] {url} の処理中に失敗: {e}")
            
    return all_articles