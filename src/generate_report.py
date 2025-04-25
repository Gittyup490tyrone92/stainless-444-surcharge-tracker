#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report generation module for stainless steel 444 alloy surcharge tracking.

This script generates comprehensive monthly reports on alloy surcharge
trends for stainless steel 444.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import weasyprint
from dotenv import load_dotenv

# Import visualization module
from visualize import generate_all_visualizations, load_data
from calculate import calculate_monthly_trend

# Load environment variables
load_dotenv()

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
REPORT_DIR = os.getenv('REPORT_OUTPUT_DIR', './reports')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
CURRENT_MONTH_FILE = os.path.join(DATA_DIR, 'current_month.json')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')


def generate_monthly_report():
    """
    Generate a comprehensive monthly report on alloy surcharge trends.
    
    Returns:
        str: Path to the generated report
    """
    # Create output directory if it doesn't exist
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Load data
    df = load_data()
    current_month_data = json.load(open(CURRENT_MONTH_FILE, 'r'))
    trend_analysis = calculate_monthly_trend(MASTER_DATA_FILE)
    
    # Generate visualizations
    viz_paths = generate_all_visualizations()
    
    # Prepare data for the report
    report_data = {
        'current_date': datetime.now().strftime("%B %d, %Y"),
        'report_month': datetime.strptime(current_month_data['date'], "%Y-%m-%d").strftime("%B %Y"),
        'current_month': current_month_data,
        'trend_analysis': trend_analysis,
        'visualizations': viz_paths,
        'historical_data': df.tail(12).to_dict(orient='records')
    }
    
    # Generate HTML report from template
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('monthly_report_template.html')
    html_content = template.render(**report_data)
    
    # Save HTML report
    report_date = datetime.now().strftime("%Y-%m")
    html_path = os.path.join(REPORT_DIR, f'monthly_report_{report_date}.html')
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    # Convert to PDF
    pdf_path = os.path.join(REPORT_DIR, f'monthly_report_{report_date}.pdf')
    weasyprint.HTML(html_path).write_pdf(pdf_path)
    
    print(f"Monthly report generated: {pdf_path}")
    return pdf_path


def generate_executive_summary():
    """
    Generate a brief executive summary of the current month's alloy surcharge.
    
    Returns:
        str: Path to the generated summary
    """
    # Create output directory if it doesn't exist
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Load data
    current_month_data = json.load(open(CURRENT_MONTH_FILE, 'r'))
    df = load_data()
    
    # Get last two months for comparison
    last_two_months = df.tail(2)
    if len(last_two_months) >= 2:
        current = last_two_months.iloc[-1]
        previous = last_two_months.iloc[-2]
        mom_change = ((current['total_surcharge'] - previous['total_surcharge']) / 
                     previous['total_surcharge']) * 100
    else:
        mom_change = 0
    
    # Get 12-month trend if available
    if len(df) >= 12:
        year_ago = df.iloc[-13] if len(df) >= 13 else df.iloc[0]
        current = df.iloc[-1]
        yoy_change = ((current['total_surcharge'] - year_ago['total_surcharge']) / 
                     year_ago['total_surcharge']) * 100
    else:
        yoy_change = 0
    
    # Prepare data for the summary
    summary_data = {
        'current_date': datetime.now().strftime("%B %d, %Y"),
        'report_month': datetime.strptime(current_month_data['date'], "%Y-%m-%d").strftime("%B %Y"),
        'current_surcharge': current_month_data['total_surcharge'],
        'mom_change': mom_change,
        'yoy_change': yoy_change,
        'raw_materials': current_month_data['raw_prices'],
        'contributions': current_month_data['contributions'],
        'notes': current_month_data.get('notes', '')
    }
    
    # Generate text summary
    summary = f"""EXECUTIVE SUMMARY: STAINLESS STEEL 444 ALLOY SURCHARGE
{'-'*60}
Report Date: {summary_data['current_date']}
Period: {summary_data['report_month']}

KEY FINDINGS:

1. Current Alloy Surcharge: ${summary_data['current_surcharge']:.2f} per metric ton

2. Monthly Change: {summary_data['mom_change']:.2f}%

3. Year-over-Year Change: {summary_data['yoy_change']:.2f}%

4. Raw Material Prices (USD/MT):
   - Chromium: ${summary_data['raw_materials']['chromium']:.2f}
   - Molybdenum: ${summary_data['raw_materials']['molybdenum']:.2f}
   - Titanium: ${summary_data['raw_materials']['titanium']:.2f}

5. Element Contributions to Surcharge:
   - Chromium (18.5%): ${summary_data['contributions']['chromium']:.2f}
   - Molybdenum (2.1%): ${summary_data['contributions']['molybdenum']:.2f}
   - Titanium (0.4%): ${summary_data['contributions']['titanium']:.2f}

NOTES:
{summary_data['notes']}

For the full report and visualizations, please refer to the monthly report.
"""
    
    # Save summary
    report_date = datetime.now().strftime("%Y-%m")
    summary_path = os.path.join(REPORT_DIR, f'executive_summary_{report_date}.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    print(f"Executive summary generated: {summary_path}")
    return summary_path


def generate_csv_export():
    """
    Generate a CSV export of the latest data for integration with other systems.
    
    Returns:
        str: Path to the exported CSV
    """
    # Create output directory if it doesn't exist
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Load data
    df = load_data()
    
    # Format date for easier integration
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Select columns for export
    export_columns = [
        'year', 'month', 'date',
        'chromium_price', 'molybdenum_price', 'titanium_price',
        'chromium_contribution', 'molybdenum_contribution', 'titanium_contribution',
        'total_surcharge'
    ]
    
    export_df = df[export_columns]
    
    # Save to CSV
    report_date = datetime.now().strftime("%Y-%m")
    export_path = os.path.join(REPORT_DIR, f'ss444_surcharge_export_{report_date}.csv')
    export_df.to_csv(export_path, index=False)
    
    print(f"CSV export generated: {export_path}")
    return export_path


def generate_all_reports():
    """
    Generate all types of reports.
    
    Returns:
        dict: Dictionary with paths to all generated reports
    """
    monthly_report = generate_monthly_report()
    executive_summary = generate_executive_summary()
    csv_export = generate_csv_export()
    
    return {
        'monthly_report': monthly_report,
        'executive_summary': executive_summary,
        'csv_export': csv_export
    }


if __name__ == "__main__":
    print("Generating reports...")
    report_paths = generate_all_reports()
    
    print("\nReports generated:")
    for name, path in report_paths.items():
        print(f"- {name}: {path}")
