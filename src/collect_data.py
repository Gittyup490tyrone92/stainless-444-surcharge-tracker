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
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Import the calculation module
from calculate import calculate_surcharge, update_master_data

# Load environment variables
load_dotenv()

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
CURRENT_MONTH_FILE = os.path.join(DATA_DIR, 'current_month.json')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Metal price API key
API_KEY = os.getenv('METAL_PRICE_API_KEY')


def fetch_metal_prices():
    """
    Fetch current prices for chromium, molybdenum, and titanium.
    
    In a real implementation, this would connect to actual data sources.
    For this example, we'll simulate the data collection process.
    
    Returns:
        dict: Dictionary with prices for each metal in USD/MT
    """
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
    
    return prices


def collect_and_save_data():
    """
    Collect metal prices, calculate surcharge, and save to file.
    
    Returns:
        dict: The collected and calculated data
    """
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'historical'), exist_ok=True)
    
    # Get current date (first day of current month for consistency)
    today = datetime.now()
    first_of_month = today.replace(day=1).strftime("%Y-%m-%d")
    
    # Fetch metal prices
    prices = fetch_metal_prices()
    
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
        print(f"Error reading previous data: {e}")
    
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
        "notes": "Monthly data collection"
    }
    
    # Save to current month file
    with open(CURRENT_MONTH_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Update master data file
    update_master_data(data, MASTER_DATA_FILE)
    
    print(f"Data collected and saved for {first_of_month}")
    print(f"Total surcharge: ${data['total_surcharge']:.2f}")
    if change_pct is not None:
        print(f"Change from previous month: {change_pct:.2f}%")
    
    return data


if __name__ == "__main__":
    collect_and_save_data()
