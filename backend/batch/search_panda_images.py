#!/usr/bin/env python3
"""
Google Custom Search API を使用したパンダ画像収集モジュール
(ヘルパー関数を utils.py に移動)
"""

import os
import sys
from datetime import datetime
from typing import Optional, List
import requests

# 共通ヘルパーをインポート
from utils import get_main_image, validate_image_url, SESSION

def fetch_from_google_search(api_key: str, cx_id: str) -> List[dict]:
    """
    Google Custom Search API (Image) を使って
    過去24時間 ('d1') のパンダの画像と元記事を取得する
    (関数名を変更)
    """
    
    API_URL = "https://www.googleapis.com/customsearch/v1"
    query = 'panda OR "giant panda" OR パンダ OR ジャイアントパンダ'
    
    TOTAL_PAGES_TO_TRY = 10
    ITEMS_PER_PAGE = 10
    
    params = {
        "key": api_key,
        "cx": cx_id,
        "q": query,
        "searchType": "image",
        "dateRestrict": "d1",
        "num": ITEMS_PER_PAGE,
    }
    
    print(f"--- Google Custom Search API 実行中 (最大100件取得, q={query}) ---")

    all_data_items = [] 
    
    for i in range(TOTAL_PAGES_TO_TRY):
        params['start'] = (i * ITEMS_PER_PAGE) + 1
        
        try:
            response = SESSION.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            items_on_this_page = data.get("items")
            
            if not items_on_this_page:
                print(" [情報] これ以上取得するアイテムがありません。ループを終了します。")
                break
            
            all_data_items.extend(items_on_this_page)

        except requests.RequestException as e:
            print(f" [APIリクエストエラー]: {e}")
            if response is not None and hasattr(response, 'text'):
                print(f" [エラー詳細]: {response.text}")
            return [] 

    results = []
    items = all_data_items
    
    if not items:
        print(" [情報] 該当する画像は見つかりませんでした。")
        return []

    print(f"\n--- APIから取得した合計 {len(items)} 件の記事候補を検証します ---")

    for item in items:
        title = item.get("title", "(タイトルなし)")
        google_image_url = item.get("link")
        source_article_url = item.get("image", {}).get("contextLink")
        source_name = item.get("displayLink")

        if not source_article_url:
            print(f" [スキップ] 元記事のURLがありません: {title}")
            continue

        print(f"\n* 検証中: {title}")
        print(f"   元記事 (参考文献): {source_article_url}")

        final_image_url = None

        # ★ 共通ヘルパーを使用
        if validate_image_url(google_image_url):
            print(f"   [OK] Google提供の画像を採用: {google_image_url}")
            final_image_url = google_image_url
        else:
            print(f"   [NG] Google提供の画像が無効。元記事をスクレイピングします...")
            # ★ 共通ヘルパーを使用
            scraped_image_url = get_main_image(source_article_url)
            
            if scraped_image_url:
                print(f"   [OK] スクレイピングで画像を発見: {scraped_image_url}")
                final_image_url = scraped_image_url
            else:
                print(f"   [FAIL] スクレイピングでも画像を発見できませんでした。")

        if final_image_url:
            results.append({
                "title": title,
                "article_url": source_article_url,
                "image_url": final_image_url,
                "source_name": source_name,
                # Google Search APIは公開日を返さないため、現在時刻をセット
                "published_at": datetime.now().isoformat() 
            })

    return results


# --- 単体実行 (テスト) ---
if __name__ == "__main__":
    print("--- モジュール単体テスト実行 (Google Search) ---")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    CUSTOM_SEARCH_CX = os.environ.get("CUSTOM_SEARCH_CX")

    if not GOOGLE_API_KEY or not CUSTOM_SEARCH_CX:
        print("【エラー】 GOOGLE_API_KEY または CUSTOM_SEARCH_CX が .env に設定されていません。")
        sys.exit(1)

    panda_images = fetch_from_google_search(GOOGLE_API_KEY, CUSTOM_SEARCH_CX)
    
    print(f"\n{'='*20} 最終結果: {len(panda_images)} 件 {'='*20}")
    for item in panda_images:
        print(f"  {item['title']} -> {item['image_url']}")