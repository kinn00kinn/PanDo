#!/usr/bin/env python3
"""
共通ヘルパーモジュール
- HTTPリクエスト
- 画像URLの検証
- 記事ページからの画像抽出 (OGP, JSON-LD, etc.)
- 日付のパース
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional, List
from time import mktime

# --- 定数 ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
HTTP_TIMEOUT = 10
MIN_IMAGE_BYTES = 512
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"})

# --- 共通ヘルパー関数 ---

def parse_published(pubval) -> datetime:
    """
    様々な形式の日付文字列や数値をdatetimeオブジェクトに変換する
    (article_collector.py, rss_collector.py から使用)
    """
    if not pubval:
        return datetime.now()
    if isinstance(pubval, (int, float)):
        try:
            return datetime.fromtimestamp(int(pubval))
        except Exception:
            return datetime.now()
    if isinstance(pubval, str):
        try:
            # ISO形式 (Zを+00:00に置換)
            return datetime.fromisoformat(pubval.replace("Z", "+00:00"))
        except Exception:
            pass
        try:
            # RFC 2822 形式 (email.utils)
            return parsedate_to_datetime(pubval)
        except Exception:
            pass
    if isinstance(pubval, (tuple, list)):
        try:
            # time.struct_time (feedparser用)
            return datetime.fromtimestamp(mktime(tuple(pubval)))
        except Exception:
            pass
            
    return datetime.now()


def fetch_html(url: str, timeout: int = HTTP_TIMEOUT) -> Optional[tuple]:
    """[内部] HTMLを取得して BeautifulSoup オブジェクトを返す"""
    try:
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        # 最終的なURLとBeautifulSoupオブジェクトを返す
        return resp.url, BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f" [fetch_html エラー] {url} : {e}")
        return None


def validate_image_url(img_url: str, timeout: int = 6) -> bool:
    """[内部] 提供された画像URLが有効か検証する"""
    try:
        if not img_url or not img_url.startswith("http"):
            return False
        
        # HEADリクエストで Content-Type と Content-Length を確認
        try:
            head = SESSION.head(img_url, timeout=timeout, allow_redirects=True)
            if head.status_code >= 400: return False
            ct = head.headers.get("Content-Type", "")
            if not ct.startswith("image/"): return False
            cl = head.headers.get("Content-Length")
            if cl and int(cl) < MIN_IMAGE_BYTES: return False
            return True
        
        # HEADが失敗した場合 (サーバーがHEADをサポートしていない場合)
        except Exception:
            g = SESSION.get(img_url, timeout=timeout, stream=True)
            if g.status_code >= 400: return False
            ct = g.headers.get("Content-Type", "") or ""
            if not ct.startswith("image/"): return False
            first_chunk = next(g.iter_content(1024), b"")
            g.close()
            return len(first_chunk) >= 16
            
    except Exception as e:
        print(f"   [validate_image 例外] {img_url} : {e}")
        return False

def get_main_image(article_url: str) -> Optional[str]:
    """
    記事URLをスクレイピングしてOGPや本文からメイン画像を取得する
    (すべてのコレクターモジュールから呼び出される)
    """
    fetched = fetch_html(article_url)
    if not fetched:
        return None
    final_url, soup = fetched

    # 1) OGP / Twitter
    meta_keys = [
        ("meta", {"property": "og:image"}, "content"),
        ("meta", {"property": "og:image:secure_url"}, "content"),
        ("meta", {"name": "twitter:image"}, "content"),
    ]
    for tag, attrs, attrname in meta_keys:
        t = soup.find(tag, attrs=attrs)
        if t and t.get(attrname):
            cand = requests.compat.urljoin(final_url, t.get(attrname))
            if validate_image_url(cand):
                return cand

    # 2) JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            txt = script.string
            if not txt: continue
            data = json.loads(txt)
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict):
                    img = it.get("image") or it.get("thumbnailUrl")
                    if isinstance(img, str):
                        cand = requests.compat.urljoin(final_url, img)
                        if validate_image_url(cand): return cand
                    elif isinstance(img, dict):
                        urlf = img.get("url")
                        if urlf:
                            cand = requests.compat.urljoin(final_url, urlf)
                            if validate_image_url(cand): return cand
                    elif isinstance(img, list):
                        for it2 in img:
                            if isinstance(it2, str):
                                cand = requests.compat.urljoin(final_url, it2)
                                if validate_image_url(cand): return cand
        except Exception:
            continue

    # 3) 本文中画像
    selectors = ["article", "main", "[role='main']", ".post-content", ".article-body", "#content"]
    main_content = None
    for s in selectors:
        main_content = soup.select_one(s)
        if main_content: break
    if not main_content:
        main_content = soup.body

    if main_content:
        for img in main_content.find_all("img", src=True):
            src = img.get("src")
            if not src or src.startswith("data:"): continue
            cand = requests.compat.urljoin(final_url, src)
            if validate_image_url(cand):
                return cand
    return None