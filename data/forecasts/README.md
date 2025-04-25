# Forecasts Directory

This directory contains price forecasts for raw materials used in stainless steel 444 and calculated alloy surcharges.

## Contents

- JSON files containing forecast data with the following format:
  - Raw material price forecasts (chromium, molybdenum, titanium)
  - Alloy surcharge forecasts
  - Confidence intervals
  - Model parameters and evaluation metrics

- Visualization charts including:
  - Price trend forecasts for each raw material
  - Alloy surcharge forecasts with confidence intervals
  - Comparison between historical data and forecasts

## File Naming Convention

Files are named using the following convention:
- `forecast_YYYY-MM.json` - Forecast data files
- `{material}_forecast_YYYY-MM-DD.png` - Material-specific forecast charts
- `surcharge_forecast_YYYY-MM-DD.png` - Surcharge forecast charts

## Forecast Models

The forecasts are generated using time series forecasting techniques:
1. ARIMA (AutoRegressive Integrated Moving Average)
2. Exponential Smoothing

The system automatically selects the model with better accuracy based on historical performance evaluated using Mean Absolute Error (MAE) metric.

## Forecast Periods

By default, the system generates 6-month forecasts with 95% confidence intervals. These parameters can be adjusted in the price_forecasting.py module.
