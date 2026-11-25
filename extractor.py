"""Core extraction logic: fetch an index page, follow its chapter links,
and combine everything into one HTML file with a table of contents."""

import html
import time
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
DEFAULT_CONTENT_SELECTORS = "div.post, article, main, body"


def suggest_link_filter(url: str) -> str:
    """Sensible default for which links to follow, based on the site."""
    host = urlparse(url).netloc
    if "zerodha.com" in host and "/varsity/" in url:
        return "/varsity/chapter/"
    return ""


def fetch_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def page_title(soup: BeautifulSoup, fallback: str) -> str:
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return fallback


def collect_links(soup: BeautifulSoup, base_url: str, link_filter: str):
    """Return [(title, absolute_url)] in page order, de-duplicated.

    If link_filter is given, keep links whose URL contains it.
    Otherwise keep links on the same site, excluding the page itself.
    """
    base_host = urlparse(base_url).netloc
    base_clean = urldefrag(base_url)[0].rstrip("/")
    links, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        abs_url = urldefrag(urljoin(base_url, href))[0]
        if link_filter:
            if link_filter not in abs_url:
                continue
        else:
            if urlparse(abs_url).netloc != base_host or abs_url.rstrip("/") == base_clean:
                continue
        title = a.get_text(" ", strip=True)
        if not title or abs_url in seen:
            continue
        seen.add(abs_url)
        links.append((title, abs_url))
    return links


def extract_content(soup: BeautifulSoup, page_url: str, selectors: str) -> str:
    """Pick the main content block and make image/link URLs absolute
    so the downloaded file still shows images offline-from-site."""
    node = None
    for sel in [s.strip() for s in selectors.split(",") if s.strip()]:
        node = soup.select_one(sel)
        if node:
            break
    if node is None:
        return "<p>Content not found.</p>"
    for tag in node.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    for img in node.find_all("img"):
        src = img.get("data-src") or img.get("data-lazy-src") or img.get("src")
        if src:
            img["src"] = urljoin(page_url, src)
        img.attrs.pop("srcset", None)
    for a in node.find_all("a", href=True):
        a["href"] = urljoin(page_url, a["href"])
    return str(node)


def build_html(doc_title: str, sections) -> str:
    """sections: [(title, url, body_html)]"""
    t = html.escape(doc_title)
    toc, articles = [], []
    for idx, (title, url, body) in enumerate(sections, start=1):
        anchor = f"issue-{idx}"
        et, eu = html.escape(title), html.escape(url, quote=True)
        toc.append(f'<li><a href="#{anchor}">{et}</a></li>')
        articles.append(f"""
    <article id="{anchor}" class="chapter">
      <h2>{et}</h2>
      <div class="source-link"><a href="{eu}" target="_blank">{eu}</a></div>
      {body}
      <p class="back-top"><a href="#top">↑ Back to Table of Contents</a></p>
    </article>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; line-height: 1.65; color: #222; }}
    h1 {{ border-bottom: 2px solid #eee; padding-bottom: 12px; }}
    #toc ul {{ columns: 2; column-gap: 32px; padding-left: 20px; }}
    #toc li {{ margin-bottom: 6px; font-size: 0.92rem; }}
    a {{ color: #387ed1; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .chapter {{ margin-top: 48px; padding-top: 24px; border-top: 2px solid #eee; }}
    .source-link {{ font-size: 0.85rem; margin-bottom: 16px; color: #666; }}
    .back-top {{ margin-top: 20px; font-size: 0.9rem; }}
    img {{ max-width: 100%; height: auto; }}
    @media (max-width: 640px) {{ #toc ul {{ columns: 1; }} }}
  </style>
</head>
<body id="top">
  <h1>{t}</h1>
  <section id="toc">
    <h2>Table of Contents ({len(sections)} sections)</h2>
    <ul>
      {"".join(toc)}
    </ul>
  </section>
  <main>
    {"".join(articles)}
  </main>
</body>
</html>
"""


def extract(url, doc_title="", link_filter="", selectors=DEFAULT_CONTENT_SELECTORS,
            max_pages=100, follow_links=True, delay=0.5, progress=None):
    """Run the whole extraction. `progress(done, total, message)` is optional.
    Returns (html_string, doc_title, sections, errors)."""
    index_soup = fetch_soup(url)
    doc_title = doc_title.strip() or page_title(index_soup, url)

    links = collect_links(index_soup, url, link_filter) if follow_links else []
    links = links[:max_pages]

    sections, errors = [], []
    if not links:
        # Nothing to follow: extract the page itself.
        sections.append((doc_title, url, extract_content(index_soup, url, selectors)))
        if progress:
            progress(1, 1, "Extracted the page itself (no links to follow).")
    else:
        for i, (title, link) in enumerate(links, start=1):
            if progress:
                progress(i - 1, len(links), f"[{i}/{len(links)}] {title}")
            try:
                body = extract_content(fetch_soup(link), link, selectors)
            except Exception as e:  # keep going on single-page failures
                errors.append((link, str(e)))
                body = f"<p>Failed to load: {html.escape(str(e))}</p>"
            sections.append((title, link, body))
            if i < len(links):
                time.sleep(delay)
        if progress:
            progress(len(links), len(links), "Done")

    return build_html(doc_title, sections), doc_title, sections, errors
