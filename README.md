# Labor Supply-Demand Gap Explorer

Interactive dashboard for exploring projected labor shortages by occupation and geography, with policy scenario modeling.

## Features

- **Occupation Selection**: View gaps for target occupations (nurses, electricians, truck drivers, etc.)
- **Geographic Filtering**: National view or drill down by state
- **Interactive Visualizations**: Supply vs demand charts, choropleth maps, waterfall decomposition
- **Policy Scenario Modeling**: Adjust training expansion, retirement timing, and retention rates to see projected impact on labor gaps

## Data Sources

- **Employment**: American Community Survey (ACS) via IPUMS
- **Training**: IPEDS community college completions
- **Projections**: BLS Employment Projections (2024-2034)

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Methodology

The gap is calculated as:

```
Gap = Projected Demand - Projected Supply

Where:
- Projected Demand = Current Employment × (1 + Growth Rate)^5 + Replacement Needs
- Projected Supply = Current Workers - Exits + Training Inflows + Other Inflows
```

Policy levers adjust:
- **Training Expansion**: Multiplies training program completions
- **Retirement Delay**: Reduces exit rates for older workers
- **Retention Improvement**: Reduces occupation transfer exits

## Note

Training data currently includes community college completions only. Gaps may be overstated due to missing training sources (apprenticeships, 4-year programs, on-the-job training).
