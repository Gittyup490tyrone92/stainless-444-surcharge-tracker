#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Price forecasting module for stainless steel 444 alloy surcharge tracking.

This module contains functions to analyze historical price trends and generate
forecasts for raw material prices and alloy surcharges.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging
from dotenv import load_dotenv
from pathlib import Path

# Import local modules
from calculate import DEFAULT_COMPOSITION, calculate_surcharge

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = os.getenv('DATA_DIR', './data')
FORECAST_DIR = os.path.join(DATA_DIR, 'forecasts')
MASTER_DATA_FILE = os.path.join(DATA_DIR, 'master_data.csv')

# Forecast parameters
FORECAST_PERIODS = 6  # Number of months to forecast
CONFIDENCE_LEVEL = 0.95  # Confidence level for prediction intervals


def prepare_time_series_data(data_path=MASTER_DATA_FILE):
    """
    Prepare time series data for forecasting.
    
    Args:
        data_path (str, optional): Path to the master data file. Defaults to MASTER_DATA_FILE.
    
    Returns:
        pandas.DataFrame: DataFrame with time series data prepared for forecasting
    """
    try:
        # Load historical data
        df = pd.read_csv(data_path)
        
        # Convert date string to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date')
        
        # Set date as index
        df_ts = df.set_index('date')
        
        return df_ts
    
    except Exception as e:
        logger.error(f"Error preparing time series data: {e}")
        return None


def generate_arima_forecast(series, periods=FORECAST_PERIODS, confidence=CONFIDENCE_LEVEL):
    """
    Generate forecast using ARIMA model.
    
    Args:
        series (pandas.Series): Time series data to forecast
        periods (int, optional): Number of periods to forecast. Defaults to FORECAST_PERIODS.
        confidence (float, optional): Confidence level for prediction intervals. Defaults to CONFIDENCE_LEVEL.
    
    Returns:
        tuple: (forecast, lower_bound, upper_bound) - Series of forecasted values and confidence intervals
    """
    try:
        # Find best ARIMA parameters (simplified approach)
        # In a production system, you would use a more sophisticated approach like auto_arima from pmdarima
        best_aic = float('inf')
        best_params = (1, 1, 1)
        
        # Try different parameters
        for p in range(3):
            for d in range(2):
                for q in range(3):
                    try:
                        model = ARIMA(series, order=(p, d, q))
                        results = model.fit()
                        
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_params = (p, d, q)
                    except:
                        continue
        
        # Fit the best model
        final_model = ARIMA(series, order=best_params)
        results = final_model.fit()
        
        # Generate forecast
        forecast_obj = results.get_forecast(steps=periods)
        forecast_mean = forecast_obj.predicted_mean
        
        # Get confidence intervals
        forecast_ci = forecast_obj.conf_int(alpha=(1 - confidence))
        lower_bound = forecast_ci.iloc[:, 0]
        upper_bound = forecast_ci.iloc[:, 1]
        
        # Ensure forecast doesn't go negative
        forecast_mean = forecast_mean.apply(lambda x: max(0, x))
        lower_bound = lower_bound.apply(lambda x: max(0, x))
        
        return forecast_mean, lower_bound, upper_bound
    
    except Exception as e:
        logger.error(f"Error generating ARIMA forecast: {e}")
        return None, None, None


