#!/usr/bin/env python3
import os
import sys
import json
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Tuple

# --- 環境変数読み込み ---
load_dotenv()

# --- RSSフィード一覧（必要に応じて編集） ---
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=%E3%83%91%E3%83%B3%E3%83%80&hl=ja&gl=JP&ceid=JP:ja",
    "https://www.tokyo-zoo.net/zoo/ueno/news/atom.xml",
    "https://www.aws-s.com/topics/atom.xml",
    "https://www.worldwildlife.org/feeds/blog/posts",
    "https://nationalzoo.si.edu/news/rss.xml"
]

# --- Supabase 設定（オプション: ローカル検証のみの場合は空でOK）---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("SupabaseのURL/KEYが未設定です。DB保存はスキップされます（ローカル検証モード）。")

# --- 設定値 ---
MIN_IMAGE_BYTES = 512  # 画像の最小バイト数（必要に応じ調整）
HTTP_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

# --- ユーティリティ関数 ---


def is_google_cache_url(u: Optional[str]) -> bool:
    if not u:
        return False
    return any(x in u for x in ("lh3.googleusercontent.com", "googleusercontent", "gstatic.com"))


def fetch_html(url: str, timeout: int = HTTP_TIMEOUT) -> Optional[Tuple[str, BeautifulSoup]]:
    """
    URLをGETして (final_url, BeautifulSoup) を返す。失敗時は None を返す。
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        final = resp.url
        soup = BeautifulSoup(resp.text, "html.parser")
        return final, soup
    except requests.RequestException as e:
        print(f"  [fetch_html エラー] {url} : {e}")
        return None


def validate_image_url(img_url: str, timeout: int = 6) -> bool:
    """
    画像URLとして有効かを検証する:
    - HEADで Content-Type が image/* を確認
    - HEADが不十分な場合は small GET を試す
    - minimal byte 長を満たすことを確認
    """
    try:
        parsed = urlparse(img_url)
        if not parsed.scheme:
            return False

        headers = {"User-Agent": USER_AGENT}
        # 1) HEAD
        try:
            head = requests.head(img_url, timeout=timeout, headers=headers, allow_redirects=True)
            if head.status_code >= 400:
                head = None
        except requests.RequestException:
            head = None

        if head:
            ct = head.headers.get("Content-Type", "")
            if ct and ct.startswith("image/"):
                cl = head.headers.get("Content-Length")
                if cl:
                    try:
                        if int(cl) < MIN_IMAGE_BYTES:
                            print(f"    [validate] content-length too small: {img_url} ({cl})")
                            return False
                    except Exception:
                        pass
                return True
            # not image according to HEAD -> fallback to small GET
        # fallback GET (stream)
        try:
            g = requests.get(img_url, timeout=timeout, headers=headers, stream=True)
            if g.status_code >= 400:
                print(f"    [validate] GET failed: {img_url} ({g.status_code})")
                return False
            ct = g.headers.get("Content-Type", "")
            if not (ct and ct.startswith("image/")):
                print(f"    [validate] Content-Type not image: {img_url} ({ct})")
                g.close()
                return False
            # check a bit of content length or read first chunk to ensure it's not empty
            cl = g.headers.get("Content-Length")
            if cl:
                try:
                    if int(cl) < MIN_IMAGE_BYTES:
                        print(f"    [validate] content-length too small (GET): {img_url} ({cl})")
                        g.close()
                        return False
                except Exception:
                    pass
            # If no content-length header, try to read a small chunk
            first_chunk = next(g.iter_content(1024), b"")
            if len(first_chunk) < 16:
                print(f"    [validate] first chunk too small: {img_url}")
                g.close()
                return False
            g.close()
            return True
        except requests.RequestException as e:
            print(f"    [validate] GET exception: {img_url} : {e}")
            return False
    except Exception as e:
        print(f"    [validate] unexpected error: {img_url} : {e}")
        return False


# JSON-LD解析やページ内URL抽出など、元記事解決ロジック


def parse_jsonld_for_url(soup: BeautifulSoup) -> Optional[str]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            txt = script.string
            if not txt:
                continue
            data = json.loads(txt)
            items = data if isinstance(data, list) else [data]
            for it in items:
                url = None
                if isinstance(it, dict):
                    url = it.get("url") or it.get("@id")
                    if url and isinstance(url, str) and url.startswith("http") and "google" not in urlparse(url).netloc:
                        return url
                    me = it.get("mainEntityOfPage")
                    if isinstance(me, dict):
                        url2 = me.get("@id") or me.get("url")
                        if url2 and isinstance(url2, str) and url2.startswith("http") and "google" not in urlparse(url2).netloc:
                            return url2
        except Exception:
            continue
    return None


def find_first_external_href(soup: BeautifulSoup) -> Optional[str]:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            net = urlparse(href).netloc.lower()
            if "google" in net or "accounts.google" in net:
                continue
            return href
    return None


def find_urls_by_regex(text: str) -> Optional[str]:
    urls = re.findall(r"https?://[^\s'\"<>)+]+", text or "")
    for u in urls:
        net = urlparse(u).netloc.lower()
        if "google" in net:
            continue
        return u
    return None


def resolve_google_news_original(final_url: str, soup: BeautifulSoup) -> Optional[str]:
    """
    Google News 中間ページから可能な限り元記事URLを見つける（複数戦略）
    """
    # og:url / canonical
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        cand = og_url["content"]
        if cand.startswith("http") and "google" not in urlparse(cand).netloc:
            print(f"  [解決] og:url -> {cand}")
            return cand

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        cand = canonical["href"]
        if cand.startswith("http") and "google" not in urlparse(cand).netloc:
            print(f"  [解決] canonical -> {cand}")
            return cand

    # JSON-LD
    jsonld = parse_jsonld_for_url(soup)
    if jsonld:
        print(f"  [解決] JSON-LD -> {jsonld}")
        return jsonld

    # amphtml
    amp = soup.find("link", rel="amphtml")
    if amp and amp.get("href"):
        cand = urljoin(final_url, amp["href"])
        print(f"  [解決候補] amphtml -> {cand}")
        return cand

    # ページ内最初の外部リンク
    ext = find_first_external_href(soup)
    if ext:
        print(f"  [解決候補] 外部リンク -> {ext}")
        return ext

    # テキストから抽出
    found = find_urls_by_regex(soup.get_text())
    if found:
        print(f"  [解決候補] テキスト内URL -> {found}")
        return found

    return None


# --- メイン画像抽出ロジック ---


def get_main_image(url: str) -> Optional[str]:
    """
    記事URLから代表画像を取得する:
    - 中間ページ（Google News 等）は元記事に解決して再取得（1回のみ）
    - OGP / twitter / JSON-LD / body images / link rel=image_src の順で試す
    - 取得候補は validate_image_url で検証してから返す
    """
    tried = set()
    queue = [(url, True)]
    while queue:
        cur_url, allow_resolve = queue.pop(0)
        if cur_url in tried:
            continue
        tried.add(cur_url)

        fetched = fetch_html(cur_url)
        if not fetched:
            continue
        final_url, soup = fetched
        netloc = urlparse(final_url).netloc.lower()

        # Google中間ページ等なら元記事を解決して再試行 (1段のみ)
        if allow_resolve and ("news.google.com" in netloc or ("google" in netloc and "news" in final_url)):
            orig = resolve_google_news_original(final_url, soup)
            if orig and orig not in tried:
                orig_abs = urljoin(final_url, orig)
                print(f"  [中間ページ解決 -> 元記事へ再取得]: {orig_abs}")
                queue.insert(0, (orig_abs, False))
                continue
            else:
                print("  [中間ページ] 元記事解決できず、そのページでOGP探索を継続します")

        # 1) OGP/Twitter/link rel=image_src
        meta_candidates = []
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            meta_candidates.append(og["content"])
        og_secure = soup.find("meta", property="og:image:secure_url")
        if og_secure and og_secure.get("content"):
            meta_candidates.append(og_secure["content"])
        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            meta_candidates.append(tw["content"])
        link_img = soup.find("link", rel="image_src")
        if link_img and link_img.get("href"):
            meta_candidates.append(link_img["href"])

        for cand in meta_candidates:
            img = urljoin(final_url, cand)
            if is_google_cache_url(img):
                print(f"  [メタ画像除外(Googleキャッシュ)]: {img}")
                continue
            if validate_image_url(img):
                print(f"  [OGP/Twitter画像発見]: {img}")
                return img
            else:
                print(f"  [メタ画像は無効]: {img}")

        # 2) JSON-LD 内の image/thumbnail
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                js = script.string
                if not js:
                    continue
                data = json.loads(js)
                items = data if isinstance(data, list) else [data]
                for it in items:
                    if isinstance(it, dict):
                        imgfield = it.get("image") or it.get("thumbnailUrl")
                        # string / dict / list 対応
                        if isinstance(imgfield, str):
                            img = urljoin(final_url, imgfield)
                            if not is_google_cache_url(img) and validate_image_url(img):
                                print(f"  [JSON-LD画像発見]: {img}")
                                return img
                        elif isinstance(imgfield, dict):
                            urlf = imgfield.get("url")
                            if urlf:
                                img = urljoin(final_url, urlf)
                                if not is_google_cache_url(img) and validate_image_url(img):
                                    print(f"  [JSON-LD画像発見]: {img}")
                                    return img
                        elif isinstance(imgfield, list):
                            for it2 in imgfield:
                                if isinstance(it2, str):
                                    img = urljoin(final_url, it2)
                                    if not is_google_cache_url(img) and validate_image_url(img):
                                        print(f"  [JSON-LD画像発見]: {img}")
                                        return img
            except Exception:
                continue

        # 3) 本文中の画像（article/main 等）
        selectors = ["article", "main", "[role='main']", ".main-content", ".post-content", ".article-body", "#content"]
        main_content = None
        for s in selectors:
            main_content = soup.select_one(s)
            if main_content:
                print(f"  [本文コンテナ発見]: {s}")
                break
        if not main_content:
            main_content = soup.body

        if main_content:
            candidates = []
            for img_tag in main_content.find_all("img", src=True):
                src = img_tag["src"]
                if src.startswith("data:"):
                    continue
                abs_img = urljoin(final_url, src)
                if is_google_cache_url(abs_img):
                    print(f"    [本文内画像除外(Googleキャッシュ)]: {abs_img}")
                    continue
                candidates.append(abs_img)
            # 最初に有効なものを返す（必要なら大きさでソートするロジックを追加可能）
            for c in candidates:
                if validate_image_url(c):
                    print(f"  [本文内画像発見]: {c}")
                    return c
                else:
                    print(f"    [本文内画像は無効]: {c}")

        # 4) その他 meta の別キーを試す（例: og:image:secure_url already tested above）
        extra = soup.find("meta", property="og:image:secure_url")
        if extra and extra.get("content"):
            img = urljoin(final_url, extra["content"])
            if not is_google_cache_url(img) and validate_image_url(img):
                print(f"  [og:image:secure_url発見]: {img}")
                return img

        print("  [画像未発見] このURLでは見つかりませんでした。")
    return None


def extract_original_from_google_description(description_html: str) -> Optional[str]:
    """
    Google News description から最初の <a> を取り出す（もし外部URLなら直接返す）
    """
    try:
        dsoup = BeautifulSoup(description_html, "html.parser")
        a = dsoup.find("a", href=True)
        if a:
            href = a["href"]
            if href.startswith("http") and "google" not in urlparse(href).netloc:
                return href
            return href
    except Exception:
        pass
    return None


# --- メイン処理（RSS巡回 & Supabase保存） ---


def process_feed_once(feed_url: str):
    print(f"\n--- フィード処理: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
        source_name = getattr(feed.feed, "title", "不明なソース")
        is_google_news = "news.google.com" in feed_url

        for entry in feed.entries:
            article_url = None
            image_url = None

            if is_google_news:
                if hasattr(entry, "description") and entry.description:
                    orig = extract_original_from_google_description(entry.description)
                    if orig:
                        article_url = orig
                        print(f"  [Google News -> 元記事URL抽出]: {article_url}")
                    else:
                        article_url = getattr(entry, "link", None)
                        print(f"  [Google News] descriptionから抽出失敗。entry.linkを使用: {article_url}")
                else:
                    article_url = getattr(entry, "link", None)
                    print(f"  [Google News] descriptionなし。entry.linkを使用: {article_url}")

                # Googleキャッシュは除外してRSS thumbnailをフォールバック
                if hasattr(entry, "description") and entry.description:
                    dsoup = BeautifulSoup(entry.description, "html.parser")
                    img_tag = dsoup.find("img", src=True)
                    if img_tag:
                        cand = img_tag["src"]
                        if not is_google_cache_url(cand) and validate_image_url(cand):
                            image_url = cand
                            print(f"  [Google News サムネイル採用]: {image_url}")
                        else:
                            print(f"  [Google News サムネイル除外または無効]: {cand}")

            else:
                # 通常RSS
                if not hasattr(entry, "link") or not entry.link:
                    print("  [RSS] リンクなし -> スキップ")
                    continue
                article_url = entry.link

                # media_content / enclosures の優先取得（ただし google cache は除外）
                if hasattr(entry, "media_content") and entry.media_content:
                    for m in entry.media_content:
                        urlm = m.get("url")
                        if urlm and not is_google_cache_url(urlm) and validate_image_url(urlm):
                            image_url = urlm
                            print(f"  [RSS内画像発見]: {image_url}")
                            break
                if not image_url and hasattr(entry, "enclosures"):
                    for e in entry.enclosures:
                        href = e.get("href")
                        if href and e.get("type", "").startswith("image/") and not is_google_cache_url(href) and validate_image_url(href):
                            image_url = href
                            print(f"  [Enclosure画像発見]: {image_url}")
                            break

            if not article_url:
                print("  [記事URL不明] -> スキップ")
                continue

            # 重複チェック（Supabaseが設定されていれば）
            if supabase:
                existing = supabase.table("articles").select("id").eq("article_url", article_url).execute()
                if existing.data:
                    print("  [既存記事] スキップ")
                    continue

            published_dt = datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else datetime.now()

            # メイン画像を取得（OGP優先）。Google中間ページは get_main_image で解決する
            print(f"  メイン画像を取得中: {article_url}")
            scraped = get_main_image(article_url)
            if scraped:
                image_url = scraped
            else:
                print("  [最終フォールバック] RSSのサムネイル等を使用する（もしあれば）")

            article = {
                "title": getattr(entry, "title", "(無題)"),
                "article_url": article_url,
                "published_at": published_dt.isoformat(),
                "source_name": source_name,
                "image_url": image_url,
            }

            print(f"  新規記事追加: {article['title']} （image: {image_url})")
            if supabase:
                try:
                    supabase.table("articles").insert(article).execute()
                except Exception as e:
                    print(f"    [Supabase挿入エラー]: {e}")

    except Exception as e:
        print(f"  [フィード処理エラー] {feed_url} : {e}")


def main():
    """
    - 引数を指定すると単発のURL検証モード（引数: URL1 URL2 ...）
    - 引数なしで実行すると RSS_FEEDS を順に処理してSupabaseに保存（既存チェックあり）
    """
    args = sys.argv[1:]
    if args:
        # 単発検証モード（ローカルでのデバッグ向け）
        for u in args:
            print(f"\n=== 単発検証: {u}")
            img = get_main_image(u)
            if img:
                print(f"FOUND image: {img}")
            else:
                print("NO image found.")
        return

    print("データ収集バッチ開始 (パンダ版)")
    for feed_url in RSS_FEEDS:
        process_feed_once(feed_url)
    print("データ収集バッチ完了。")


if __name__ == "__main__":
    main()
