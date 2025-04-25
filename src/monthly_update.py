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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from jinja2 import Environment, FileSystemLoader

# Import project modules
from collect_data import collect_and_save_data
from visualize import generate_all_visualizations
from generate_report import generate_all_reports
from data_validation import validate_prices
from price_forecasting import generate_forecast, generate_forecast_chart

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

# Flag to enable/disable data validation (read from .env)
ENABLE_VALIDATION = os.getenv('ENABLE_VALIDATION', 'True').lower() in ('true', 'yes', '1')

# Flag to enable/disable price forecasting (read from .env)
ENABLE_FORECASTING = os.getenv('ENABLE_FORECASTING', 'True').lower() in ('true', 'yes', '1')

# Flag to halt process on validation failure (read from .env)
HALT_ON_VALIDATION_FAILURE = os.getenv('HALT_ON_VALIDATION_FAILURE', 'False').lower() in ('true', 'yes', '1')


def send_notification_email(report_paths, data, forecast_available=False, forecast_charts=None, validation_result=None):
    """
    Send a notification email with the generated reports.
    
    Args:
        report_paths (dict): Dictionary with paths to generated reports
        data (dict): The collected data
        forecast_available (bool): Whether forecast data is available
        forecast_charts (dict): Dictionary with paths to forecast charts
        validation_result (dict): Data validation results
    
    Returns:
        bool: True if successful, False otherwise
    """
    notify_email = os.getenv('NOTIFY_EMAIL')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    # Skip if email settings are not configured
    if not all([notify_email, smtp_server, smtp_username, smtp_password]):
        logger.warning("Email notification skipped - missing configuration")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_username
        msg['To'] = notify_email
        msg['Subject'] = f"Stainless Steel 444 Alloy Surcharge Report - {datetime.now().strftime('%B %Y')}"
        
        # Generate HTML email content using template
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template('email_template.html')
        
        # Prepare data for template
        report_month = datetime.strptime(data['date'], "%Y-%m-%d").strftime("%B %Y")
        forecast_info = None
        if forecast_available and forecast_charts:
            forecast_info = {
                'available': True,
                'charts': forecast_charts
            }
        
        # Build context for template
        context = {
            'report_month': report_month,
            'current_month': data,
            'forecast': forecast_info,
            'validation': validation_result,
            'dashboard_link': f"file://{os.path.abspath(report_paths.get('monthly_report', ''))}"
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Attach plain text and HTML versions
        msg.attach(MIMEText("""Monthly stainless steel 444 alloy surcharge report is attached.

This automated email contains the monthly report with detailed analysis and visualizations.
Please review the attached files for the latest pricing information and trends.
""", 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Attach reports
        for name, path in report_paths.items():
            with open(path, 'rb') as file:
                attachment = MIMEApplication(file.read(), Name=os.path.basename(path))
                attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                msg.attach(attachment)
        
        # Attach forecast charts if available
        if forecast_available and forecast_charts:
            for name, path in forecast_charts.items():
                if os.path.exists(path):
                    with open(path, 'rb') as file:
                        attachment = MIMEApplication(file.read(), Name=os.path.basename(path))
                        attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                        msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Notification email sent to {notify_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False


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
        forecast_available, forecast_data, forecast_charts = run_price_forecasting(data)
        
        # Step 5: Generate reports
        logger.info("Step 5: Generating reports")
        report_paths = generate_all_reports()
        logger.info(f"Generated {len(report_paths)} reports")
        
        # Step 6: Send notification
        logger.info("Step 6: Sending notification")
        send_notification_email(
            report_paths, 
            data, 
            forecast_available=forecast_available, 
            forecast_charts=forecast_charts,
            validation_result=validation_result
        )
        
        # Step 7: Save monthly update summary
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": data['date'],
            "surcharge": data['total_surcharge'],
            "validation": validation_result,
            "forecast_available": forecast_available,
            "reports_generated": list(report_paths.keys()),
            "visualizations_generated": list(viz_paths.keys()),
            "forecast_charts": list(forecast_charts.keys()) if forecast_charts else []
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
