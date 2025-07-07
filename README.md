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
# 📁 Output
CSV files like output_Locksmith.csv or output_Car+Wash.csv containing:

Business Name	Phone Number	Address	Category	State

🚨 Legality Notice
This tool is intended for educational and personal research purposes only.

⚖️ Legal Disclaimer:
Scraping publicly available websites like BBB.org may violate their terms of service. Always review the website's Terms of Use before using this tool. The author assumes no liability for any misuse or damages caused by running this script.

🧠 Credits
Built using Playwright Python

Data source: bbb.org
