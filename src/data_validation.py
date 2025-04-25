#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data validation module for stainless steel 444 alloy surcharge tracking.

This module contains functions to validate raw material prices and detect anomalies
in the data before it is used for calculations and reporting.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from scipy import stats
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Anomaly thresholds
ZSCORE_THRESHOLD = 3.0  # Number of standard deviations for Z-score outlier detection
MAX_MONTHLY_PCT_CHANGE = 25.0  # Maximum allowed month-over-month percentage change
MIN_MONTHLY_PCT_CHANGE = -25.0  # Minimum allowed month-over-month percentage change


def validate_price_range(prices):
    """
    Validate that raw material prices are within reasonable ranges.
    
    Args:
        prices (dict): Dictionary with prices for 'chromium', 'molybdenum', and 'titanium'
    
    Returns:
        tuple: (is_valid, issues) where is_valid is a boolean and issues is a list of validation issues
    """
    issues = []
    
    # Define reasonable price ranges for each material (USD/MT)
    price_ranges = {
        'chromium': (8000, 20000),  # Min, Max expected price
        'molybdenum': (20000, 60000),
        'titanium': (5000, 10000)
    }
    
    # Check each price
    for material, (min_price, max_price) in price_ranges.items():
        if material in prices:
            price = prices[material]
            if price < min_price:
                issues.append(f"{material.capitalize()} price (${price}) is below expected minimum (${min_price})")
            elif price > max_price:
                issues.append(f"{material.capitalize()} price (${price}) is above expected maximum (${max_price})")
        else:
            issues.append(f"Missing price for {material}")
    
    return len(issues) == 0, issues


def detect_price_anomalies(new_prices):
    """
    Detect anomalies in new prices compared to historical data.
    
    Args:
        new_prices (dict): Dictionary with new prices for 'chromium', 'molybdenum', and 'titanium'
    
    Returns:
        tuple: (has_anomalies, anomalies) where has_anomalies is a boolean and anomalies is a list of detected anomalies
    """
    anomalies = []
    
    try:
        # Load historical data
        df = pd.read_csv(MASTER_DATA_FILE)
        if len(df) < 3:  # Need at least 3 data points for meaningful anomaly detection
            logger.warning("Not enough historical data for anomaly detection")
            return False, []
        
        # Check for each material
        for material in ['chromium', 'molybdenum', 'titanium']:
            column = f"{material}_price"
            
            # Get historical values
            hist_values = df[column].values
            
            # Z-score anomaly detection
            mean = np.mean(hist_values)
            std = np.std(hist_values)
            
            if std > 0:  # Avoid division by zero
                z_score = (new_prices[material] - mean) / std
                if abs(z_score) > ZSCORE_THRESHOLD:
                    anomalies.append(
                        f"{material.capitalize()} price (${new_prices[material]}) has a Z-score of {z_score:.2f}, "
                        f"which is outside the normal range (±{ZSCORE_THRESHOLD} std dev from mean ${mean:.2f})"
                    )
            
            # Month-over-month change check
            if len(hist_values) > 0:
                last_price = hist_values[-1]
                pct_change = ((new_prices[material] - last_price) / last_price) * 100
                
                if pct_change > MAX_MONTHLY_PCT_CHANGE:
                    anomalies.append(
                        f"{material.capitalize()} price increased by {pct_change:.2f}%, "
                        f"which exceeds the maximum expected change of {MAX_MONTHLY_PCT_CHANGE}%"
                    )
                elif pct_change < MIN_MONTHLY_PCT_CHANGE:
                    anomalies.append(
                        f"{material.capitalize()} price decreased by {abs(pct_change):.2f}%, "
                        f"which exceeds the maximum expected change of {abs(MIN_MONTHLY_PCT_CHANGE)}%"
                    )
    
    except Exception as e:
        logger.error(f"Error during anomaly detection: {e}")
        return False, [f"Error during anomaly detection: {e}"]
    
    return len(anomalies) > 0, anomalies


def cross_validate_prices(prices, secondary_prices=None):
    """
    Cross-validate prices against a secondary source if available.
    
    Args:
        prices (dict): Primary prices for 'chromium', 'molybdenum', and 'titanium'
        secondary_prices (dict, optional): Secondary source prices for validation
    
    Returns:
        tuple: (is_valid, issues) where is_valid is a boolean and issues is a list of validation issues
    """
    issues = []
    
    # If no secondary prices are provided, return valid
    if secondary_prices is None:
        return True, []
    
    # Maximum allowed percentage difference between primary and secondary sources
    MAX_DIFF_PCT = 10.0
    
    # Check each material
    for material in ['chromium', 'molybdenum', 'titanium']:
        if material in prices and material in secondary_prices:
            primary = prices[material]
            secondary = secondary_prices[material]
            
            # Calculate percentage difference
            diff_pct = abs((primary - secondary) / secondary) * 100
            
            if diff_pct > MAX_DIFF_PCT:
                issues.append(
                    f"{material.capitalize()} price (${primary}) differs by {diff_pct:.2f}% "
                    f"from secondary source (${secondary}), which exceeds the maximum allowed difference of {MAX_DIFF_PCT}%"
                )
    
    return len(issues) == 0, issues


def log_validation_result(prices, is_valid, issues):
    """
    Log validation results and save to validation log file.
    
    Args:
        prices (dict): Prices that were validated
        is_valid (bool): Whether the prices are valid
        issues (list): List of validation issues
    
    Returns:
        bool: True if logging was successful, False otherwise
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create validation log file path
        log_file = os.path.join(log_dir, f'price_validation_{datetime.now().strftime("%Y-%m")}.json')
        
        # Prepare log entry
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prices": prices,
            "is_valid": is_valid,
            "issues": issues
        }
        
        # Append to existing log if it exists
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        # Save updated logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        # Log to console/file based on logging configuration
        if is_valid:
            logger.info(f"Price validation successful for {datetime.now().strftime('%Y-%m')}")
        else:
            logger.warning(f"Price validation issues detected: {', '.join(issues)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error logging validation result: {e}")
        return False


def validate_prices(prices, secondary_prices=None):
    """
    Perform all validation checks on the provided prices.
    
    Args:
        prices (dict): Prices for 'chromium', 'molybdenum', and 'titanium'
        secondary_prices (dict, optional): Secondary source prices for validation
    
    Returns:
        tuple: (is_valid, issues) where is_valid is a boolean and issues is a list of all validation issues
    """
    all_issues = []
    
    # Check price ranges
    range_valid, range_issues = validate_price_range(prices)
    all_issues.extend(range_issues)
    
    # Detect anomalies
    has_anomalies, anomalies = detect_price_anomalies(prices)
    all_issues.extend(anomalies)
    
    # Cross-validate if secondary source is available
    if secondary_prices:
        cross_valid, cross_issues = cross_validate_prices(prices, secondary_prices)
        all_issues.extend(cross_issues)
    
    # Log validation results
    is_valid = len(all_issues) == 0
    log_validation_result(prices, is_valid, all_issues)
    
    return is_valid, all_issues


if __name__ == "__main__":
    # Example usage
    test_prices = {
        "chromium": 12800,
        "molybdenum": 36500,
        "titanium": 7050
    }
    
    is_valid, issues = validate_prices(test_prices)
    
    if is_valid:
        print("Prices validated successfully!")
    else:
        print("Validation issues detected:")
        for issue in issues:
            print(f"- {issue}")
