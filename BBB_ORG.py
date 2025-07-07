# Save this as bbb_scraper_playwright.py and run using: python bbb_scraper_playwright.py
# Make sure to install required packages first:
# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import csv
import time
import random
import os
import gc
import signal
from datetime import datetime

# --- CONFIGURATION ---
CATEGORIES = ["motorcycle-dealers", "Appliance-Repair",
              "handyman", "Car+Wash", "Locksmith", "Security-Guards"]

city_url_tuples = [
    (["Salt Lake City", "West Valley City", "Saint George", "Ogden", "Logan", "Moab",
     "West Jordan", "Orem", "Lehi", "Sandy", "South Jordan", "Layton", "Provo"], "UT"),
    (["Denver", "Colorado Springs", "Aurora", "Fort Collins",
     "Lakewood", "Thornton", "Pueblo", "Arvada", "Westminster"], "CO"),
    (["Wichita", "Overland Park", "Kansas City", "Olathe",
     "Topeka", "Lawrence", "Shawnee", "Manhattan", "Lenexa"], "KS"),
    (["Oklahoma City", "Tulsa", "Norman", "Broken Arrow", "Edmond", "Lawton"], "OK"),
    (["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth", "El Paso",
     "Arlington", "Corpus Christi", "Plano", "Laredo", "Lubbock", "Garland"], "TX"),
    (["Kansas City", "Saint Louis", "Springfield", "Columbia",
     "Independence", "Lee’s Summit", "O’Fallon", "Saint Joseph"], "MO"),
    (["New Orleans", "Baton Rouge", "Shreveport",
     "Lafayette", "Lake Charles", "Kenner"], "LA"),
    (["Chicago", "Aurora", "Naperville", "Joliet", "Rockford",
     "Springfield", "Peoria", "Elgin", "Waukegan", "Cicero"], "IL"),
    (["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron",
     "Dayton", "Parma", "Canton", "Youngstown"], "OH"),
    (["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Lansing",
     "Ann Arbor", "Flint", "Dearborn", "Livonia", "Westland", "Troy"], "MI"),
    (["Nashville", "Memphis", "Knoxville", "Chattanooga",
     "Clarksville", "Murfreesboro"], "TN"),
    (["Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg", "Hialeah", "Port St. Lucie", "Cape Coral", "Tallahassee", "Fort Lauderdale",
     "Pembroke Pines", "Hollywood", "Gainesville", "Miramar", "Coral Springs", "Palm Bay", "Clearwater", "Lakeland", "Pompano Beach", "West Palm Beach"], "FL"),
    (["Atlanta", "Augusta", "Columbus", "Macon", "Savannah", "Athens", "Sandy Springs", "Roswell", "Johns Creek",
     "Albany", "Warner Robins", "Alpharetta", "Marietta", "Valdosta", "Smyrna", "Dunwoody"], "GA"),
    (["Columbia", "Charleston", "North Charleston", "Mount Pleasant", "Rock Hill",
     "Greenville", "Summerville", "Sumter", "Goose Creek", "Hilton Head Island"], "SC"),
    (["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
     "Fayetteville", "Cary", "Wilmington", "High Point", "Concord"], "NC"),
    (["Virginia Beach", "Norfolk", "Chesapeake", "Richmond", "Newport News",
     "Alexandria", "Hampton", "Roanoke", "Portsmouth", "Suffolk"], "VA"),
    (["Baltimore", "Columbia", "Germantown", "Silver Spring", "Waldorf",
     "Glen Burnie", "Ellicott City", "Frederick", "Dundalk", "Rockville"], "MD"),
    (["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel",
     "Fishers", "Bloomington", "Hammond", "Gary", "Lafayette"], "IN")

]
save_interval = 50
last_page_file = "last_page.txt"
output_file = "07.05_BBBroffing.csv"

all_data = set()
entry_count = 0
page_counter = 0
pages_before_restart = 15
browser = None
context = None


def log(msg, tag="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{tag}] {timestamp} - {msg}"
    print(line)
    with open("scraper.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_existing_data():
    global all_data, entry_count
    if os.path.exists(output_file):
        with open(output_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    all_data.add(tuple(row[:5]))
        entry_count = len(all_data)
        log(f"Loaded {entry_count} existing entries", "RESUME")


def load_last_page():
    if os.path.exists(last_page_file):
        with open(last_page_file, "r") as f:
            line = f.read().strip()
            if line.isdigit():
                return int(line)
    return 1


def save_last_page(page_num):
    with open(last_page_file, "w") as f:
        f.write(str(page_num))


def save_data():
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Business Name", "Phone Number",
                        "Address", "Category", "State"])
        for row in all_data:
            writer.writerow(row)
    log(f"Saved {len(all_data)} unique records", "SAVE")


def create_browser(playwright):
    global browser, context
    user_agent = random.choice([
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",

        # 📱 Android
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",

        # 💻 MacBook (Safari)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",

        # 💻 MacBook (Chrome)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36",

        # 💻 Windows (Chrome)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

        # 💻 Windows (Edge)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"
        # 📱 Android (Samsung)
        "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",

        # 📱 iPad (Safari)
        "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",

        # 💻 Windows (Firefox)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",

        # 💻 Linux (Chrome)
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36",

        # 💻 Chromebook (Chrome OS)
        # (your list as before)
        "Mozilla/5.0 (X11; CrOS x86_64 15474.61.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.234 Safari/537.36"
    ])
    browser = playwright.chromium.launch(
        headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": random.randint(
            1100, 1400), "height": random.randint(700, 900)},
        locale='en-US',
        java_script_enabled=True,
        ignore_https_errors=True
    )
    context.set_default_timeout(30000)

    # Abort heavy or tracking requests
    def handle_route(route, request):
        if request.resource_type in ["image", "stylesheet", "font", "media", "xhr", "fetch"]:
            route.abort()
        else:
            route.continue_()

    context.route("**/*", handle_route)
    log("Optimized browser created.", "INFO")
    return context


