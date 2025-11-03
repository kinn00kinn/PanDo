#!/usr/bin/env python3
import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

MIN_IMAGE_BYTES = 1024  # 最低バイト数（必要に応じて調整）

def is_google_cache_url(u: str) -> bool:
    if not u:
        return False
    return any(x in u for x in ("lh3.googleusercontent.com", "googleusercontent", "gstatic.com"))

def fetch_html(url: str, timeout=10):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ImageChecker/1.0)"}
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.url, BeautifulSoup(r.text, "html.parser")

def validate_image_url(url: str, timeout=8) -> bool:
    try:
        # HEAD で確認
        h = requests.head(url, timeout=timeout, allow_redirects=True)
        if h.status_code >= 400:
            # fallback to small GET
            g = requests.get(url, timeout=timeout, stream=True)
            if g.status_code >= 400:
                return False
            ct = g.headers.get("Content-Type", "")
            length = g.headers.get("Content-Length")
            if ct.startswith("image/") and (length is None or int(length) >= MIN_IMAGE_BYTES):
                g.close()
                return True
            g.close()
            return False
        ct = h.headers.get("Content-Type", "")
        if not ct.startswith("image/"):
            return False
        length = h.headers.get("Content-Length")
        if length and int(length) < MIN_IMAGE_BYTES:
            return False
        return True
    except Exception:
        return False

def resolve_google_news_original(final_url: str, soup: BeautifulSoup):
    # 1. og:url
    og = soup.find("meta", property="og:url")
    if og and og.get("content"):
        c = og["content"]
        if c.startswith("http") and "google" not in urlparse(c).netloc:
            return c
    # 2. canonical
    can = soup.find("link", rel="canonical")
    if can and can.get("href"):
        c = can["href"]
        if c.startswith("http") and "google" not in urlparse(c).netloc:
            return c
    # 3. amphtml
    amp = soup.find("link", rel="amphtml")
    if amp and amp.get("href"):
        return urljoin(final_url, amp["href"])
    # 4. JSON-LD
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
            if isinstance(data, dict):
                url = data.get("url") or data.get("@id")
                if url and url.startswith("http") and "google" not in urlparse(url).netloc:
                    return url
        except Exception:
            continue
    # 5. ページ内の最初の外部リンク
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "google" not in urlparse(href).netloc:
            return href
    return None

def get_main_image(url: str):
    tried = set()
    queue = [(url, True)]
    while queue:
        cur, allow_resolve = queue.pop(0)
        if cur in tried:
            continue
        tried.add(cur)
        try:
            final, soup = fetch_html(cur)
        except Exception as e:
            print(f"  [fetch_html failed] {cur} -> {e}")
            continue

        net = urlparse(final).netloc.lower()
        if allow_resolve and ("news.google.com" in net or ("google" in net and "news" in final)):
            orig = resolve_google_news_original(final, soup)
            if orig and orig not in tried:
                orig = urljoin(final, orig)
                print(f"  [resolved -> original] {orig}")
                queue.insert(0, (orig, False))
                continue
            else:
                print("  [middle page] cannot resolve original; continue checking this page")

        # 1. OGP
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            img = urljoin(final, og["content"])
            if not is_google_cache_url(img) and validate_image_url(img):
                return img
            else:
                print(f"  [og:image invalid/ignored] {img}")

        # 2. twitter:image
        tw = soup.find("meta", attrs={"name":"twitter:image"})
        if tw and tw.get("content"):
            img = urljoin(final, tw["content"])
            if not is_google_cache_url(img) and validate_image_url(img):
                return img
            else:
                print(f"  [twitter:image invalid/ignored] {img}")

        # 3. JSON-LD image
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(s.string or "{}")
                if isinstance(data, dict):
                    imgf = data.get("image") or data.get("thumbnailUrl")
                    if isinstance(imgf, str):
                        img = urljoin(final, imgf)
                        if not is_google_cache_url(img) and validate_image_url(img):
                            return img
            except Exception:
                continue

        # 4. 本文内画像（最初の有効なもの）
        selectors = ["article","main","[role='main']", ".post-content", ".article-body", "#content"]
        main_area = None
        for sel in selectors:
            main_area = soup.select_one(sel)
            if main_area:
                break
        if not main_area:
            main_area = soup.body

        if main_area:
            imgs = main_area.find_all("img", src=True)
            for img_tag in imgs:
                src = img_tag["src"]
                if src.startswith("data:"):
                    continue
                absimg = urljoin(final, src)
                if is_google_cache_url(absimg):
                    continue
                if validate_image_url(absimg):
                    return absimg

        # 5. link rel=image_src
        link_img = soup.find("link", rel="image_src")
        if link_img and link_img.get("href"):
            img = urljoin(final, link_img["href"])
            if not is_google_cache_url(img) and validate_image_url(img):
                return img

        print("  [no image found on this URL]")
    return None

def download_image(img_url: str, dest_dir="downloaded_images"):
    os.makedirs(dest_dir, exist_ok=True)
    parsed = urlparse(img_url)
    name = os.path.basename(parsed.path) or "image"
    # シンプルに連番やタイムスタンプを付けても良い
    local = os.path.join(dest_dir, name)
    i = 1
    base, ext = os.path.splitext(local)
    while os.path.exists(local):
        local = f"{base}_{i}{ext}"
        i += 1
    with requests.get(img_url, stream=True) as r:
        r.raise_for_status()
        with open(local, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    return local

def main():
    urls = sys.argv[1:] if len(sys.argv) > 1 else []
    if not urls:
        print("Usage: python test_fetch_image.py <url1> [url2] ...")
        return
    for u in urls:
        print(f"\n== Processing: {u}")
        img = get_main_image(u)
        if img:
            print(f"FOUND image: {img}")
            try:
                saved = download_image(img)
                print(f"Saved to: {saved}")
            except Exception as e:
                print(f"Failed to download image: {e}")
        else:
            print("NO image found.")

if __name__ == "__main__":
    main()
