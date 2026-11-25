# Web Site Pull

A Streamlit web app that turns a multi-page website section (for example a
[Zerodha Varsity](https://zerodha.com/varsity/) module) into **one HTML file**
with a clickable table of contents, ready to read offline or print.

## What it does

1. You enter a web page address, such as a module or index page.
2. The app finds the chapter links on that page.
3. It downloads each linked page and keeps only its main content
   (scripts, menus and other clutter are removed).
4. Everything is combined into a single HTML file with a table of contents
   and "Back to top" links. Image and link addresses are made absolute, so
   pictures still load when you open the file.
5. You download the file with one click, or preview it in the app first.

If a chapter fails to load, the app skips it, keeps going, and lists the
failures at the end.

## Using the app

| Field | What it does |
|---|---|
| **Web page address** | The index page whose links you want to collect. |
| **Document title** | Title for the output file. Leave blank to use the page's own heading. |

Under **Advanced options**:

| Option | Default | What it does |
|---|---|---|
| Follow links on the page | On | Turn off to extract only the page you entered. |
| Only follow links containing | `/varsity/chapter/` on Varsity pages, otherwise blank | Only links whose address contains this text are followed. Blank follows every link on the same site. |
| Content selectors | `div.post, article, main, body` | CSS selectors tried in order; the first that matches on each page is kept as its content. |
| Maximum pages to fetch | 100 | Upper limit on how many linked pages are downloaded. |
| Delay between requests | 0.5 s | Pause between pages so the site isn't overloaded. |

### Example

- Address: `https://zerodha.com/varsity/module/sector-analysis/`
- Title: `Sector Analysis`
- Click **Extract**, wait for the progress bar, then **Download HTML**.

## Run locally

Requires Python 3.9 or newer.

```bash
git clone https://github.com/SeetharamanM/web-site-pull.git
cd web-site-pull
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Deploy to Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. Click **Create app** (or **New app**) and choose **Deploy a public app from GitHub**.
3. Set **Repository** to `SeetharamanM/web-site-pull`, **Branch** to `main`,
   and **Main file path** to `app.py`.
4. Click **Deploy**. Streamlit installs `requirements.txt` and gives you a public URL.

Every push to `main` redeploys the app automatically.

## Project files

| File | Purpose |
|---|---|
| `app.py` | Streamlit user interface. |
| `extractor.py` | Fetching, link collection, content cleanup and HTML building. Can be used on its own from Python. |
| `requirements.txt` | Python dependencies (`streamlit`, `requests`, `beautifulsoup4`). |

### Using the extractor without the UI

```python
from extractor import extract

html, title, sections, errors = extract(
    "https://zerodha.com/varsity/module/sector-analysis/",
    doc_title="Sector Analysis",
    link_filter="/varsity/chapter/",
)
open("Sector_Analysis.html", "w", encoding="utf-8").write(html)
```

## Notes

- Use it only on content you're allowed to download, and keep the delay
  reasonable to respect the site.
- Pages that build their content with JavaScript may come out empty, because
  the app reads the HTML the server sends and doesn't run scripts.
- If a site's main content lives in a different element, add its CSS selector
  to the front of **Content selectors**.
