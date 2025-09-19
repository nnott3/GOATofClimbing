# Climbing Competition Analysis Dashboard

Data pipeline and analytics dashboard for IFSC climbing competitions with ELO ratings and performance analysis.

## Features

- **Data Pipeline**: Automated scraping from IFSC API with incremental updates
- **ELO Ratings**: Historical rating calculations and progression tracking
- **Analytics Dashboard**: Country performance, athlete comparisons, career analysis

## Quick Start

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run data pipeline**
```bash
cd utils
python main.py
```

3. **Launch dashboard**
```bash
streamlit run app.py
```

## Project Structure

```
├── Data/aggregate_data/           # Processed competition data
├── Elo_Data/                      # ELO rating history
├── utils/
│   ├── main.py                    # Data pipeline orchestrator
│   ├── scraper_init.py            # IFSC API scraper
│   ├── data_aggregator.py         # Data processing
│   ├── elo_scoring.py             # ELO calculations
│   └── streamlit_*.py             # Dashboard modules
└── app.py                         # Main dashboard
```

## Dashboard Tabs

- **ELO Rankings**: Interactive ratings with historical charts
- **Overview**: Competition trends and participation statistics  
- **Countries**: Performance analysis with growth tracking
- **Athletes**: Individual analysis, head-to-head comparisons, career progression

## Key Components

**IFSCDataManager**: Orchestrates scraping, aggregation, and ELO updates
**ELOCalculator**: Rating system with incremental updates (K=32, initial=1500)
**Streamlit Modules**: Interactive analytics for different aspects

## Configuration

Create `.env` file for API settings:
```
IFSC_HEADERS={"User-Agent": "your-user-agent"}
```

## Usage

```python
from utils.main import IFSCDataManager

# Initial setup
manager = IFSCDataManager()
manager.initial_data_fetch()

# Regular updates  
manager.update_existing_data()
```