def generate_exponential_smoothing_forecast(series, periods=FORECAST_PERIODS, confidence=CONFIDENCE_LEVEL):
    """
    Generate forecast using Exponential Smoothing model.
    
    Args:
        series (pandas.Series): Time series data to forecast
        periods (int, optional): Number of periods to forecast. Defaults to FORECAST_PERIODS.
        confidence (float, optional): Confidence level for prediction intervals. Defaults to CONFIDENCE_LEVEL.
    
    Returns:
        tuple: (forecast, lower_bound, upper_bound) - Series of forecasted values and confidence intervals
    """
    try:
        # Determine if data has seasonal pattern
        if len(series) >= 12:
            # Try to detect seasonality
            try:
                decomposition = seasonal_decompose(series, model='additive', period=12)
                has_seasonality = decomposition.seasonal.abs().mean() > 0.1 * series.mean()
            except:
                has_seasonality = False
        else:
            has_seasonality = False
        
        # Set up model based on detected patterns
        if has_seasonality:
            model = ExponentialSmoothing(
                series,
                seasonal_periods=12,
                trend='add',
                seasonal='add',
                use_boxcox=False,
                initialization_method="estimated"
            )
        else:
            model = ExponentialSmoothing(
                series,
                trend='add',
                seasonal=None,
                use_boxcox=False,
                initialization_method="estimated"
            )
        
        # Fit model
        results = model.fit()
        
        # Generate forecast
        forecast = results.forecast(periods)
        
        # Calculate forecast errors for confidence intervals
        residuals = results.resid
        residual_std = residuals.std()
        
        # Z-value for confidence interval
        import scipy.stats as stats
        z = stats.norm.ppf((1 + confidence) / 2)
        
        # Create confidence intervals
        margin_of_error = z * residual_std * np.sqrt(np.arange(1, periods + 1))
        lower_bound = forecast - margin_of_error
        upper_bound = forecast + margin_of_error
        
        # Ensure forecast doesn't go negative
        forecast = forecast.apply(lambda x: max(0, x))
        lower_bound = lower_bound.apply(lambda x: max(0, x))
        
        return forecast, lower_bound, upper_bound
    
    except Exception as e:
        logger.error(f"Error generating Exponential Smoothing forecast: {e}")
        return None, None, None


def calculate_forecast_surcharge(forecasts, composition=DEFAULT_COMPOSITION):
    """
    Calculate forecasted alloy surcharge based on forecasted raw material prices.
    
    Args:
        forecasts (dict): Dictionary with forecasted prices for raw materials
        composition (dict, optional): Alloy composition percentages. Defaults to DEFAULT_COMPOSITION.
    
    Returns:
        pandas.Series: Forecasted surcharge values
    """
    try:
        # Extract forecasted prices
        chromium_forecast = forecasts['chromium']
        molybdenum_forecast = forecasts['molybdenum']
        titanium_forecast = forecasts['titanium']
        
        # Ensure all forecasts have the same length
        min_length = min(len(chromium_forecast), len(molybdenum_forecast), len(titanium_forecast))
        
        # Calculate surcharge for each forecasted period
        surcharge_forecast = []
        surcharge_dates = chromium_forecast.index[:min_length]
        
        for i in range(min_length):
            prices = {
                'chromium': chromium_forecast.iloc[i],
                'molybdenum': molybdenum_forecast.iloc[i],
                'titanium': titanium_forecast.iloc[i]
            }
            
            result = calculate_surcharge(prices, composition)
            surcharge_forecast.append(result['total_surcharge'])
        
        # Create a Series with dates as index
        return pd.Series(surcharge_forecast, index=surcharge_dates)
    
    except Exception as e:
        logger.error(f"Error calculating forecast surcharge: {e}")
        return None


