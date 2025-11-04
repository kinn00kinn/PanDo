#!/usr/bin/env python3
"""
データベース管理モジュール (Supabase)
- Supabaseクライアントの初期化
- 記事データのリストを受け取り、重複を無視してDBに保存 (Upsert)
- 24時間以上経過した古い記事をDBから削除
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime, timedelta, timezone  # ### 追加 ###

def init_supabase_client() -> Optional[Client]:
    """
    環境変数を読み込み、Supabaseクライアントを初期化して返す
    """
    load_dotenv()
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        print("Supabaseクライアントを初期化しました。")
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("Supabase未設定: ローカル検証モード（DB保存はスキップ）")
        return None

def save_articles_to_db(supabase_client: Optional[Client], articles: List[dict]) -> int:
    """
    記事データのリストを受け取り、DBに Upsert (挿入 or 無視) する。
    """
    if not supabase_client:
        print("DBクライアント未設定のため、保存処理をスキップします。")
        return 0
    
    if not articles:
        print("保存対象の記事がありません。")
        return 0

    # ### 修正 ###
    # 以前の「1件ずつSELECT」ロジックを削除。
    # 代わりに、重複(article_url)したら無視(ignore_duplicates=True)する
    # `upsert` を使います。
    # これが 23505 (重複キー) エラーの最も効率的で正しい解決策です。

    print(f"--- {len(articles)} 件の記事候補をDBに一括 Upsert (挿入/無視) します ---")
    total_inserted = 0
    try:
        # `returning='representation'` を指定すると、
        # *新規挿入されたレコード* のみがリストで返されます。
        response = supabase_client.table("articles").upsert(
            articles,
            on_conflict='article_url',    # 重複をチェックするカラム
            ignore_duplicates=True,     # 重複したら無視 (DO NOTHING)
            returning='representation'  # 新規挿入されたデータだけを返す
        ).execute()
        
        total_inserted = len(response.data)
        
        if total_inserted > 0:
            print(f" [Supabase Upsert 成功] {total_inserted} 件の新規記事を挿入しました。")
        else:
            print(f" [情報] 新規に挿入された記事はありませんでした。")
            
    except Exception as e:
        print(f" [Supabase一括 Upsert エラー]: {e}")
            
    return total_inserted


# ### 追加: 古い記事を削除する関数 ###
def delete_old_articles(supabase_client: Optional[Client]) -> int:
    """
    DB内の古い（24時間以上経過した）記事を削除する
    スキーマの 'created_at' (TIMESTAMPTZ) を基準にします
    """
    if not supabase_client:
        print("DBクライアント未設定のため、削除処理をスキップします。")
        return 0

    print("--- 24時間以上経過した古い記事の削除処理を開始します ---")
    
    try:
        # 24時間前のカットオフ時刻をUTCで計算 (TIMESTAMPTZはUTC基準のため)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        cutoff_iso = cutoff_time.isoformat()
        
        print(f" [情報] 以下の時刻より古い記事 (created_at) を削除します: {cutoff_iso}")

        # 'created_at' が cutoff_time より小さい (lt) ものを削除
        # `returning='representation'` を指定すると、削除されたレコードが返る
        response = supabase_client.table("articles").delete(
            returning='representation'
        ).lt(
            "created_at", cutoff_iso
        ).execute()
        
        deleted_count = len(response.data)
        
        if deleted_count > 0:
            print(f" [Supabase削除成功] {deleted_count} 件の古い記事を削除しました。")
        else:
            print(f" [情報] 削除対象の古い記事はありませんでした。")
            
        return deleted_count

    except Exception as e:
        print(f" [Supabase削除エラー]: {e}")
        return 0