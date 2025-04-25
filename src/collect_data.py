#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data collection module for stainless steel 444 alloy surcharge tracking.

This script collects current prices for the raw materials used in stainless steel 444
(chromium, molybdenum, titanium) from various sources and saves them to a JSON file.

It can be run manually or scheduled as a monthly task.
"""

import json
import os
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Import local modules
from calculate import calculate_surcharge, update_master_data
from data_validation import validate_prices
from price_forecasting import generate_forecast, generate_forecast_chart

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
CURRENT_MONTH_FILE = os.path.join(DATA_DIR, 'current_month.json')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Metal price API key
API_KEY = os.getenv('METAL_PRICE_API_KEY')

# Flag to enable/disable data validation
ENABLE_VALIDATION = os.getenv('ENABLE_VALIDATION', 'True').lower() in ('true', 'yes', '1')

# Flag to enable/disable price forecasting
ENABLE_FORECASTING = os.getenv('ENABLE_FORECASTING', 'True').lower() in ('true', 'yes', '1')

# Flag to bypass validation in case of anomalies (not recommended for production)
BYPASS_VALIDATION = os.getenv('BYPASS_VALIDATION', 'False').lower() in ('true', 'yes', '1')


def fetch_metal_prices():
    """
    Fetch current prices for chromium, molybdenum, and titanium.
    
    In a real implementation, this would connect to actual data sources.
    For this example, we'll simulate the data collection process.
    
    Returns:
        dict: Dictionary with prices for each metal in USD/MT
    """
    try:
        # TODO: Replace with actual API calls in production
        
        # This is a simulation - in a real implementation, you would use API calls
        # to metal price data providers, or web scraping from reliable sources
        
        # Example API call (commented out):
        # response = requests.get(
        #     "https://api.example.com/metal-prices",
        #     headers={"Authorization": f"Bearer {API_KEY}"},
        #     params={"metals": "chromium,molybdenum,titanium"}
        # )
        # data = response.json()
        
        # For demonstration purposes, we'll return simulated prices
        # In a real implementation, these values would come from the API response
        
        # Simulate monthly variations with slight increases
        # In a real-world scenario, these would be actual market prices
        prices = {
            "chromium": 12800,  # USD per metric ton
            "molybdenum": 36500,  # USD per metric ton
            "titanium": 7050  # USD per metric ton
        }
        
        # In production, implement a fallback mechanism
        # If primary source fails, try secondary sources
        # Example (commented out):
        # try:
        #     prices = fetch_from_primary_source()
        # except Exception:
        #     logger.warning("Primary source failed, trying secondary source")
        #     prices = fetch_from_secondary_source()
        
        logger.info(f"Fetched metal prices: {prices}")
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching metal prices: {e}")
        raise


def fetch_secondary_prices():
    """
    Fetch prices from a secondary source for validation.
    
    In a real implementation, this would connect to a different data source
    than the primary one to enable cross-validation.
    
    Returns:
        dict: Dictionary with prices from secondary source
    """
    try:
        # This is a simulation - in a real implementation, this would be a different source
        # than the primary one used in fetch_metal_prices()
        
        # For demonstration purposes, we'll return slightly different simulated prices
        secondary_prices = {
            "chromium": 12750,  # USD per metric ton
            "molybdenum": 36700,  # USD per metric ton
            "titanium": 7000  # USD per metric ton
        }
        
        logger.info(f"Fetched secondary prices for validation: {secondary_prices}")
        return secondary_prices
        
    except Exception as e:
        logger.error(f"Error fetching secondary prices: {e}")
        return None


def collect_and_save_data():
    """
    Collect metal prices, validate data, calculate surcharge, generate forecasts, and save to file.
    
    Returns:
        dict: The collected and calculated data
    """
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'historical'), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'forecasts'), exist_ok=True)
    
    # Get current date (first day of current month for consistency)
    today = datetime.now()
    first_of_month = today.replace(day=1).strftime("%Y-%m-%d")
    
    # Fetch metal prices
    prices = fetch_metal_prices()
    
    # Validate data if enabled
    if ENABLE_VALIDATION:
        logger.info("Validating price data...")
        secondary_prices = fetch_secondary_prices()
        is_valid, issues = validate_prices(prices, secondary_prices)
        
        if not is_valid and not BYPASS_VALIDATION:
            error_msg = f"Data validation failed: {', '.join(issues)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        elif not is_valid and BYPASS_VALIDATION:
            logger.warning(f"Data validation failed but bypassed: {', '.join(issues)}")
    
    # Calculate surcharge
    calculation = calculate_surcharge(prices)
    
    # Load previous month's data to calculate change
    previous_surcharge = None
    try:
        if os.path.exists(CURRENT_MONTH_FILE):
            with open(CURRENT_MONTH_FILE, 'r') as f:
                previous_data = json.load(f)
                previous_surcharge = previous_data.get('total_surcharge')
    except Exception as e:
        logger.error(f"Error reading previous data: {e}")
    
    # Calculate change from previous month
    change_pct = None
    if previous_surcharge:
        change_pct = ((calculation['total_surcharge'] - previous_surcharge) / previous_surcharge) * 100
    
    # Prepare data structure
    data = {
        "date": first_of_month,
        "raw_prices": prices,
        "composition": {
            "chromium": 18.5,
            "molybdenum": 2.1,
            "titanium": 0.4
        },
        "contributions": calculation['contributions'],
        "total_surcharge": calculation['total_surcharge'],
        "change_from_previous": change_pct,
        "data_sources": [
            "Metal Exchange Index",
            "Commodity Price Report",
            "Industry Analysis Weekly"
        ],
        "notes": "Monthly data collection",
        "validation": {
            "validated": ENABLE_VALIDATION,
            "is_valid": True if not ENABLE_VALIDATION else is_valid,
            "issues": [] if not ENABLE_VALIDATION else issues
        }
    }
    
    # Save to current month file
    with open(CURRENT_MONTH_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Update master data file
    update_master_data(data, MASTER_DATA_FILE)
    
    # Generate price forecasts if enabled
    if ENABLE_FORECASTING:
        logger.info("Generating price forecasts...")
        try:
            forecast_data = generate_forecast()
            if forecast_data:
                # Generate forecast charts
                chart_paths = generate_forecast_chart(forecast_data)
                logger.info(f"Forecast charts generated: {', '.join(chart_paths.keys())}")
                
                # Add forecast info to data
                data["forecast_available"] = True
                data["forecast_charts"] = chart_paths
            else:
                logger.warning("Failed to generate price forecasts")
                data["forecast_available"] = False
        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            data["forecast_available"] = False
    
    logger.info(f"Data collected and saved for {first_of_month}")
    logger.info(f"Total surcharge: ${data['total_surcharge']:.2f}")
    if change_pct is not None:
        logger.info(f"Change from previous month: {change_pct:.2f}%")
    
    return data


if __name__ == "__main__":
    # Configure logging for command line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        data = collect_and_save_data()
        print(f"Data collected and saved for {data['date']}")
        print(f"Total surcharge: ${data['total_surcharge']:.2f}")
        if data.get('change_from_previous') is not None:
            print(f"Change from previous month: {data['change_from_previous']:.2f}%")
        
        if ENABLE_VALIDATION:
            validation = data.get('validation', {})
            if validation.get('is_valid', False):
                print("Data validation: PASSED")
            else:
                print(f"Data validation: FAILED - {', '.join(validation.get('issues', []))}")
        
        if ENABLE_FORECASTING and data.get('forecast_available', False):
            print(f"Forecasts generated successfully!")
            for chart_name, chart_path in data.get('forecast_charts', {}).items():
                print(f"- {chart_name}: {chart_path}")
        
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        print(f"Error: {e}")
        exit(1)
