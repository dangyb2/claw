import time
import random
import pandas as pd
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ============================================================
# CONFIG
# ============================================================

EXISTING_JSON_PATH = "goodreads_books_cleaned_english.json"
OUTPUT_CSV = "balanced_dataset_additions.csv"

# Only the genres that actually need more data (based on F1 scores + dataset counts).
# Genres with plenty of data (romance, fiction, thriller, etc.) are excluded.
TAG_MAP = {
    "essay":      ["essays", "creative-nonfiction", "essay-collection"],
    "anthology":  ["anthologies", "short-stories", "anthology"],
    "technology": ["technology", "computers", "artificial-intelligence"],
    "sports":     ["sports", "baseball", "basketball", "football", "soccer"],
    "western":    ["westerns", "western", "frontier"],
    "self_help":  ["self-help", "personal-development", "productivity"],
}

# How many NEW books to gather per genre before stopping.
GENRE_CAPS = {
    "essay":      20000,
    "anthology":   15000,
    "technology":  10000,
    "sports":      10000,
    "western":     8000,
    "self_help":   5500,
}

MAX_TAG_PAGES  = 5   # pages of list results per tag  (~30 lists/page)
MAX_LIST_PAGES = 5   # pages deep per individual list (~100 books/page)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ============================================================
# PHASE 1: Get list URLs from a Listopia tag page
# ============================================================

