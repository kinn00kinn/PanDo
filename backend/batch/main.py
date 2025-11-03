import os
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# --- 環境変数読み込み ---
load_dotenv()

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=%E3%83%91%E3%83%B3%E3%83%80&hl=ja&gl=JP&ceid=JP:ja",
    "https://www.tokyo-zoo.net/zoo/ueno/news/atom.xml",
    "https://www.aws-s.com/topics/atom.xml",
    "https://www.worldwildlife.org/feeds/blog/posts",
    "https://nationalzoo.si.edu/news/rss.xml"
]

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SupabaseのURLとキーを環境変数に設定してください。")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def is_google_cache_url(u: str) -> bool:
    if not u:
        return False
    return "lh3.googleusercontent.com" in u or "googleusercontent" in u or "gstatic.com" in u


def fetch_html(url: str, timeout: int = 10) -> Optional[tuple]:
    """
    指定URLをGETして (final_url, BeautifulSoup) を返す。失敗時は None を返す。
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        final = resp.url
        soup = BeautifulSoup(resp.text, "html.parser")
        return final, soup
    except requests.RequestException as e:
        print(f"  [fetch_html エラー] {url} : {e}")
        return None


def resolve_google_news_original(final_url: str, soup: BeautifulSoup) -> Optional[str]:
    """
    news.google.com や Googleの中間ページを開いた際に、元記事（canonical / og:url / amphtml / 外部リンク）を探す。
    発見できれば元記事URLを返す。無ければ None。
    """
    # 1) og:url / canonical を探す
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        cand = og_url["content"]
        if not ("news.google.com" in cand or "google" in urlparse(cand).netloc):
            print(f"  [解決] og:url -> {cand}")
            return cand

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        cand = canonical["href"]
        if not ("news.google.com" in cand or "google" in urlparse(cand).netloc):
            print(f"  [解決] canonical -> {cand}")
            return cand

    # 2) amphtml を探す
    amp = soup.find("link", rel="amphtml")
    if amp and amp.get("href"):
        cand = amp["href"]
        # amp は元記事側のAMPページの可能性が高い（それ自体をさらに解決する）
        print(f"  [解決候補] amphtml -> {cand}")
        return cand

    # 3) ページ内の外部リンクを探す（最初の外部href）
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # data: や javascript: などは除外
        if href.startswith("http") and not ("news.google.com" in href or "google.com" in href or "accounts.google.com" in href):
            # 外部の実URLっぽければ採用
            print(f"  [解決候補] 外部リンク -> {href}")
            return href

    # 見つからなかった
    return None


def get_main_image(url: str) -> Optional[str]:
    """
    記事URLからOGP/tw:image/本文中画像を取得する。
    news.google.com 等の中間ページは元記事に解決して再取得する（1回だけ）。
    """
    tried_urls = set()
    to_try = [(url, True)]  # (url, allow_resolve_google_news)
    while to_try:
        current_url, allow_resolve_google_news = to_try.pop(0)
        if current_url in tried_urls:
            continue
        tried_urls.add(current_url)

        fetched = fetch_html(current_url)
        if not fetched:
            continue
        final_url, soup = fetched
        parsed_netloc = urlparse(final_url).netloc.lower()

        # もしGoogleニュース等の中間ページなら、元記事URLを探して再試行（1段階のみ）
        if allow_resolve_google_news and ("news.google.com" in parsed_netloc or "google" in parsed_netloc and "news" in final_url):
            orig = resolve_google_news_original(final_url, soup)
            if orig and orig not in tried_urls:
                # absolute化
                orig = urljoin(final_url, orig)
                print(f"  [中間ページ解決 -> 元記事へ再取得]: {orig}")
                # 追跡は1回だけ（allow_resolve_google_news=False）
                to_try.insert(0, (orig, False))
                continue
            else:
                print("  [中間ページ] 元記事解決できず、そのページでOGP探索を継続します")

        # --- OGP ---
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            img = urljoin(final_url, og_image["content"])
            if not is_google_cache_url(img):
                print(f"  [OGP画像発見]: {img}")
                return img
            else:
                print(f"  [OGP画像除外(Googleキャッシュ)]: {img}")

        # --- twitter:image ---
        tw_image = soup.find("meta", attrs={"name": "twitter:image"})
        if tw_image and tw_image.get("content"):
            img = urljoin(final_url, tw_image["content"])
            if not is_google_cache_url(img):
                print(f"  [Twitter画像発見]: {img}")
                return img
            else:
                print(f"  [Twitter画像除外(Googleキャッシュ)]: {img}")

        # --- 本文中の画像（article/main 等）---
        content_selectors = ["article", "main", "[role='main']", ".main-content", ".post-content", ".article-body", "#content"]
        main_content = None
        for sel in content_selectors:
            main_content = soup.select_one(sel)
            if main_content:
                print(f"  [本文コンテナ発見]: {sel}")
                break
        if not main_content:
            main_content = soup.body

        if main_content:
            # 優先順位：大きそうな画像を探す（width/height属性やファイル名）、ただし簡易実装として最初の有効画像を使う
            candidates = []
            for img_tag in main_content.find_all("img", src=True):
                src = img_tag["src"]
                if src.startswith("data:"):
                    continue
                abs_img = urljoin(final_url, src)
                if is_google_cache_url(abs_img):
                    print(f"    [本文内画像除外(Googleキャッシュ)]: {abs_img}")
                    continue
                candidates.append((abs_img, img_tag))
            if candidates:
                # 今は単純に最初の候補を返すが、必要ならサイズなどでソート可能
                chosen = candidates[0][0]
                print(f"  [本文内画像発見]: {chosen}")
                return chosen

        # --- 最後の手段: ページ内にある他の画像metaやリンクを探す ---
        # 例: og:image:secure_url, og:image:alt など
        meta_img = soup.find("meta", property="og:image:secure_url")
        if meta_img and meta_img.get("content"):
            img = urljoin(final_url, meta_img["content"])
            if not is_google_cache_url(img):
                print(f"  [og:image:secure_url発見]: {img}")
                return img

        # 見つからなければ次のURLへ（もしto_tryにあるなら）
        print("  [画像未発見] このURLでは見つかりませんでした。")
    return None


def extract_original_from_google_description(description_html: str) -> Optional[str]:
    """
    Google Newsのdescription HTMLから元記事のリンクを抽出（first <a>）する。
    """
    try:
        dsoup = BeautifulSoup(description_html, "html.parser")
        a = dsoup.find("a", href=True)
        if a:
            return a["href"]
    except Exception:
        return None
    return None


def main():
    print("データ収集バッチ開始 (パンダ版)")

    for feed_url in RSS_FEEDS:
        print(f"フィードを処理中: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            source_name = getattr(feed.feed, "title", "不明なソース")
            is_google_news = "news.google.com" in feed_url

            for entry in feed.entries:
                article_url = None
                image_url = None

                if is_google_news:
                    # Google News 特別処理: description から元記事URLを優先取得
                    if hasattr(entry, "description") and entry.description:
                        orig = extract_original_from_google_description(entry.description)
                        if orig:
                            article_url = orig
                            print(f"  [Google News -> 元記事URL抽出]: {article_url}")
                        else:
                            # fallback: entry.link might be a google-news intermediate link; we'll use it but get_main_imageで解決を試みる
                            article_url = getattr(entry, "link", None)
                            print(f"  [Google News] descriptionからURL抽出失敗。entry.linkを使用: {article_url}")
                    else:
                        article_url = getattr(entry, "link", None)
                        print(f"  [Google News] descriptionなし。entry.linkを使用: {article_url}")

                    # サムネイル（RSS内）は一応取得するが、Googleキャッシュは除外
                    if hasattr(entry, "description") and entry.description:
                        dsoup = BeautifulSoup(entry.description, "html.parser")
                        img_tag = dsoup.find("img", src=True)
                        if img_tag:
                            cand = img_tag["src"]
                            if not is_google_cache_url(cand):
                                image_url = cand
                                print(f"  [Google News サムネイル採用]: {image_url}")
                            else:
                                print(f"  [Google News サムネイル除外]: {cand}")

                else:
                    # 通常RSS
                    if not hasattr(entry, "link") or not entry.link:
                        print("  [RSS] リンクなし -> スキップ")
                        continue
                    article_url = entry.link

                    # RSS 内 image/media/enclosure を優先的に拾う（ただし google cache は除外）
                    if hasattr(entry, "media_content") and entry.media_content:
                        images = [m.get("url") for m in entry.media_content if m.get("url")]
                        for img in images:
                            if not is_google_cache_url(img):
                                image_url = img
                                print(f"  [RSS内画像発見]: {image_url}")
                                break
                    if not image_url and hasattr(entry, "enclosures"):
                        for e in entry.enclosures:
                            href = e.get("href")
                            if href and not is_google_cache_url(href) and e.get("type", "").startswith("image/"):
                                image_url = href
                                print(f"  [Enclosure画像発見]: {image_url}")
                                break

                if not article_url:
                    print("  [記事URL不明] -> スキップ")
                    continue

                # 重複チェック
                existing = supabase.table("articles").select("id").eq("article_url", article_url).execute()
                if existing.data:
                    print("  [既存記事] スキップ")
                    continue

                published_dt = datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else datetime.now()

                # メイン画像を取得（OGP優先）。Google中間ページは get_main_image 側で解決する
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

                print(f"  新規記事追加: {article['title']}")
                supabase.table("articles").insert(article).execute()

        except Exception as e:
            print(f"  [フィード処理エラー] {feed_url} : {e}")
            continue

    print("データ収集バッチ完了。")


if __name__ == "__main__":
    main()