def generate_forecast():
    """
    Generate forecasts for raw material prices and alloy surcharges.
    
    Returns:
        dict: Dictionary with all forecast data
    """
    try:
        # Prepare time series data
        df_ts = prepare_time_series_data()
        if df_ts is None or len(df_ts) < 6:  # Need at least 6 data points for meaningful forecasting
            logger.warning("Not enough historical data for forecasting")
            return None
        
        # Create forecasts directory if it doesn't exist
        os.makedirs(FORECAST_DIR, exist_ok=True)
        
        # Forecast each raw material price
        forecasts = {}
        lower_bounds = {}
        upper_bounds = {}
        
        # Current date for forecast start
        last_date = df_ts.index[-1]
        forecast_start = last_date + timedelta(days=1)
        forecast_dates = pd.date_range(
            start=forecast_start,
            periods=FORECAST_PERIODS,
            freq='MS'  # Month start frequency
        )
        
        for material in ['chromium', 'molybdenum', 'titanium']:
            column = f"{material}_price"
            
            # Get historical series
            series = df_ts[column]
            
            # Generate forecasts using both methods
            arima_forecast, arima_lower, arima_upper = generate_arima_forecast(series)
            es_forecast, es_lower, es_upper = generate_exponential_smoothing_forecast(series)
            
            # Choose the better model based on error metrics
            if arima_forecast is not None and es_forecast is not None:
                # Calculate error metrics for both models
                # Use the last 3 months as a test set
                test_size = min(3, len(series) // 3)
                train_series = series[:-test_size]
                test_series = series[-test_size:]
                
                # ARIMA errors
                arima_model = ARIMA(train_series, order=(1, 1, 1))  # Simplified for example
                arima_fit = arima_model.fit()
                arima_pred = arima_fit.forecast(steps=test_size)
                arima_mae = mean_absolute_error(test_series, arima_pred)
                
                # Exponential Smoothing errors
                es_model = ExponentialSmoothing(train_series, trend='add', seasonal=None)
                es_fit = es_model.fit()
                es_pred = es_fit.forecast(test_size)
                es_mae = mean_absolute_error(test_series, es_pred)
                
                # Choose the model with lower MAE
                if arima_mae < es_mae:
                    logger.info(f"Using ARIMA for {material} forecasting (MAE: {arima_mae:.2f})")
                    material_forecast = pd.Series(arima_forecast.values, index=forecast_dates)
                    material_lower = pd.Series(arima_lower.values, index=forecast_dates)
                    material_upper = pd.Series(arima_upper.values, index=forecast_dates)
                else:
                    logger.info(f"Using Exponential Smoothing for {material} forecasting (MAE: {es_mae:.2f})")
                    material_forecast = pd.Series(es_forecast.values, index=forecast_dates)
                    material_lower = pd.Series(es_lower.values, index=forecast_dates)
                    material_upper = pd.Series(es_upper.values, index=forecast_dates)
            
            elif arima_forecast is not None:
                material_forecast = pd.Series(arima_forecast.values, index=forecast_dates)
                material_lower = pd.Series(arima_lower.values, index=forecast_dates)
                material_upper = pd.Series(arima_upper.values, index=forecast_dates)
            
            elif es_forecast is not None:
                material_forecast = pd.Series(es_forecast.values, index=forecast_dates)
                material_lower = pd.Series(es_lower.values, index=forecast_dates)
                material_upper = pd.Series(es_upper.values, index=forecast_dates)
            
            else:
                logger.error(f"Both forecasting methods failed for {material}")
                return None
            
            forecasts[material] = material_forecast
            lower_bounds[material] = material_lower
            upper_bounds[material] = material_upper
        
        # Calculate forecasted surcharge
        surcharge_forecast = calculate_forecast_surcharge(forecasts)
        
        # Calculate lower and upper bounds for surcharge
        lower_surcharge = calculate_forecast_surcharge(lower_bounds)
        upper_surcharge = calculate_forecast_surcharge(upper_bounds)
        
        # Create forecast result object
        forecast_result = {
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'forecast_periods': FORECAST_PERIODS,
            'confidence_level': CONFIDENCE_LEVEL,
            'raw_materials': {
                material: {
                    'forecast': forecasts[material].to_dict(),
                    'lower_bound': lower_bounds[material].to_dict(),
                    'upper_bound': upper_bounds[material].to_dict()
                } for material in ['chromium', 'molybdenum', 'titanium']
            },
            'alloy_surcharge': {
                'forecast': surcharge_forecast.to_dict(),
                'lower_bound': lower_surcharge.to_dict(),
                'upper_bound': upper_surcharge.to_dict()
            }
        }
        
        # Save forecast result to file
        current_month = datetime.now().strftime("%Y-%m")
        forecast_file = os.path.join(FORECAST_DIR, f'forecast_{current_month}.json')
        
        with open(forecast_file, 'w') as f:
            json.dump(forecast_result, f, indent=2)
        
        logger.info(f"Forecast generated and saved to {forecast_file}")
        
        return forecast_result
    
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        return None


def generate_forecast_chart(forecast_data, output_dir=None):
    """
    Generate charts visualizing the forecasts.
    
    Args:
        forecast_data (dict): Forecast data generated by generate_forecast()
        output_dir (str, optional): Directory to save the charts. Defaults to FORECAST_DIR.
    
    Returns:
        dict: Dictionary with paths to the generated charts
    """
    if output_dir is None:
        output_dir = FORECAST_DIR
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    chart_paths = {}
    
    try:
        # Set style for charts
        sns.set(style="whitegrid")
        
        # Current date for file naming
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Generate raw material price forecast charts
        for material in ['chromium', 'molybdenum', 'titanium']:
            plt.figure(figsize=(10, 6))
            
            # Convert forecast data to pandas Series
            dates = [datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in forecast_data['raw_materials'][material]['forecast'].keys()]
            forecast_values = list(forecast_data['raw_materials'][material]['forecast'].values())
            lower_values = list(forecast_data['raw_materials'][material]['lower_bound'].values())
            upper_values = list(forecast_data['raw_materials'][material]['upper_bound'].values())
            
            # Plot forecast line
            plt.plot(dates, forecast_values, 'b-', label='Forecast')
            
            # Plot confidence interval
            plt.fill_between(
                dates,
                lower_values,
                upper_values,
                alpha=0.2,
                color='b',
                label=f'{int(forecast_data["confidence_level"]*100)}% Confidence Interval'
            )
            
            # Add labels and title
            plt.title(f'{material.capitalize()} Price Forecast (USD/MT)', fontsize=14)
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Price (USD/MT)', fontsize=12)
            plt.xticks(rotation=45)
            plt.legend()
            plt.tight_layout()
            
            # Save chart
            chart_path = os.path.join(output_dir, f'{material}_forecast_{current_date}.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_paths[f'{material}_chart'] = chart_path
        
        # 2. Generate alloy surcharge forecast chart
        plt.figure(figsize=(10, 6))
        
        # Convert forecast data to pandas Series
        dates = [datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in forecast_data['alloy_surcharge']['forecast'].keys()]
        forecast_values = list(forecast_data['alloy_surcharge']['forecast'].values())
        lower_values = list(forecast_data['alloy_surcharge']['lower_bound'].values())
        upper_values = list(forecast_data['alloy_surcharge']['upper_bound'].values())
        
        # Plot forecast line
        plt.plot(dates, forecast_values, 'r-', label='Forecast')
        
        # Plot confidence interval
        plt.fill_between(
            dates,
            lower_values,
            upper_values,
            alpha=0.2,
            color='r',
            label=f'{int(forecast_data["confidence_level"]*100)}% Confidence Interval'
        )
        
        # Add labels and title
        plt.title('Stainless Steel 444 Alloy Surcharge Forecast (USD/MT)', fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Surcharge (USD/MT)', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Save chart
        chart_path = os.path.join(output_dir, f'surcharge_forecast_{current_date}.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        chart_paths['surcharge_chart'] = chart_path
        
        return chart_paths
    
    except Exception as e:
        logger.error(f"Error generating forecast charts: {e}")
        return {}


if __name__ == "__main__":
    # Configure logging for command line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Generating price forecasts...")
    forecast_data = generate_forecast()
    
    if forecast_data:
        print("Generating forecast charts...")
        chart_paths = generate_forecast_chart(forecast_data)
        
        print("\nForecasts generated:")
        for name, path in chart_paths.items():
            print(f"- {name}: {path}")
    else:
        print("Failed to generate forecasts. See logs for details.")
