#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monthly update script for stainless steel 444 alloy surcharge tracking.

This script is intended to be run once a month (e.g., via a cron job)
to collect the latest data, update the database, generate visualizations,
and create monthly reports.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import project modules
from collect_data import collect_and_save_data
from visualize import generate_all_visualizations
from generate_report import generate_all_reports
from data_validation import validate_prices
from price_forecasting import generate_forecast, generate_forecast_chart
from calculate import calculate_monthly_trend
from email_service import send_notification_email

# Load environment variables
load_dotenv()

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'monthly_update_{datetime.now().strftime("%Y-%m")}.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('monthly_update')

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
CURRENT_MONTH_FILE = os.path.join(DATA_DIR, 'current_month.json')
FORECAST_DIR = os.path.join(DATA_DIR, 'forecasts')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Flag to enable/disable data validation (read from .env)
ENABLE_VALIDATION = os.getenv('ENABLE_VALIDATION', 'True').lower() in ('true', 'yes', '1')

# Flag to enable/disable price forecasting (read from .env)
ENABLE_FORECASTING = os.getenv('ENABLE_FORECASTING', 'True').lower() in ('true', 'yes', '1')

# Flag to halt process on validation failure (read from .env)
HALT_ON_VALIDATION_FAILURE = os.getenv('HALT_ON_VALIDATION_FAILURE', 'False').lower() in ('true', 'yes', '1')


def run_data_validation(prices):
    """
    Run data validation on the collected prices.
    
    Args:
        prices (dict): Dictionary with prices for 'chromium', 'molybdenum', and 'titanium'
    
    Returns:
        tuple: (is_valid, validation_result) - Boolean indicating if data is valid and validation details
    """
    if not ENABLE_VALIDATION:
        logger.info("Data validation is disabled")
        return True, {'enabled': False, 'message': 'Data validation is disabled'}
    
    try:
        logger.info("Validating price data...")
        
        # Fetch secondary prices for cross-validation
        secondary_prices = None
        try:
            # This would be implemented to fetch from a secondary source
            # For now, we'll simulate with slightly different values
            secondary_prices = {
                "chromium": prices["chromium"] * 0.98,  # 2% lower
                "molybdenum": prices["molybdenum"] * 1.02,  # 2% higher
                "titanium": prices["titanium"] * 0.99  # 1% lower
            }
        except Exception as e:
            logger.warning(f"Failed to fetch secondary prices for validation: {e}")
        
        # Run validation
        is_valid, issues = validate_prices(prices, secondary_prices)
        
        validation_result = {
            'enabled': True,
            'is_valid': is_valid,
            'issues': issues,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if is_valid:
            logger.info("Data validation passed successfully")
        else:
            logger.warning(f"Data validation failed: {', '.join(issues)}")
            
            if HALT_ON_VALIDATION_FAILURE:
                logger.error("Process halted due to validation failure")
                raise ValueError(f"Data validation failed: {', '.join(issues)}")
        
        return is_valid, validation_result
        
    except Exception as e:
        logger.error(f"Error during data validation: {e}")
        return False, {'enabled': True, 'is_valid': False, 'message': str(e)}


def run_price_forecasting(data):
    """
    Generate price forecasts if enabled.
    
    Args:
        data (dict): The collected data
    
    Returns:
        tuple: (forecast_available, forecast_data, forecast_charts)
    """
    if not ENABLE_FORECASTING:
        logger.info("Price forecasting is disabled")
        return False, None, None
    
    try:
        logger.info("Generating price forecasts...")
        
        # Generate forecasts
        forecast_data = generate_forecast()
        
        if forecast_data:
            # Generate forecast charts
            forecast_charts = generate_forecast_chart(forecast_data)
            logger.info(f"Price forecasts and charts generated successfully")
            return True, forecast_data, forecast_charts
        else:
            logger.warning("Failed to generate price forecasts")
            return False, None, None
            
    except Exception as e:
        logger.error(f"Error during price forecasting: {e}")
        return False, None, None


def run_monthly_update():
    """
    Run the complete monthly update process.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting monthly update process")
        
        # Step 1: Collect latest data
        logger.info("Step 1: Collecting latest data")
        data = collect_and_save_data()
        logger.info(f"Collected data for {data['date']} - Surcharge: ${data['total_surcharge']:.2f}")
        
        # Step 2: Validate data
        is_valid, validation_result = run_data_validation(data['raw_prices'])
        
        # Step 3: Generate visualizations
        logger.info("Step 3: Generating visualizations")
        viz_paths = generate_all_visualizations()
        logger.info(f"Generated {len(viz_paths)} visualizations")
        
        # Step 4: Generate forecasts
        logger.info("Step 4: Generating forecasts")
        forecast_available, forecast_data, forecast_charts = run_price_forecasting(data)
        
        # Step 5: Calculate trend analysis
        logger.info("Step 5: Calculating trend analysis")
        trend_analysis = calculate_monthly_trend(MASTER_DATA_FILE)
        
        # Step 6: Generate reports
        logger.info("Step 6: Generating reports")
        report_paths = generate_all_reports()
        logger.info(f"Generated {len(report_paths)} reports")
        
        # Step 7: Send notification with enhanced email service
        logger.info("Step 7: Sending enhanced email notification")
        email_sent = send_notification_email(
            report_paths,
            data,
            trend_analysis,
            viz_paths,
            validation_result,
            forecast_available,
            forecast_data,
            forecast_charts
        )
        
        if email_sent:
            logger.info("Email notification sent successfully")
        else:
            logger.warning("Failed to send email notification")
        
        # Step 8: Save monthly update summary
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": data['date'],
            "surcharge": data['total_surcharge'],
            "validation": validation_result,
            "forecast_available": forecast_available,
            "reports_generated": list(report_paths.keys()),
            "visualizations_generated": list(viz_paths.keys()),
            "forecast_charts": list(forecast_charts.keys()) if forecast_charts else [],
            "email_sent": email_sent
        }
        
        summary_file = os.path.join(log_dir, f"update_summary_{datetime.now().strftime('%Y-%m')}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Monthly update summary saved to {summary_file}")
        logger.info("Monthly update process completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Monthly update process failed: {e}")
        return False


if __name__ == "__main__":
    successful = run_monthly_update()
    sys.exit(0 if successful else 1)
