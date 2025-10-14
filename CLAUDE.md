# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StockGuru is a Chinese stock market analysis tool for short-term trading review. It has evolved from a simple Python CLI tool to a full-stack web application with FastAPI backend and Next.js frontend.

**Current Architecture**: Dual-mode system supporting both CLI (v0.9.0) and web application (v2.0.0)

## Development Commands

### CLI Tool (Legacy - v0.9.0)
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run stock screening
python cli.py

# Output: HTML reports in ./output/ directory
```

### Web Application (Current - v2.0.0)
```bash
# Quick start - use provided scripts
cd scripts/start
./start-all.sh    # Start both frontend and backend
./stop-all.sh     # Stop all services

# Manual setup
cd stockguru-web/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in separate terminal)
cd frontend
npm install
npm run dev  # Next.js with Turbopack on port 3000
```

### Testing
```bash
# System diagnostics and testing
cd scripts/test
./diagnose.sh        # Full system check
./test-system.sh     # System functionality test
./test-real-data.sh  # Test with real market data

# Manual test files (no formal framework)
cd tests
python test-momentum.py      # Momentum calculation tests
python test_kline_api.py     # K-line data API tests
```

## Architecture Overview

### Core Screening Algorithm
1. **Data Collection**: Fetch Volume Top 100 + Heat Top 100 stocks using pywencai (问财)
2. **Normalization**: Min-Max scaling to standardize rankings (0-100 scale)
3. **Scoring**: Weighted combination (volume: 0.5, heat: 0.5) with comprehensive scoring
4. **Filtering**: Exclude ST stocks, new listings (<60 days), apply price limits
5. **Momentum Calculation**: 25-day linear regression (slope × R²) using akshare historical data
6. **Visualization**: Interactive HTML reports with PyEcharts/Recharts

### Project Structure

```
StockGuru/
├── cli.py                          # Standalone CLI entry point
├── config.py                       # Core screening parameters
├── stockguru-web/                  # Full web application (v2.0.0)
│   ├── backend/
│   │   ├── app/main.py            # FastAPI application
│   │   ├── app/api/               # REST API endpoints
│   │   ├── app/services/          # Business logic layer
│   │   ├── app/core/config.py     # Configuration management
│   │   └── requirements.txt       # 106 Python dependencies
│   └── database/                   # Supabase schemas and migrations
├── frontend/                       # Next.js application
│   ├── app/page.tsx               # Main dashboard
│   ├── components/                # React components
│   └── package.json               # Next.js 15.5.5 + React 19.1.0
├── tests/                          # Manual test scripts
├── docs/                           # Comprehensive documentation
├── scripts/                        # Deployment and utility scripts
└── output/                         # Generated reports
```

### Key Configuration (config.py)

**Screening Parameters**:
- `VOLUME_TOP_N`: 100 (volume ranking range)
- `HEAT_TOP_N`: 100 (heat ranking range)
- `MOMENTUM_DAYS`: 25 (momentum calculation period)
- `VOLUME_WEIGHT`: 0.5, `HEAT_WEIGHT`: 0.5 (scoring weights)

**Filtering Rules**:
- Exclude ST stocks, new listings (<60 days)
- Price limits: `MAX_RISE_RATIO`: 0.11 (11% daily limit)
- Market cap and liquidity requirements

**Data Sources**:
- pywencai: Stock heat/volume rankings from 问财
- akshare: Historical K-line data and technical indicators
- Supabase: PostgreSQL for data persistence (web version)

### API Endpoints (FastAPI)

**Stock Screening**:
- `POST /api/screening/run` - Execute stock screening
- `GET /api/screening/results/{id}` - Get screening results
- `GET /api/screening/history` - Historical screening data

**Stock Data**:
- `GET /api/stocks/{code}/kline` - K-line historical data
- `GET /api/stocks/{code}/indicators` - Technical indicators
- `GET /api/stocks/market-data` - Real-time market data

### Frontend Components (Next.js)

**Main Dashboard** (`app/page.tsx`):
- Stock screening results table
- Momentum score visualization
- Interactive K-line charts using Recharts
- Real-time data updates via Supabase

**Key Technologies**:
- Next.js 15.5.5 with App Router
- React 19.1.0 with TypeScript
- Tailwind CSS v4 for styling
- Recharts for data visualization
- Supabase for real-time data

### Important Implementation Notes

1. **Chinese Market Focus**: A-share market with Chinese stock codes (600***, 000***, 300***)
2. **Data Dependencies**: Heavy reliance on pywencai and akshare APIs - monitor for API changes
3. **No Formal Testing**: Manual tests only - consider pytest for new features
4. **Fixed Date Issue**: Legacy CLI uses hardcoded dates - web version uses dynamic dates
5. **Error Handling**: Basic logging to files - improve error handling for production
6. **Performance**: No caching mechanism for API calls - consider Redis for optimization

### Common Development Tasks

**Adding New Screening Criteria**:
1. Update `config.py` with new parameters
2. Modify filtering logic in backend services
3. Update API schemas if needed
4. Test with both CLI and web interfaces

**Modifying Momentum Calculation**:
1. Update `momentum_calculator.py` (CLI) or backend service
2. Adjust calculation periods in configuration
3. Test with historical data validation

**Adding Technical Indicators**:
1. Extend momentum calculation modules
2. Update chart generation (PyEcharts for CLI, Recharts for web)
3. Add corresponding API endpoints

**Debugging Data Issues**:
1. Check pywencai/akshare connectivity
2. Verify data formats in fetcher modules
3. Review logs in backend or `stockguru.log` (CLI)
4. Use test scripts in `tests/` directory