#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Email service module for stainless steel 444 alloy surcharge tracking.

This module provides enhanced email notification capabilities with rich
visual content, embedded charts, and conditional formatting.
"""

import os
import io
import base64
import logging
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from jinja2 import Environment, FileSystemLoader
import smtplib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
REPORT_DIR = os.getenv('REPORT_OUTPUT_DIR', './reports')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')
CURRENT_MONTH_FILE = os.path.join(DATA_DIR, 'current_month.json')

# Email settings
EMAIL_TEMPLATE = os.getenv('EMAIL_TEMPLATE', 'enhanced_email_template.html')
EMAIL_USE_ENHANCED_TEMPLATE = os.getenv('EMAIL_USE_ENHANCED_TEMPLATE', 'True').lower() in ('true', 'yes', '1')


def generate_sparkline(data_series, color='#2d6ca2', fill_color=None, figsize=(2, 0.5), linewidth=2):
    """
    Generate a sparkline chart from a data series.
    
    Args:
        data_series (list or pandas.Series): Data to plot
        color (str): Line color
        fill_color (str, optional): Area fill color
        figsize (tuple): Figure size (width, height)
        linewidth (int): Line width
    
    Returns:
        bytes: PNG image data
    """
    # Set style
    plt.style.use('ggplot')
    
    # Create figure with tight layout and no axes
    fig = plt.figure(figsize=figsize, dpi=100)
    ax = fig.add_subplot(111)
    
    # Plot the data
    ax.plot(data_series, color=color, linewidth=linewidth)
    
    # Add fill if specified
    if fill_color:
        ax.fill_between(range(len(data_series)), data_series, alpha=0.2, color=fill_color)
    
    # Add marker for last point
    if len(data_series) > 0:
        ax.plot(len(data_series)-1, data_series.iloc[-1] if hasattr(data_series, 'iloc') else data_series[-1], 
                'o', color=color, markersize=4)
    
    # Remove all axes, grids, etc.
    ax.set_frame_on(False)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    
    # Return the buffer contents
    buffer.seek(0)
    return buffer.getvalue()


def generate_forecast_insights(forecast_data):
    """
    Generate natural language insights from forecast data.
    
    Args:
        forecast_data (dict): Forecast data
    
    Returns:
        dict: Dictionary with insight information
    """
    insights = {
        'trend_direction': 'stable',
        'trend_description': 'remain stable',
        'significant_events': None,
        'material_insights': []
    }
    
    try:
        # Determine overall trend direction for surcharge
        if 'alloy_surcharge' in forecast_data:
            surcharge = forecast_data['alloy_surcharge']['forecast']
            first_month = list(surcharge.values())[0]
            last_month = list(surcharge.values())[-1]
            percent_change = ((last_month - first_month) / first_month) * 100
            
            if percent_change > 5:
                insights['trend_direction'] = 'up'
                insights['trend_description'] = f'increase by approximately {percent_change:.1f}%'
            elif percent_change < -5:
                insights['trend_direction'] = 'down'
                insights['trend_description'] = f'decrease by approximately {abs(percent_change):.1f}%'
            else:
                insights['trend_description'] = 'remain relatively stable'
        
        # Check for significant events
        max_monthly_change = 0
        max_month = None
        
        if 'alloy_surcharge' in forecast_data:
            surcharge_values = list(forecast_data['alloy_surcharge']['forecast'].values())
            for i in range(1, len(surcharge_values)):
                monthly_change = ((surcharge_values[i] - surcharge_values[i-1]) / surcharge_values[i-1]) * 100
                if abs(monthly_change) > abs(max_monthly_change):
                    max_monthly_change = monthly_change
                    max_month = i
        
        if abs(max_monthly_change) > 8:
            month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                         'July', 'August', 'September', 'October', 'November', 'December']
            
            # Get the month name
            forecast_dates = list(forecast_data['alloy_surcharge']['forecast'].keys())
            forecast_date = datetime.strptime(forecast_dates[max_month], '%Y-%m-%d %H:%M:%S')
            month_name = month_names[forecast_date.month - 1]
            
            direction = "increase" if max_monthly_change > 0 else "decrease"
            insights['significant_events'] = f"A significant {direction} of {abs(max_monthly_change):.1f}% is expected in {month_name}."
        
        # Generate material-specific insights
        for material in ['chromium', 'molybdenum', 'titanium']:
            if material in forecast_data['raw_materials']:
                material_forecast = forecast_data['raw_materials'][material]['forecast']
                first_month = list(material_forecast.values())[0]
                last_month = list(material_forecast.values())[-1]
                percent_change = ((last_month - first_month) / first_month) * 100
                
                # Only add insights for significant changes
                if abs(percent_change) > 7:
                    direction = "up" if percent_change > 0 else "down"
                    insight = {
                        'material': material.capitalize(),
                        'direction': direction,
                        'message': f"{material.capitalize()} prices are projected to {'increase' if percent_change > 0 else 'decrease'} by {abs(percent_change):.1f}% over the next 6 months."
                    }
                    insights['material_insights'].append(insight)
        
        return insights
    
    except Exception as e:
        logger.error(f"Error generating forecast insights: {e}")
        return insights


def prepare_email_data(data, trend_analysis, viz_paths, validation_result=None, forecast_data=None, forecast_charts=None):
    """
    Prepare data for email template rendering.
    
    Args:
        data (dict): Current month's data
        trend_analysis (dict): Trend analysis results
        viz_paths (dict): Paths to visualization files
        validation_result (dict, optional): Data validation results
        forecast_data (dict, optional): Forecast data
        forecast_charts (dict, optional): Paths to forecast charts
    
    Returns:
        dict: Context data for email template
    """
    # Load historical data for sparklines
    historical_df = pd.read_csv(MASTER_DATA_FILE)
    historical_df['date'] = pd.to_datetime(historical_df['date'])
    historical_df = historical_df.sort_values('date')
    
    # Limit to last 6 months for sparklines
    sparkline_df = historical_df.tail(6)
    
    # Generate forecast insights if forecast data is available
    forecast_insights = None
    if forecast_data:
        forecast_insights = generate_forecast_insights(forecast_data)
    
    # Prepare dashboard and download links
    dashboard_url = os.getenv('DASHBOARD_URL', '#')
    if not dashboard_url or dashboard_url == '#':
        dashboard_url = f"file://{os.path.abspath(viz_paths.get('dashboard', ''))}"
    
    download_url = os.getenv('DOWNLOAD_URL', '#')
    if not download_url or download_url == '#':
        download_url = f"file://{os.path.abspath(os.path.join(REPORT_DIR, 'ss444_surcharge_export_' + datetime.now().strftime('%Y-%m') + '.csv'))}"
    
    # Build context for template
    context = {
        'report_month': datetime.strptime(data['date'], "%Y-%m-%d").strftime("%B %Y"),
        'current_month': data,
        'trend_analysis': trend_analysis,
        'historical_data': historical_df.to_dict('records'),
        'sparkline_data': {
            'chromium': sparkline_df['chromium_price'].tolist(),
            'molybdenum': sparkline_df['molybdenum_price'].tolist(),
            'titanium': sparkline_df['titanium_price'].tolist(),
            'surcharge': sparkline_df['total_surcharge'].tolist()
        },
        'validation': validation_result,
        'dashboard_link': dashboard_url,
        'download_link': download_url
    }
    
    # Add forecast data if available
    if forecast_data and forecast_insights:
        context['forecast'] = {
            'available': True,
            'data': forecast_data,
            'charts': forecast_charts,
            'trend_direction': forecast_insights['trend_direction'],
            'trend_description': forecast_insights['trend_description'],
            'significant_events': forecast_insights['significant_events'],
            'material_insights': forecast_insights['material_insights']
        }
    else:
        context['forecast'] = {'available': False}
    
    return context


def create_inline_charts(email_context):
    """
    Create inline charts for embedding in the HTML email.
    
    Args:
        email_context (dict): Context data for email template
    
    Returns:
        dict: Dictionary of chart image data
    """
    charts = {}
    
    # Generate sparklines for each material
    sparkline_data = email_context['sparkline_data']
    
    # Surcharge sparkline
    surcharge_data = sparkline_data['surcharge']
    charts['surcharge_sparkline'] = generate_sparkline(
        surcharge_data, 
        color='#2874a6', 
        fill_color='#aed6f1'
    )
    
    # Material-specific sparklines
    charts['chromium_sparkline'] = generate_sparkline(
        sparkline_data['chromium'], 
        color='#7d3c98', 
        fill_color='#d2b4de'
    )
    
    charts['molybdenum_sparkline'] = generate_sparkline(
        sparkline_data['molybdenum'], 
        color='#28b463', 
        fill_color='#abebc6'
    )
    
    charts['titanium_sparkline'] = generate_sparkline(
        sparkline_data['titanium'], 
        color='#f39c12', 
        fill_color='#fad7a0'
    )
    
    # Add main visualization charts if paths are provided
    for chart_name in ['surcharge_chart', 'price_chart', 'pie_chart']:
        if chart_name in email_context.get('visualizations', {}):
            chart_path = email_context['visualizations'][chart_name]
            if os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    if chart_name == 'pie_chart':
                        charts['contribution_pie'] = f.read()
                    else:
                        charts[chart_name] = f.read()
    
    # Add forecast chart if available
    if email_context.get('forecast', {}).get('available', False):
        forecast_charts = email_context.get('forecast', {}).get('charts', {})
        if 'surcharge_chart' in forecast_charts and os.path.exists(forecast_charts['surcharge_chart']):
            with open(forecast_charts['surcharge_chart'], 'rb') as f:
                charts['surcharge_forecast'] = f.read()
    
    return charts


def send_enhanced_email(recipient, subject, report_paths, email_context, inline_charts):
    """
    Send an enhanced HTML email with inline charts and attachments.
    
    Args:
        recipient (str): Email recipient
        subject (str): Email subject
        report_paths (dict): Paths to report files to attach
        email_context (dict): Context data for email template
        inline_charts (dict): Dictionary of chart image data
    
    Returns:
        bool: True if successful, False otherwise
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    # Skip if email settings are not configured
    if not all([recipient, smtp_server, smtp_username, smtp_password]):
        logger.warning("Email notification skipped - missing configuration")
        return False
    
    try:
        # Render email template
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template(EMAIL_TEMPLATE)
        html_content = template.render(**email_context)
        
        # Create email message
        msg = MIMEMultipart('related')
        msg['From'] = smtp_username
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Attach inline charts
        for chart_id, chart_data in inline_charts.items():
            image = MIMEImage(chart_data)
            image.add_header('Content-ID', f'<{chart_id}>')
            image.add_header('Content-Disposition', 'inline')
            msg.attach(image)
        
        # Attach report files
        for name, path in report_paths.items():
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
        
        logger.info(f"Enhanced email notification sent to {recipient}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send enhanced email notification: {e}")
        return False


