# BBB Business Scraper

This Python script uses Playwright to scrape business data from [BBB.org](https://www.bbb.org/) across multiple US cities and categories.

## 🚀 Features

- Scrapes business name, phone number, address, category, and state
- Supports multiple business categories
- Covers major cities across over 15 US states
- Optimized Playwright browser settings (stealth, lightweight)
- Saves data in category-specific CSV files
- Auto-resumes from last page on crash or manual stop
- Logs all events to `scraper.log`

## ⚙️ Requirements

- Python 3.8+
- Playwright
- Install dependencies:

```bash
pip install -r requirements.txt
playwright install
