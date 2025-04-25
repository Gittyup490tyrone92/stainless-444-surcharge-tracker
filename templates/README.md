# Email Templates Directory

This directory contains HTML templates for email notifications sent by the Stainless Steel 444 Alloy Surcharge Tracker system.

## Available Templates

1. **email_template.html** - Basic email template with minimal styling.
2. **enhanced_email_template.html** - Rich visual template with embedded charts, sparklines, and conditional sections.

## Template Selection

The template used for emails is controlled by the following environment variables in your `.env` file:

```
EMAIL_USE_ENHANCED_TEMPLATE=True
EMAIL_TEMPLATE=enhanced_email_template.html
```

## Template Context Data

The templates are rendered with the following context data:

- `report_month` - Current report month (e.g., "April 2025")
- `current_month` - Current month's data including:
  - `date` - Report date
  - `raw_prices` - Raw material prices
  - `contributions` - Element contributions to surcharge
  - `total_surcharge` - Total calculated surcharge
  - `change_from_previous` - Percentage change from previous month
  - `data_sources` - List of data source names
  - `notes` - Market notes
- `trend_analysis` - Trend analysis results including:
  - `latest_month` - Latest month's data
  - `avg_surcharge` - Average surcharge over the time period
  - `contribution_percentages` - Element contribution percentages
- `historical_data` - List of historical data records
- `validation` - Data validation results (if validation is enabled)
- `forecast` - Price forecast data (if forecasting is enabled)
- `dashboard_link` - URL to view the full dashboard
- `download_link` - URL to download the data

## Inline Charts

The enhanced template supports the following embedded images:

1. **Sparklines** - Tiny inline charts showing trends:
   - `surcharge_sparkline` - Surcharge trend sparkline
   - `chromium_sparkline` - Chromium price sparkline
   - `molybdenum_sparkline` - Molybdenum price sparkline
   - `titanium_sparkline` - Titanium price sparkline

2. **Full Charts**:
   - `contribution_pie` - Pie chart showing element contributions
   - `surcharge_chart` - Surcharge trend chart
   - `price_chart` - Raw material price chart
   - `surcharge_forecast` - Surcharge forecast chart (if available)

## Customizing Templates

### Creating a New Template

1. Copy an existing template as a starting point:
   ```
   cp enhanced_email_template.html custom_template.html
   ```

2. Modify the HTML and CSS to match your preferred style.

3. Update your `.env` file to use the new template:
   ```
   EMAIL_TEMPLATE=custom_template.html
   ```

### Email Compatibility Tips

When customizing templates, keep these email client compatibility tips in mind:

1. **Inline CSS** - Always use inline CSS as some email clients strip `<style>` tags.
2. **Table-based layout** - For maximum compatibility, consider using table-based layouts.
3. **Image Size** - Always specify width and height for images.
4. **Limited CSS Support** - Avoid advanced CSS features like CSS Grid, Flexbox, or CSS variables.
5. **No JavaScript** - Email clients block JavaScript.
6. **Limited HTML5 Support** - Stick to basic HTML elements.
7. **Test Thoroughly** - Test your templates in multiple email clients.

## Components

The enhanced template includes several reusable components:

1. **Key Metrics Grid** - Displays key metrics with sparklines.
2. **Materials Container** - Lists material prices with changes and trends.
3. **Validation Alert** - Shows validation issues when present.
4. **Forecast Section** - Displays forecast data with insights.
5. **Collapsible Sections** - Expandable content sections.

## Adding New Components

To add new components to a template:

1. Define the HTML structure and CSS for your component.
2. Add the component to the template where appropriate.
3. Update the `email_service.py` file if your component requires additional data.

## Debugging Templates

For debugging, you can save the rendered template to a file:

```python
# In email_service.py
html_content = template.render(**email_context)
with open('debug_email.html', 'w') as f:
    f.write(html_content)
```

This will save the rendered HTML to a file you can open in a browser.