def send_notification_email(report_paths, data, trend_analysis, viz_paths, validation_result=None, forecast_available=False, forecast_data=None, forecast_charts=None):
    """
    Send a notification email with the generated reports.
    
    Args:
        report_paths (dict): Dictionary with paths to generated reports
        data (dict): Current month's data
        trend_analysis (dict): Trend analysis results
        viz_paths (dict): Paths to visualization files
        validation_result (dict, optional): Data validation results
        forecast_available (bool): Whether forecast data is available
        forecast_data (dict, optional): Forecast data
        forecast_charts (dict, optional): Paths to forecast charts
    
    Returns:
        bool: True if successful, False otherwise
    """
    notify_email = os.getenv('NOTIFY_EMAIL')
    
    # Skip if email recipient is not configured
    if not notify_email:
        logger.warning("Email notification skipped - recipient not configured")
        return False
    
    # Get current month for subject line
    report_month = datetime.strptime(data['date'], "%Y-%m-%d").strftime("%B %Y")
    subject = f"Stainless Steel 444 Alloy Surcharge Report - {report_month}"
    
    # Use enhanced email if enabled
    if EMAIL_USE_ENHANCED_TEMPLATE:
        # Prepare email context data
        email_context = prepare_email_data(
            data, 
            trend_analysis, 
            viz_paths, 
            validation_result, 
            forecast_data, 
            forecast_charts
        )
        
        # Create inline charts
        inline_charts = create_inline_charts(email_context)
        
        # Send enhanced email
        return send_enhanced_email(
            notify_email,
            subject,
            report_paths,
            email_context,
            inline_charts
        )
    
    # Fall back to basic email if enhanced template is disabled
    else:
        # Use the simpler email function from monthly_update.py
        # This is a simplified version for backward compatibility
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            # Create basic message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = notify_email
            msg['Subject'] = subject
            
            # Add basic body
            body = f"""Monthly stainless steel 444 alloy surcharge report for {report_month} is attached.

Current Surcharge: ${data['total_surcharge']:.2f} per metric ton
Change from previous month: {data['change_from_previous']:.2f}%

Please review the attached files for the latest pricing information and trends.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach files
            for name, path in report_paths.items():
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
            
            logger.info(f"Basic email notification sent to {notify_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


if __name__ == "__main__":
    # Configure logging for command line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test sparkline generation
    test_data = [100, 105, 103, 110, 108, 115]
    sparkline = generate_sparkline(test_data)
    
    # Save test sparkline
    with open('test_sparkline.png', 'wb') as f:
        f.write(sparkline)
    
    print("Test sparkline generated as 'test_sparkline.png'")
