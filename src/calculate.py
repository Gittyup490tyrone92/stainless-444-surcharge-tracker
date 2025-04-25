#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Calculation module for stainless steel 444 alloy surcharge.

This module contains functions to calculate the alloy surcharge based on
raw material prices and the composition of stainless steel 444.
"""

import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

# Default composition percentages for grade 444 stainless steel
DEFAULT_COMPOSITION = {
    "chromium": 18.5,  # Using midpoint of 17.5-19.5%
    "molybdenum": 2.1,  # Using midpoint of 1.75-2.5%
    "titanium": 0.4  # Using midpoint of 0.3-0.5%
}


def calculate_surcharge(prices, composition=None):
    """
    Calculate alloy surcharge based on raw material prices and composition.
    
    Args:
        prices (dict): Dictionary with prices for 'chromium', 'molybdenum', and 'titanium' in USD/MT
        composition (dict, optional): Dictionary with composition percentages. 
                                      Defaults to DEFAULT_COMPOSITION.
    
    Returns:
        dict: Dictionary with contribution of each element and total surcharge
    """
    if composition is None:
        composition = DEFAULT_COMPOSITION
        
    contributions = {}
    
    # Calculate contribution of each element
    for element, percentage in composition.items():
        if element in prices:
            contributions[element] = (percentage * prices[element]) / 100
        else:
            raise ValueError(f"Price for {element} not provided")
    
    # Calculate total surcharge
    total_surcharge = sum(contributions.values())
    
    return {
        "contributions": contributions,
        "total_surcharge": total_surcharge
    }


def calculate_monthly_trend(data_path="../data/master_data.csv"):
    """
    Calculate monthly trends from historical data.
    
    Args:
        data_path (str, optional): Path to master data CSV. Defaults to "../data/master_data.csv".
    
    Returns:
        dict: Dictionary with trend analysis results
    """
    df = pd.read_csv(data_path)
    
    # Convert date string to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date
    df = df.sort_values('date')
    
    # Calculate month-over-month changes
    for column in ['chromium_price', 'molybdenum_price', 'titanium_price', 'total_surcharge']:
        df[f'{column}_change'] = df[column].pct_change() * 100
    
    # Calculate 3-month moving average
    df['surcharge_3m_avg'] = df['total_surcharge'].rolling(window=3).mean()
    
    # Calculate year-over-year changes if enough data is available
    if len(df) >= 12:
        df['surcharge_yoy_change'] = df['total_surcharge'].pct_change(periods=12) * 100
    
    # Get latest month's data
    latest = df.iloc[-1].to_dict()
    
    # Get average surcharge
    avg_surcharge = df['total_surcharge'].mean()
    
    # Calculate contribution percentages
    contribution_cols = ['chromium_contribution', 'molybdenum_contribution', 'titanium_contribution']
    total_contributions = df[contribution_cols].sum().sum()
    contribution_pcts = (df[contribution_cols].sum() / total_contributions * 100).to_dict()
    
    return {
        "latest_month": latest,
        "avg_surcharge": avg_surcharge,
        "contribution_percentages": contribution_pcts,
        "trend_data": df.to_dict(orient='records')
    }


def update_master_data(new_data, master_path="../data/master_data.csv"):
    """
    Update master data file with new data for the current month.
    
    Args:
        new_data (dict): Dictionary with new data for the current month
        master_path (str, optional): Path to master data CSV. Defaults to "../data/master_data.csv".
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read existing data
        df = pd.read_csv(master_path)
        
        # Create new row
        new_row = {
            'date': new_data['date'],
            'chromium_price': new_data['raw_prices']['chromium'],
            'molybdenum_price': new_data['raw_prices']['molybdenum'],
            'titanium_price': new_data['raw_prices']['titanium'],
            'chromium_contribution': new_data['contributions']['chromium'],
            'molybdenum_contribution': new_data['contributions']['molybdenum'],
            'titanium_contribution': new_data['contributions']['titanium'],
            'total_surcharge': new_data['total_surcharge']
        }
        
        # Append new row
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Save updated data
        df.to_csv(master_path, index=False)
        
        # Also save to historical directory
        date = datetime.strptime(new_data['date'], "%Y-%m-%d")
        year_dir = os.path.join(os.path.dirname(master_path), 'historical', str(date.year))
        os.makedirs(year_dir, exist_ok=True)
        
        with open(os.path.join(year_dir, f"{date.strftime('%Y-%m')}.json"), 'w') as f:
            json.dump(new_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error updating master data: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    prices = {
        "chromium": 12800,
        "molybdenum": 36500,
        "titanium": 7050
    }
    
    result = calculate_surcharge(prices)
    print(f"Calculated surcharge: ${result['total_surcharge']:.2f}")
    print("Contributions:")
    for element, contribution in result['contributions'].items():
        print(f"  {element}: ${contribution:.2f}")