def get_list_urls_for_tag(page, tag, max_pages=MAX_TAG_PAGES):
    """Collect Listopia list URLs for a given tag."""
    list_urls = []

    for p in range(1, max_pages + 1):
        url = f"https://www.goodreads.com/list/tag/{tag}?page={p}"
        print(f"  [Tag '{tag}' page {p}] {url}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1500)
        except Exception:
            print(f"  ⚠️ Timeout on tag page {p}, stopping.")
            break

        links = page.locator("a.listTitle")
        count = links.count()

        if count == 0:
            print(f"  No lists found on page {p}. Tag exhausted.")
            break

        for i in range(count):
            href = links.nth(i).get_attribute("href")
            if href:
                full = f"https://www.goodreads.com{href}" if href.startswith("/") else href
                if full not in list_urls:
                    list_urls.append(full)

        print(f"  → {count} lists found (total so far: {len(list_urls)})")
        time.sleep(random.uniform(1.5, 3.5))

    return list_urls


# ============================================================
# PHASE 2: Get book URLs from a single Listopia list
# ============================================================

def get_book_urls_from_list(page, list_url, existing_titles, max_pages=MAX_LIST_PAGES):
    """Collect new book URLs from a Listopia list (handles pagination)."""
    book_entries = []

    for p in range(1, max_pages + 1):
        url = f"{list_url}?page={p}"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector('tr[itemtype="http://schema.org/Book"]', timeout=10000)
        except Exception:
            break

        rows = page.locator('tr[itemtype="http://schema.org/Book"]').all()
        new_count = 0

        for row in rows:
            title_el = row.locator("a.bookTitle span")
            link_el  = row.locator("a.bookTitle")

            if title_el.count() == 0 or link_el.count() == 0:
                continue

            title = title_el.first.inner_text().strip()
            if title.lower() in existing_titles:
                continue

            href = link_el.first.get_attribute("href")
            if not href:
                continue

            full_url = f"https://www.goodreads.com{href}" if href.startswith("/") else href
            book_entries.append({"title": title, "url": full_url})
            existing_titles.add(title.lower())
            new_count += 1

        print(f"    [List page {p}] {new_count} new books")

        if new_count == 0:
            break

        time.sleep(random.uniform(1, 2.5))

    return book_entries


# ============================================================
# PHASE 3: Fetch description + genres for each book
# ============================================================

def fetch_book_details(page, book_url):
    """Navigate to a book page and extract description and genres."""
    details = {"description": None, "genres": None}

    try:
        page.goto(book_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2000)

        # --- DESCRIPTION ---
        if page.locator('meta[property="og:description"]').count() > 0:
            details["description"] = (
                page.locator('meta[property="og:description"]')
                .first.get_attribute("content")
                .strip()
            )
        elif page.locator('meta[name="description"]').count() > 0:
            details["description"] = (
                page.locator('meta[name="description"]')
                .first.get_attribute("content")
                .strip()
            )
        elif page.locator('div[data-testid="description"]').count() > 0:
            details["description"] = (
                page.locator('div[data-testid="description"]')
                .first.inner_text()
                .strip()
            )

        # --- GENRES ---
        genre_links = page.locator('[data-testid="genresList"] a[href*="/genres/"]')
        if genre_links.count() == 0:
            genre_links = page.locator('.BookPageMetadataSection__genres a[href*="/genres/"]')

        if genre_links.count() > 0:
            raw_genres = genre_links.all_inner_texts()
            clean_genres = []
            for g in raw_genres:
                g = g.strip()
                if g and "more" not in g.lower() and g not in clean_genres:
                    clean_genres.append(g)
            if clean_genres:
                details["genres"] = ", ".join(clean_genres)

    except Exception:
        print(f"    [SKIPPED] Timeout or error on: {book_url}")

    return details


# ============================================================
# MAIN SCRAPER
# ============================================================

def scrape_genre(genre_label, tags, existing_titles, cap):
    """Run all 3 phases for one genre label across multiple tags."""
    all_books_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # ── Phase 1 + 2: collect book URLs ──────────────────
        gather_context = browser.new_context(user_agent=USER_AGENT)
        gather_page    = gather_context.new_page()

        urls_to_scrape = []

        for tag in tags:
            if len(urls_to_scrape) >= cap:
                print(f"  ✅ Cap of {cap:,} reached. Skipping remaining tags.")
                break

            print(f"\n  ▸ Collecting lists for tag: '{tag}'")
            list_urls = get_list_urls_for_tag(gather_page, tag)
            print(f"  ▸ Found {len(list_urls)} lists for tag '{tag}'")

            for i, list_url in enumerate(list_urls, 1):
                if len(urls_to_scrape) >= cap:
                    print(f"  ✅ Cap of {cap:,} reached. Skipping remaining lists.")
                    break

                print(f"  ▸ List {i}/{len(list_urls)}: {list_url}")
                entries = get_book_urls_from_list(gather_page, list_url, existing_titles)
                urls_to_scrape.extend(entries)
                print(f"    Running total: {len(urls_to_scrape):,} / {cap:,}")
                time.sleep(random.uniform(2, 4))

        gather_context.close()

        # Trim to exact cap in case the last list pushed us over
        urls_to_scrape = urls_to_scrape[:cap]
        print(f"\n--- PHASE 3: Fetching details for {len(urls_to_scrape):,} books ---")

        # ── Phase 3: fetch details ───────────────────────────
        fetch_context = browser.new_context(user_agent=USER_AGENT)
        fetch_page    = fetch_context.new_page()

        for idx, book in enumerate(urls_to_scrape, 1):
            print(f" [{idx}/{len(urls_to_scrape)}] {book['title']}")
            details = fetch_book_details(fetch_page, book["url"])

            if details["description"]:
                genre_value = details["genres"] if details["genres"] else genre_label
                print(f"    [SUCCESS] {genre_value[:60]}...")
                all_books_data.append({
                    "title":       book["title"],
                    "description": details["description"],
                    "genre":       genre_value,
                })
            else:
                print(f"    [FAILED] No description.")

            time.sleep(random.uniform(1, 3))

        fetch_context.close()
        browser.close()

    return all_books_data


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("Loading existing dataset...")
    try:
        existing_data = []
        with open(EXISTING_JSON_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        obj = json.loads(line)
                        existing_data.append(obj["title"])
                    except:
                        continue
        existing_titles = set(t.lower().strip() for t in existing_data if isinstance(t, str))
        print(f"✅ Loaded {len(existing_titles):,} existing titles to skip.")
    except Exception as e:
        print(f"⚠️ Could not load existing JSON ({e}). Starting fresh.")
        existing_titles = set()

    all_new_books = []

    # Sort by most urgent first (lowest F1 / smallest dataset)
    priority_order = []

    for genre_label in priority_order:
        tags = TAG_MAP[genre_label]
        cap  = GENRE_CAPS[genre_label]

        print(f"\n{'='*55}")
        print(f"▶ GENRE: {genre_label.upper()}  |  Cap: {cap:,}  |  Tags: {tags}")
        print(f"{'='*55}")

        results = scrape_genre(genre_label, tags, existing_titles, cap)

        if results:
            all_new_books.extend(results)
            pd.DataFrame(all_new_books).to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
            print(f"💾 Saved. Total new books so far: {len(all_new_books):,}")

        print("Sleeping 15s before next genre...")
        time.sleep(15)

    print(f"\n🎉 DONE! {len(all_new_books):,} new books saved to {OUTPUT_CSV}")