# Labor Shortage Explorer - Project Summary

**Created:** January 2026
**Live App:** https://labor-gap-explorer.streamlit.app
**GitHub Repo:** https://github.com/gregcwright-blip/labor-gap-explorer

---

## Project Overview

An interactive tool for exploring projected labor shortages by occupation and geography, with policy scenario modeling. The app shows 5-year supply/demand gaps and lets users model the impact of policy interventions.

### Core Concept

```
Gap = Projected Demand - Projected Supply

Where:
- Demand = Current Employment × Growth Rate + Replacement Needs (retirements + separations)
- Supply = Current Workers - Exits + Training Inflows + Other Inflows
```

---

## App Features

### Sidebar Controls

**Filters:**
- Occupation selector (8 key shortage occupations or browse all ~400)
- Geography filter (All States or specific state)

**Policy Scenarios:**
- Training Expansion (1-3x multiplier)
- Retirement Delay (0-5 years)
- Retention Improvement (0-30%)

### Main Dashboard

**Key Metrics (update in real-time with policy changes):**
- Current Employment
- 5-Year Projected Demand
- 5-Year Projected Supply
- Shortage Gap (red unless surplus, then green)

**Views:**
1. **Overview** - Supply vs demand bar chart, gap decomposition waterfall, training adequacy gauge
2. **Geography** - State choropleth map with dynamic color scaling, state details table
3. **Compare** - Top 10 shortage occupations bar chart

**Policy Impact Banner** - Shows gap reduction when policy levers are adjusted

---

## Key Shortage Occupations

| OCC Code | Occupation | 5-Year Gap | Key Issue |
|----------|------------|------------|-----------|
| 3130 | Registered Nurses | 3.2M | Training bottleneck, aging workforce |
| 3600 | Home Health Aides | 3.9M | High turnover, low wages |
| 6230 | Electricians | 932K | Apprenticeship capacity |
| 7315 | HVAC Mechanics | 358K | Infrastructure demand |
| 6440 | Plumbers | 440K | Licensing requirements |
| 8140 | Welders | 533K | Manufacturing demand |
| 9130 | Truck Drivers | 4.2M | Aging, CDL requirements |
| 5120 | Bookkeeping Clerks | 1.2M | Automation offset |

---

## Data Pipeline

| Script | Purpose | Output |
|--------|---------|--------|
| `download_bls_oes.py` | Download current employment from BLS OES | `oes_employment_state.csv` |
| `download_state_projections.py` | Get state/national growth projections | `occupation_growth_rates.csv` |
| `build_demand_projections.py` | Project 5-year demand by occupation × CZ | `demand_projections_cz.csv` |
| `build_supply_projections.py` | Project 5-year supply by occupation × CZ | `supply_projections_cz.csv` |
| `calculate_gap.py` | Combine into gap estimates with policy scenarios | `gap_projections_cz.csv` |

---

## Data Sources

| Data | Source | Geographic Level |
|------|--------|------------------|
| Current employment | ACS via IPUMS | Commuting Zone |
| Age distributions | ACS (replacement_ratios_cz.csv) | Commuting Zone |
| Training completions | IPEDS (training_capacity_cz.csv) | Commuting Zone |
| Growth projections | BLS Employment Projections 2024-2034 | National (applied to states) |
| Separation rates | BLS methodology | Occupation |

---

## Technical Implementation

### Stack
- **Frontend:** Streamlit
- **Visualization:** Plotly
- **Data:** Pandas, NumPy
- **Deployment:** Streamlit Cloud (auto-deploys from GitHub)

### Key Design Decisions
- Policy sliders in sidebar for easy access
- Metrics update in real-time when policy levers change
- Dynamic color scaling on map to show variation within actual data range
- Radio button view selector (persists selection on rerun)
- Clean, modern UI with Inter font and subtle styling

---

## Updating the App

```bash
cd /Users/gregorywright/Library/CloudStorage/Dropbox/Projects/Bahar/labor-gap-app

# Make changes to app.py or data files, then:
git add -A
git commit -m "Description of changes"
git push
```

Streamlit Cloud auto-redeploys within ~1 minute.

---

## Known Limitations

### Training Data Gaps

The current training data only captures **community college completions**. Missing sources:

| Missing Source | Occupations Affected |
|----------------|---------------------|
| 4-year university programs | Nurses (BSN), Managers |
| Registered apprenticeships | Electricians, Plumbers, HVAC |
| CDL schools | Truck Drivers |
| Employer-sponsored training | Home Health Aides |
| On-the-job training | Many occupations |

**Impact:** Training adequacy ratios appear very low (0.3-3%), overstating the gap.

### Geographic Limitations

- BLS does not produce metro-level projections
- State projections applied uniformly within states
- Commuting zone boundaries may not align with labor markets

### Methodological Simplifications

- Exit rates based on national averages, not local demographics
- Policy lever impacts are estimated, not empirically calibrated
- No wage elasticity modeling (how wage changes affect supply)

---

## Possible Next Steps

### Data Improvements
- [ ] Add apprenticeship data from RAPIDS (apprenticeship.gov)
- [ ] Add 4-year nursing programs from IPEDS
- [ ] Get actual state projections from Projections Central
- [ ] Integrate Lightcast job postings for real-time demand signals
- [ ] Add wage data alongside gaps

### Model Calibration
- [ ] Calibrate exit rates using BLS separations data
- [ ] Calibrate training-to-employment rates
- [ ] Add wage elasticity modeling
- [ ] Validate against historical data

### App Enhancements
- [ ] Download/export filtered data as CSV
- [ ] Time series of gap projections
- [ ] Demographic breakdowns (age, race, gender)
- [ ] Mobile optimization

### Deployment
- [ ] Custom domain (labor-gap.theipdhub.com)
- [ ] Embed in theipdhub.com via iframe
- [ ] API endpoint for other tools

---

## File Structure

```
/Users/gregorywright/Library/CloudStorage/Dropbox/Projects/Bahar/
├── labor-gap-app/                    # Deployed Streamlit app
│   ├── app.py                        # Main application
│   ├── requirements.txt              # Python dependencies
│   ├── PROJECT_SUMMARY.md            # This file
│   ├── README.md                     # GitHub readme
│   ├── data/
│   │   ├── gap_projections_cz.csv    # Main data file
│   │   └── gap_projections_state.csv # State-level summary
│   └── .streamlit/config.toml        # Streamlit config
├── build_demand_projections.py       # Demand projection pipeline
├── build_supply_projections.py       # Supply projection pipeline
├── calculate_gap.py                  # Gap calculation + scenarios
├── replacement_ratios_cz.csv         # Supply-side data
└── training_capacity_cz.csv          # Training data
```

---

## Running Locally

```bash
# Activate virtual environment
cd /Users/gregorywright/Library/CloudStorage/Dropbox/Projects/Bahar
source venv/bin/activate

# Run Streamlit app
streamlit run labor-gap-app/app.py

# Or run the data pipeline
python3 build_demand_projections.py
python3 build_supply_projections.py
python3 calculate_gap.py
```

---

## Resources

- **Streamlit Cloud Dashboard:** https://share.streamlit.io
- **BLS Employment Projections:** https://www.bls.gov/emp/
- **Projections Central:** https://projectionscentral.org/
- **IPEDS Data:** https://nces.ed.gov/ipeds/

---

*Last updated: January 27, 2026*
