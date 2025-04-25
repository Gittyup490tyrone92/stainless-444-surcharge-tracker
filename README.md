# Stainless Steel 444 Alloy Surcharge Tracker

This project provides tools to track and visualize monthly price trends for the key alloying elements in stainless steel grade 444, and calculates the resulting alloy surcharge.

## About Stainless Steel 444

Grade 444 stainless steel is a ferritic stainless steel with the following typical composition:
- Chromium: 17.5-19.5% (using 18.5% for calculations)
- Molybdenum: 1.75-2.5% (using 2.1% for calculations)
- Titanium: 0.3-0.5% (using 0.4% for calculations)

This composition makes 444 more resistant to stress corrosion cracking than austenitic grades while providing good formability and weldability. The alloy surcharge is generally lower than for nickel-containing austenitic grades (like 304 or 316) since it avoids the significant cost volatility associated with nickel.

## Features

- Monthly data collection for raw material prices (chromium, molybdenum, titanium)
- Automated alloy surcharge calculation
- Visualization of price trends and surcharge components
- Historical data tracking and comparison
- Monthly report generation
- CSV export for further analysis

## Getting Started

1. Clone this repository
2. Install the required dependencies with `pip install -r requirements.txt`
3. Run the data collection script: `python src/collect_data.py`
4. Generate visualizations: `python src/visualize.py`
5. Generate a monthly report: `python src/generate_report.py`

Alternatively, run the all-in-one script: `python src/monthly_update.py`

## Project Structure

```
├── data/
│   ├── historical/          # Historical data by year
│   │   ├── 2024/
│   │   └── 2025/
│   ├── current_month.json   # Current month's data
│   └── master_data.csv      # Complete historical dataset
├── reports/                 # Generated monthly reports
├── src/
│   ├── collect_data.py      # Data collection script
│   ├── visualize.py         # Visualization generator
│   ├── calculate.py         # Surcharge calculation logic
│   ├── generate_report.py   # Report generation script
│   └── monthly_update.py    # All-in-one update script
├── templates/               # Report templates
├── .env.example            # Environment variables example
├── requirements.txt         # Project dependencies
└── README.md               # Project documentation
```

## Data Sources

This project collects data from multiple industry sources:
- Metal price indices
- Industry publications
- Market reports

## License

MIT
