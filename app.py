import re

import streamlit as st

from extractor import DEFAULT_CONTENT_SELECTORS, extract, suggest_link_filter

st.set_page_config(page_title="Web Page Extractor", page_icon="📄", layout="centered")
st.title("📄 Web Page Extractor")
st.caption(
    "Enter a page address. The app follows the chapter links on that page and "
    "combines them into one HTML file with a table of contents."
)

url = st.text_input(
    "Web page address",
    placeholder="https://zerodha.com/varsity/module/sector-analysis/",
)
doc_title = st.text_input("Document title (optional)", placeholder="Uses the page's heading if left blank")

with st.expander("Advanced options"):
    follow_links = st.checkbox("Follow links on the page (uncheck to extract just this page)", value=True)
    link_filter = st.text_input(
        "Only follow links containing",
        value=suggest_link_filter(url) if url else "",
        help="For Zerodha Varsity this is /varsity/chapter/. Leave blank to follow every link on the same site.",
        key=f"filter-{url}",
    )
    selectors = st.text_input(
        "Content selectors (CSS, tried in order)",
        value=DEFAULT_CONTENT_SELECTORS,
        help="The first selector that matches on each page is used as its content.",
    )
    max_pages = st.number_input("Maximum pages to fetch", 1, 500, 100)
    delay = st.slider("Delay between requests (seconds)", 0.0, 3.0, 0.5, 0.1)

if st.button("Extract", type="primary", disabled=not url):
    if not re.match(r"^https?://", url.strip()):
        url = "https://" + url.strip()
    bar = st.progress(0.0, text="Fetching index page…")

    def on_progress(done, total, msg):
        bar.progress(done / total if total else 1.0, text=msg)

    try:
        html_out, title, sections, errors = extract(
            url.strip(), doc_title, link_filter.strip(), selectors,
            int(max_pages), follow_links, delay, on_progress,
        )
    except Exception as e:
        bar.empty()
        st.error(f"Could not fetch {url}: {e}")
    else:
        st.session_state["result"] = (html_out, title, len(sections), errors)

if "result" in st.session_state:
    html_out, title, count, errors = st.session_state["result"]
    st.success(f"Extracted {count} section(s) into “{title}”.")
    if errors:
        with st.expander(f"{len(errors)} page(s) failed"):
            for link, err in errors:
                st.write(f"- {link}: {err}")
    filename = re.sub(r"[^\w\-]+", "_", title).strip("_")[:80] or "extracted"
    st.download_button(
        "⬇️ Download HTML", html_out.encode("utf-8"),
        file_name=f"{filename}.html", mime="text/html", type="primary",
    )
    with st.expander("Preview"):
        st.components.v1.html(html_out, height=600, scrolling=True)
