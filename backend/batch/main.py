#!/usr/bin/env python3
"""
Pandas ニュース収集バッチ実行スクリプト (拡張版)

1. 各種コレクターモジュールを呼び出し、記事データを並列で取得
   - Google Search API (search_panda_images.py)
   - NewsAPI (article_collector.py)
   - RSS (rss_collector.py)
   - 個別スクレイピング (scrape_collector.py)
2. DB管理モジュール (database_manager) を呼び出し、取得したデータを保存
3. 古いデータをクリーンアップ
"""

import os
import sys
from dotenv import load_dotenv
from typing import List

# --- DB管理モジュール ---
from database_manager import init_supabase_client, save_articles_to_db, delete_old_articles

# --- 共通ヘルパー (単発検証用) ---
from utils import get_main_image

# --- 各種コレクターモジュール ---
from search_panda_images import fetch_from_google_search
from article_collector import fetch_from_newsapi
from rss_collector import fetch_from_rss
from scrape_collector import fetch_from_scraping

def main():
    # 1. 環境変数の読み込みとDBクライアントの初期化
    load_dotenv()
    supabase_client = init_supabase_client()

    # 2. 必要なAPIキーを環境変数から取得
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    CUSTOM_SEARCH_CX = os.environ.get("CUSTOM_SEARCH_CX")
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

    # 3. コマンドライン引数がある場合は単発検証モード
    #    (utils.py の get_main_image を使うように修正)
    args = sys.argv[1:]
    if args:
        for u in args:
            print(f"=== 単発検証: {u}")
            img = get_main_image(u) 
            if img:
                print(f"FOUND image: {img}")
            else:
                print("NO image found.")
        return

    # 4. メインのバッチ処理
    print("データ収集バッチ開始 (マルチソース・モード)")
    
    all_collected_articles: List[dict] = []

    # --- 4-1. Google Search API から収集 ---
    if GOOGLE_API_KEY and CUSTOM_SEARCH_CX:
        try:
            google_articles = fetch_from_google_search(GOOGLE_API_KEY, CUSTOM_SEARCH_CX)
            all_collected_articles.extend(google_articles)
            print(f"[収集完了] Google Search API: {len(google_articles)} 件")
        except Exception as e:
            print(f"[収集エラー] Google Search API: {e}")
    else:
        print("[収集スキップ] Google APIキーが設定されていません。")

    # --- 4-2. NewsAPI から収集 ---
    if NEWS_API_KEY:
        try:
            newsapi_articles = fetch_from_newsapi(NEWS_API_KEY)
            all_collected_articles.extend(newsapi_articles)
            print(f"[収集完了] NewsAPI: {len(newsapi_articles)} 件")
        except Exception as e:
            print(f"[収集エラー] NewsAPI: {e}")
    else:
        print("[収集スキップ] NewsAPIキーが設定されていません。")

    # --- 4-3. RSSフィード から収集 ---
    try:
        rss_articles = fetch_from_rss()
        all_collected_articles.extend(rss_articles)
        print(f"[収集完了] RSSフィード: {len(rss_articles)} 件")
    except Exception as e:
        print(f"[収集エラー] RSSフィード: {e}")

    # --- 4-4. 個別スクレイピング ---
    # (注: 現在はサンプル。必要に応じて有効化・拡張してください)
    # try:
    #     scraped_articles = fetch_from_scraping()
    #     all_collected_articles.extend(scraped_articles)
    #     print(f"[収集完了] 個別スクレイピング: {len(scraped_articles)} 件")
    # except Exception as e:
    #     print(f"[収集エラー] 個別スクレイピング: {e}")


    print(f"\n--- 全ソースから合計 {len(all_collected_articles)} 件の記事候補を取得しました ---")
    
    # 5. データの保存 (変更なし)
    print("--- データベースへの保存処理を開始します ---")
    total_saved = save_articles_to_db(supabase_client, all_collected_articles)

    # 6. 古いデータの削除 (変更なし)
    print("--- 古い記事のクリーンアップ処理を開始します ---")
    total_deleted = delete_old_articles(supabase_client)

    print(f"\nデータ収集バッチ完了 (新規保存: {total_saved} 件, 削除: {total_deleted} 件)")


if __name__ == "__main__":
    main()