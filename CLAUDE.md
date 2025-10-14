# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StockGuru is a Python-based Chinese stock market analysis tool for short-term trading review. It automatically screens for strong momentum stocks and generates interactive HTML reports with visualizations.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Execute stock screening and report generation
python main.py

# Output: HTML report in ./output/ directory
```

### Testing
**Note**: No formal testing framework is currently implemented. When adding tests, consider pytest as the testing framework.

## Architecture Overview

### Core Modules (`modules/`)

1. **DataFetcher** (`data_fetcher.py`)
   - Integrates with pywencai (问财) and akshare for Chinese stock data
   - Fetches volume top stocks and heat top stocks
   - Retrieves historical K-line data for momentum calculation

2. **StockFilter** (`stock_filter.py`)
   - Implements Min-Max normalization for comprehensive scoring
   - Applies filtering rules (ST stocks, new stocks, price limits)
   - Combines volume and heat rankings with configurable weights

3. **MomentumCalculator** (`momentum_calculator.py`)
   - Calculates momentum using linear regression (slope × R²)
   - Computes moving averages (MA5, MA10, MA20)
   - 25-day momentum calculation period by default

4. **ReportGenerator** (`report_generator.py`)
   - Generates interactive HTML reports using PyEcharts
   - Creates candlestick charts with volume indicators
   - Uses Jinja2 templates for report formatting

### Data Flow

1. **Data Collection**: Volume Top 100 + Heat Top 100 → Intersection
2. **Normalization**: Min-Max scaling for ranking standardization
3. **Scoring**: Weighted combination (volume: 0.5, heat: 0.5)
4. **Filtering**: Apply exclusion rules (ST, new stocks, price limits)
5. **Momentum**: Linear regression on 25-day historical data
6. **Visualization**: Interactive HTML with K-line charts and indicators

### Configuration (`config.py`)

All parameters are centralized in `config.py`:
- Screening parameters (top N values, momentum days)
- Scoring weights (volume vs heat)
- Filtering rules (ST exclusion, new stock days, max rise ratio)
- Chart settings (MA periods, dimensions, display days)
- Output paths and logging configuration

### Key Dependencies

- **pywencai**: Stock heat/volume data from 问财
- **akshare**: Chinese stock market data API
- **pandas/numpy**: Data processing and analysis
- **scikit-learn**: Linear regression for momentum calculation
- **pyecharts**: Interactive chart generation
- **jinja2**: HTML template rendering

### Important Implementation Notes

1. **Fixed Date Testing**: Currently uses fixed date ('2024-10-11') for testing. Production should use dynamic recent trading day detection.

2. **Chinese Market Focus**: Specifically designed for A-share market with Chinese stock codes and names.

3. **No Database**: Currently file-based with data caching in `./data/cache/`.

4. **Error Handling**: Basic exception handling with logging to `stockguru.log`.

5. **Web Migration Planned**: See `web-implementation-guide.md` for Next.js + FastAPI architecture plans.

### Common Development Tasks

When modifying screening logic:
- Check `stock_filter.py` for scoring and filtering algorithms
- Update `config.py` for any new parameters
- Test with different date values in `main.py`

When adding new indicators:
- Extend `momentum_calculator.py` for technical indicators
- Update `report_generator.py` for visualization
- Modify HTML templates in `templates/` directory

When debugging data issues:
- Check pywencai/akshare connectivity and API changes
- Verify data formats in `data_fetcher.py`
- Review logs in `stockguru.log` for detailed error information