import time
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://online.atletika.cz/clenska-sekce/oddily/adresar-oddilu/"
SEASON = "2026"
OUT_CSV = "clubs_database.csv"
OUT_JSON = "clubs_database.json"

# Official region names exactly as shown in the filter.
REGIONS = [
    "Pražský",
    "Středočeský",
    "Jihočeský",
    "Plzeňský",
    "Karlovarský",
    "Ústecký",
    "Liberecký",
    "Královéhradecký",
    "Pardubický",
    "Vysočina",
    "Jihomoravský",
    "Olomoucký",
    "Zlínský",
    "Moravskoslezský",
]


def wait_for_table_to_refresh(page):
    """Wait until the table body is present and stable after filtering."""
    page.wait_for_selector("table tbody tr", timeout=15000)
    # Small stabilization pause because the site updates the table asynchronously.
    page.wait_for_timeout(600)


def read_rows_from_current_table(page, region_name: str):
    rows = page.query_selector_all("table tbody tr")
    clubs = []

    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) < 5:
            continue

        zkratka = cells[1].inner_text().strip()
        nazev = cells[2].inner_text().strip()
        kontakt = cells[3].inner_text().strip() if len(cells) > 3 else ""
        adresa = cells[4].inner_text().strip() if len(cells) > 4 else ""

        if not zkratka or not nazev:
            continue

        clubs.append(
            {
                "zkratka": zkratka,
                "nazev": nazev,
                "kraj": region_name,
                "kontakt": kontakt,
                "adresa": adresa,
            }
        )

    return clubs


def scrape_region(page, region_name: str):
    print(f"Scraping kraj: {region_name}")

    # Set season if the filter exists.
    try:
        season_select = page.locator("select").nth(0)
        season_select.select_option(label=SEASON)
        page.wait_for_timeout(200)
    except Exception:
        pass

    # Select the official region from the second select element.
    region_select = page.locator("select").nth(1)
    region_select.select_option(label=region_name)

    # Click the filter button.
    filter_button = page.get_by_role("button", name="FILTRUJ")
    filter_button.click()

    wait_for_table_to_refresh(page)
    region_rows = read_rows_from_current_table(page, region_name)
    print(f"  -> nalezeno {len(region_rows)} oddílů")
    return region_rows


def main():
    all_clubs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1200})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        # Accept cookie banner if it appears.
        try:
            page.get_by_role("button", name="Souhlasím").click(timeout=2000)
            page.wait_for_timeout(500)
        except PlaywrightTimeoutError:
            pass
        except Exception:
            pass

        # Make sure the filter controls are visible.
        page.wait_for_selector("select", timeout=15000)

        for region in REGIONS:
            try:
                region_clubs = scrape_region(page, region)
                all_clubs.extend(region_clubs)
            except Exception as e:
                print(f"Chyba při zpracování kraje {region}: {e}")

        browser.close()

    df = pd.DataFrame(all_clubs)

    if df.empty:
        raise RuntimeError(
            "Nepodařilo se načíst žádné oddíly. Zkontroluj selektory stránky nebo změny v HTML."
        )

    # Deduplicate because some rows can appear multiple times across refreshes.
    df = df.drop_duplicates(subset=["zkratka", "nazev", "kraj"]).reset_index(drop=True)
    df = df[["zkratka", "nazev", "kraj", "kontakt", "adresa"]]
    df = df.sort_values(by=["kraj", "nazev"], kind="stable").reset_index(drop=True)

    df.to_csv(OUT_CSV, index=False)
    df.to_json(OUT_JSON, orient="records", force_ascii=False)

    print("Hotovo.")
    print("Počet klubů:", len(df))
    print(df.groupby("kraj").size().to_string())
    print(df.head(15).to_string(index=False))


if __name__ == "__main__":
    main()