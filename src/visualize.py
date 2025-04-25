#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization module for stainless steel 444 alloy surcharge tracking.

This script generates various visualizations for understanding the
trends in raw material prices and the resulting alloy surcharge.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
REPORT_DIR = os.getenv('REPORT_OUTPUT_DIR', './reports')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Set style for matplotlib
sns.set(style="whitegrid")


def load_data(data_path=MASTER_DATA_FILE):
    """
    Load data from the master data file.
    
    Args:
        data_path (str, optional): Path to the master data file. Defaults to MASTER_DATA_FILE.
    
    Returns:
        pandas.DataFrame: Loaded data
    """
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def generate_price_trend_chart(df, output_dir=REPORT_DIR):
    """
    Generate a chart showing the price trends of raw materials.
    
    Args:
        df (pandas.DataFrame): Data frame with historical data
        output_dir (str, optional): Directory to save the chart. Defaults to REPORT_DIR.
    
    Returns:
        str: Path to the saved chart
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create figure
    fig = plt.figure(figsize=(12, 6))
    
    # Plot raw material prices
    plt.plot(df['date'], df['chromium_price'], marker='o', label='Chromium')
    plt.plot(df['date'], df['molybdenum_price'], marker='s', label='Molybdenum')
    plt.plot(df['date'], df['titanium_price'], marker='^', label='Titanium')
    
    # Formatting
    plt.title('Raw Material Price Trends (USD/MT)', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price (USD/MT)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    # Save figure
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f'price_trends_{today}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_surcharge_chart(df, output_dir=REPORT_DIR):
    """
    Generate a chart showing the alloy surcharge trend.
    
    Args:
        df (pandas.DataFrame): Data frame with historical data
        output_dir (str, optional): Directory to save the chart. Defaults to REPORT_DIR.
    
    Returns:
        str: Path to the saved chart
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot stacked bar for contributions
    bottom_data = np.zeros(len(df))
    for column, color, label in [
        ('chromium_contribution', '#8884d8', 'Chromium'),
        ('molybdenum_contribution', '#82ca9d', 'Molybdenum'),
        ('titanium_contribution', '#ffc658', 'Titanium')
    ]:
        ax1.bar(df['date'], df[column], bottom=bottom_data, label=label, alpha=0.7, color=color)
        bottom_data += df[column]
    
    # Plot line for total surcharge
    ax1.plot(df['date'], df['total_surcharge'], 'r-', marker='o', label='Total Surcharge', linewidth=2)
    
    # Formatting
    ax1.set_title('Monthly Alloy Surcharge for 444 Stainless Steel', fontsize=14)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('USD/MT', fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper left')
    
    plt.tight_layout()
    
    # Save figure
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f'surcharge_trend_{today}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_contribution_pie_chart(df, output_dir=REPORT_DIR):
    """
    Generate a pie chart showing the contribution of each element to the surcharge.
    
    Args:
        df (pandas.DataFrame): Data frame with historical data
        output_dir (str, optional): Directory to save the chart. Defaults to REPORT_DIR.
    
    Returns:
        str: Path to the saved chart
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate total contributions
    chromium_total = df['chromium_contribution'].sum()
    molybdenum_total = df['molybdenum_contribution'].sum()
    titanium_total = df['titanium_contribution'].sum()
    total = chromium_total + molybdenum_total + titanium_total
    
    # Calculate percentages
    chromium_pct = (chromium_total / total) * 100
    molybdenum_pct = (molybdenum_total / total) * 100
    titanium_pct = (titanium_total / total) * 100
    
    # Create figure
    plt.figure(figsize=(8, 8))
    
    # Plot pie chart
    plt.pie(
        [chromium_pct, molybdenum_pct, titanium_pct],
        labels=['Chromium (18.5%)', 'Molybdenum (2.1%)', 'Titanium (0.4%)'],
        autopct='%1.1f%%',
        startangle=90,
        colors=['#8884d8', '#82ca9d', '#ffc658'],
        shadow=True,
        explode=(0.05, 0.05, 0.05)
    )
    
    # Formatting
    plt.title('Element Contribution to Alloy Surcharge', fontsize=14)
    plt.tight_layout()
    
    # Save figure
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f'contribution_pie_{today}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_interactive_dashboard(df, output_dir=REPORT_DIR):
    """
    Generate an interactive HTML dashboard with Plotly.
    
    Args:
        df (pandas.DataFrame): Data frame with historical data
        output_dir (str, optional): Directory to save the dashboard. Defaults to REPORT_DIR.
    
    Returns:
        str: Path to the saved dashboard
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Raw Material Price Trends (USD/MT)',
            'Monthly Alloy Surcharge',
            'Element Contribution to Surcharge',
            'Month-over-Month Change (%)'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'pie'}, {'type': 'bar'}]
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # 1. Raw Material Price Trends
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['chromium_price'], mode='lines+markers', name='Chromium'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['molybdenum_price'], mode='lines+markers', name='Molybdenum'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['titanium_price'], mode='lines+markers', name='Titanium'),
        row=1, col=1
    )
    
    # 2. Monthly Alloy Surcharge
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['total_surcharge'], mode='lines+markers', name='Total Surcharge',
                   line=dict(color='red', width=3)),
        row=1, col=2
    )
    
    # 3. Element Contribution to Surcharge (Pie Chart)
    # Calculate total contributions
    chromium_total = df['chromium_contribution'].sum()
    molybdenum_total = df['molybdenum_contribution'].sum()
    titanium_total = df['titanium_contribution'].sum()
    
    fig.add_trace(
        go.Pie(
            labels=['Chromium (18.5%)', 'Molybdenum (2.1%)', 'Titanium (0.4%)'],
            values=[chromium_total, molybdenum_total, titanium_total],
            marker=dict(colors=['#8884d8', '#82ca9d', '#ffc658']),
            textinfo='percent+label',
            hole=0.3
        ),
        row=2, col=1
    )
    
    # 4. Month-over-Month Change
    # Calculate month-over-month changes
    df['mom_change'] = df['total_surcharge'].pct_change() * 100
    
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['mom_change'],
            marker=dict(
                color=df['mom_change'].apply(lambda x: 'green' if x >= 0 else 'red'),
                opacity=0.7
            ),
            name='MoM Change'
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title='Stainless Steel 444 Alloy Surcharge Dashboard',
        height=800,
        width=1200,
        template='plotly_white',
        showlegend=False
    )
    
    # Save as HTML
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f'interactive_dashboard_{today}.html')
    fig.write_html(output_path)
    
    return output_path


def generate_all_visualizations():
    """
    Generate all visualizations and return their paths.
    
    Returns:
        dict: Dictionary with paths to all generated visualizations
    """
    # Load data
    df = load_data()
    
    # Generate all visualizations
    price_chart = generate_price_trend_chart(df)
    surcharge_chart = generate_surcharge_chart(df)
    pie_chart = generate_contribution_pie_chart(df)
    dashboard = generate_interactive_dashboard(df)
    
    return {
        'price_chart': price_chart,
        'surcharge_chart': surcharge_chart,
        'pie_chart': pie_chart,
        'dashboard': dashboard
    }


if __name__ == "__main__":
    print("Generating visualizations...")
    viz_paths = generate_all_visualizations()
    
    print("Visualizations generated:")
    for name, path in viz_paths.items():
        print(f"- {name}: {path}")
