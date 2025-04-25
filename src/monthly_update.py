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
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Import project modules
from collect_data import collect_and_save_data
from visualize import generate_all_visualizations
from generate_report import generate_all_reports

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


def send_notification_email(report_paths):
    """
    Send a notification email with the generated reports.
    
    Args:
        report_paths (dict): Dictionary with paths to generated reports
    
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
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = notify_email
        msg['Subject'] = f"Stainless Steel 444 Alloy Surcharge Report - {datetime.now().strftime('%B %Y')}"
        
        # Add body
        body = """Monthly stainless steel 444 alloy surcharge report is attached.

This automated email contains:
1. The monthly PDF report with detailed analysis and visualizations
2. Executive summary as a text file
3. CSV export for data integration

Please review the attached files for the latest pricing information and trends.
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach files
        for name, path in report_paths.items():
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
        
        # Step 2: Generate visualizations
        logger.info("Step 2: Generating visualizations")
        viz_paths = generate_all_visualizations()
        logger.info(f"Generated {len(viz_paths)} visualizations")
        
        # Step 3: Generate reports
        logger.info("Step 3: Generating reports")
        report_paths = generate_all_reports()
        logger.info(f"Generated {len(report_paths)} reports")
        
        # Step 4: Send notification
        logger.info("Step 4: Sending notification")
        send_notification_email(report_paths)
        
        logger.info("Monthly update process completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Monthly update process failed: {e}")
        return False


if __name__ == "__main__":
    successful = run_monthly_update()
    sys.exit(0 if successful else 1)