def scrape_page(page, category, state):
    global entry_count
    try:
        names = page.eval_on_selector_all(
            "h3.result-business-name > a > span", "els => els.map(e => e.textContent.trim())")
        phones = page.eval_on_selector_all(
            "div.result-business-info a[href^='tel:']", "els => els.map(e => e.textContent.trim())")
        addresses = page.eval_on_selector_all(
            "div.result-business-info p", "els => els.map(e => e.textContent.trim())")
    except Exception as e:
        log(f"JavaScript scraping failed: {e}", "JS-ERROR")
        return

    for i in range(min(len(names), len(phones), len(addresses))):
        name, phone, address = names[i], phones[i], addresses[i]
        if name and phone and address and not any(phone == entry[1] for entry in all_data):
            all_data.add((name, phone, address, category, state))
            entry_count += 1
            log(f"{name} | {phone} | {address} | {category} | {state}", "DATA")


def handle_exit(sig, frame):
    log("Detected Ctrl+C! Saving data and closing...", "EXIT")
    save_data()
    if context:
        context.close()
    if browser:
        browser.close()
    exit(0)


def run_scraper():
    global page_counter, browser, context

    signal.signal(signal.SIGINT, handle_exit)
    load_existing_data()
    current_page_num = load_last_page()

    with sync_playwright() as playwright:
        for category in CATEGORIES:
            CATEGORY_FOR_URL = category.replace(" ", "+")
            CATEGORY_FOR_OUTPUT = category.title()
            category_output_file = f"output_{CATEGORY_FOR_URL}.csv"

            global output_file
            output_file = category_output_file
            load_existing_data()

            context = create_browser(playwright)

            try:
                for cities, state in city_url_tuples:
                    for city in cities:
                        log(f"Starting city: {city}, {state} for category: {category}", "INFO")

                        base_url = (
                            f"https://www.bbb.org/search?"
                            f"find_text={CATEGORY_FOR_URL}"
                            f"&find_entity=&find_type=&find_loc={city.replace(' ', '+')}+{state}"
                            f"&find_country=USA&page=1"
                        )

                        page_url = base_url
                        pages_scraped_for_city = 0
                        page = context.new_page()

                        while page_url:
                            try:
                                log(f"Scraping URL: {page_url}", "START")
                                page.goto(page_url, timeout=30000)

                                # Wait for the category heading (more reliable)
                                time.sleep(random.uniform(0.5, 1.0))

                                # Wait for business listings
                                try:
                                    page.wait_for_selector(
                                        "h3.result-business-name", timeout=7000)
                                except:
                                    log("Business listings didn’t load — possibly blocked or empty page.", "WARN")
                                    with open("bbb_debug_business.html", "w", encoding="utf-8") as f:
                                        f.write(page.content())
                                    page.screenshot(
                                        path="bbb_debug_business.png", full_page=True)

                                time.sleep(random.uniform(0.3, 0.7))

                                before_count = entry_count
                                scrape_page(page, CATEGORY_FOR_OUTPUT, state)
                                new_entries = entry_count - before_count

                                if new_entries == 0:
                                    log("No new data found on this page", "INFO")

                                pages_scraped_for_city += 1
                                page_counter += 1
                                current_page_num += 1
                                save_last_page(current_page_num)

                                if page_counter >= pages_before_restart:
                                    log(
                                        f"Restarting browser after {page_counter} pages", "INFO")
                                    save_data()
                                    context.close()
                                    browser.close()
                                    gc.collect()
                                    context = create_browser(playwright)
                                    page = context.new_page()
                                    page_counter = 0

                                next_btn = page.query_selector(
                                    "nav a[rel='next']")
                                if next_btn:
                                    next_href = next_btn.get_attribute("href")
                                    if next_href:
                                        page_url = next_href
                                        log(f"Next page: {page_url}", "NAV")
                                    else:
                                        break
                                else:
                                    break

                            except PlaywrightTimeoutError:
                                log(f"Timeout while scraping: {page_url}", "TIMEOUT")
                                break
                            except Exception as e:
                                log(f"Error scraping page: {e}", "ERROR")
                                time.sleep(0.5)

                        page.close()
                        log(f"Finished city: {city}", "INFO")
                        save_data()
                        gc.collect()

            except Exception as e:
                log(f"Fatal error: {e}", "FATAL")
            finally:
                save_data()
                if context:
                    context.close()
                if browser:
                    browser.close()
                log(f"Finished scraping for category: {category}",
                    "CATEGORY DONE")


if __name__ == "__main__":
    run_scraper()
