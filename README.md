# Web Page Extractor

Streamlit app: enter a page address, it follows the chapter links on that page and
combines them into one downloadable HTML file with a table of contents.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy to Streamlit Community Cloud
1. Put `app.py`, `extractor.py` and `requirements.txt` in a GitHub repo.
2. At share.streamlit.io choose **New app**, pick the repo, set main file to `app.py`.

## Options
- **Only follow links containing**: auto-fills `/varsity/chapter/` for Zerodha Varsity.
  Blank = every link on the same site.
- **Content selectors**: CSS selectors tried in order for each page's main content.
- Uncheck **Follow links** to extract just the one page.
