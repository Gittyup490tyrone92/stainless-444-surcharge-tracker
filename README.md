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
- Advanced data validation with anomaly detection and cross-validation
- Price forecasting using time series analysis (ARIMA, Exponential Smoothing)
- Rich email templating with embedded charts and interactive elements
- Visualization of price trends and surcharge components
- Interactive dashboards with historical data and forecasts
- Historical data tracking and comparison
- Monthly report generation with forecast projections
- CSV export for further analysis
- Email notifications with embedded charts and analysis

## Getting Started

1. Clone this repository
2. Install the required dependencies with `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your settings
4. Run the data collection script: `python src/collect_data.py`
5. Generate visualizations: `python src/visualize.py`
6. Generate price forecasts: `python src/price_forecasting.py`
7. Generate a monthly report: `python src/generate_report.py`

Alternatively, run the all-in-one script: `python src/monthly_update.py`

## Data Validation

The system includes robust data validation capabilities:

- **Range Validation**: Ensures prices fall within expected historical ranges
- **Anomaly Detection**: Uses statistical methods (Z-score) to identify outliers
- **Cross-Validation**: Compares prices from multiple sources for consistency
- **Trend Analysis**: Verifies that month-over-month changes are within reasonable limits
- **Validation Logging**: Detailed logs of all validation checks for auditability

Configure validation behavior in your `.env` file:
```
ENABLE_VALIDATION=True          # Enable/disable validation
BYPASS_VALIDATION=False         # Skip validation failures but log them
HALT_ON_VALIDATION_FAILURE=False  # Stop processing if validation fails
```

## Price Forecasting

The system can generate price forecasts for raw materials and alloy surcharges:

- **Multiple Models**: Uses both ARIMA and Exponential Smoothing methods
- **Model Selection**: Automatically selects the best performing model
- **Confidence Intervals**: Provides upper and lower bounds for forecasts
- **Visualization**: Generates charts showing forecast trends with confidence bands
- **Performance Metrics**: Calculates accuracy metrics (MAE, RMSE) for model evaluation
- **Seasonal Detection**: Identifies and accounts for seasonal patterns in price data

Configure forecasting behavior in your `.env` file:
```
ENABLE_FORECASTING=True  # Enable/disable forecasting feature
```

## Enhanced Email Templating

The system features a sophisticated email templating system with rich visual elements:

- **Multiple Template Options**: Choose between basic, enhanced, or modular templates
- **Embedded Charts**: Inline charts and sparklines integrated directly in emails
- **Conditional Content**: Content sections that appear only when relevant
- **Interactive Elements**: Expandable sections for detailed information
- **Mobile Responsive**: Templates adapt to different screen sizes
- **Component-Based Design**: Reusable components for easy customization

Configure email templates in your `.env` file:
```
EMAIL_USE_ENHANCED_TEMPLATE=True
EMAIL_TEMPLATE=modular_email_template.html
```

Available templates:
- `email_template.html` - Basic template
- `enhanced_email_template.html` - Rich visual template
- `modular_email_template.html` - Component-based modular template

For detailed information about customizing email templates, see [templates/README.md](templates/README.md).

## Project Structure

```
├── data/
│   ├── historical/          # Historical data by year
│   │   ├── 2024/
│   │   └── 2025/
│   ├── forecasts/           # Price forecast data and charts
│   ├── current_month.json   # Current month's data
│   └── master_data.csv      # Complete historical dataset
├── logs/                    # Log files directory
│   ├── monthly_update_*.log # Update process logs
│   └── price_validation_*.json # Validation result logs
├── reports/                 # Generated monthly reports
├── src/
│   ├── collect_data.py      # Data collection script
│   ├── visualize.py         # Visualization generator
│   ├── calculate.py         # Surcharge calculation logic
│   ├── data_validation.py   # Data validation module
│   ├── price_forecasting.py # Price forecasting module
│   ├── email_service.py     # Enhanced email service
│   ├── generate_report.py   # Report generation script
│   ├── monthly_update.py    # All-in-one update script
│   └── __init__.py          # Package initialization
├── templates/               # Report and email templates
│   ├── monthly_report_template.html
│   ├── email_template.html
│   ├── enhanced_email_template.html
│   ├── modular_email_template.html
│   └── components/          # Reusable template components
├── .env.example            # Environment variables example
├── requirements.txt         # Project dependencies
├── setup.py                # Package installation script
├── LICENSE                 # MIT License
└── README.md               # Project documentation
```

## Data Sources

This project collects data from multiple industry sources:
- Metal price indices
- Industry publications
- Market reports

For cross-validation, the system can be configured to pull data from multiple sources and compare them for consistency.

## Automation

The system is designed to be run automatically on a monthly schedule:

### Using Cron (Linux/macOS)

Add to your crontab:
```bash
# Run on the 1st of each month at 7:00 AM
0 7 1 * * cd /path/to/stainless-444-surcharge-tracker && python src/monthly_update.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a new task to run monthly
3. Set the action to run:
   - Program: `python`
   - Arguments: `src/monthly_update.py`
   - Start in: `C:\path\to\stainless-444-surcharge-tracker`

## API Integration

To connect to real data sources:

1. Obtain API keys from your preferred metal price data providers
2. Add the keys to your `.env` file
3. Modify the `fetch_metal_prices()` function in `src/collect_data.py` to make the appropriate API calls

## License

MIT
