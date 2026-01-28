# Labor Supply-Demand Gap Project Summary

**Created:** January 2026
**Live App:** https://labor-gap-explorer.streamlit.app
**GitHub Repo:** https://github.com/gregcwright-blip/labor-gap-explorer

---

## Project Overview

This project builds an interactive tool for exploring projected labor shortages by occupation and geography, with policy scenario modeling. It shifts the focus from documenting current shortages to a forward-looking supply/demand gap framework.

### Core Concept

```
Gap = Projected Demand - Projected Supply

Where:
- Demand = Current Employment × Growth Rate + Replacement Needs (retirements + separations)
- Supply = Current Workers - Exits + Training Inflows + Other Inflows
```

---

## What Was Built

### Data Pipeline

| Script | Purpose | Output |
|--------|---------|--------|
| `download_bls_oes.py` | Download current employment from BLS OES | `oes_employment_state.csv` |
| `download_state_projections.py` | Get state/national growth projections | `occupation_growth_rates.csv` |
| `build_demand_projections.py` | Project 5-year demand by occupation × CZ | `demand_projections_cz.csv` |
| `build_supply_projections.py` | Project 5-year supply by occupation × CZ | `supply_projections_cz.csv` |
| `calculate_gap.py` | Combine into gap estimates with policy scenarios | `gap_projections_cz.csv` |

### Interactive Dashboard

| File | Purpose |
|------|---------|
| `labor-gap-app/app.py` | Streamlit dashboard (deployed) |
| `gap_explorer.html` | Standalone HTML/JS version (no server needed) |

### Features

1. **Occupation selector** - Target occupations (nurses, electricians, truck drivers, etc.)
2. **State filter** - National or state-specific views
3. **Key metrics** - Current employment, 5-year demand, supply, and gap
4. **Visualizations**:
   - Supply vs demand bar chart
   - Gap decomposition waterfall
   - State choropleth map
   - Top shortage occupations comparison
   - Training adequacy gauge
5. **Policy scenario modeling**:
   - Training expansion (1-3x multiplier)
   - Retirement delay (0-5 years)
   - Retention improvement (0-30%)

---

## Data Sources

| Data | Source | Geographic Level |
|------|--------|------------------|
| Current employment | ACS via IPUMS (your existing data) | Commuting Zone |
| Age distributions | ACS (replacement_ratios_cz.csv) | Commuting Zone |
| Training completions | IPEDS (training_capacity_cz.csv) | Commuting Zone |
| Growth projections | BLS Employment Projections 2024-2034 | National (applied to states) |
| Separation rates | BLS methodology | Occupation |

---

## Target Occupations

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

### 1. Data Improvements

- [ ] **Add apprenticeship data** - Download from RAPIDS (apprenticeship.gov) for electricians, plumbers, HVAC
- [ ] **Add 4-year nursing programs** - IPEDS data for BSN completions
- [ ] **Get actual state projections** - Download from Projections Central for each state
- [ ] **Integrate Lightcast data** - Job postings for real-time demand signals
- [ ] **Add wage data** - Show wage trends alongside gaps

### 2. Model Calibration

- [ ] **Calibrate exit rates** - Use BLS separations data to validate
- [ ] **Calibrate training-to-employment rates** - Compare completions to actual job placements
- [ ] **Add wage elasticity** - Model how wage increases affect supply
- [ ] **Validate against historical data** - Backtest projections against actual outcomes

### 3. App Enhancements

- [ ] **Add more visualizations**:
  - Time series of gap projections
  - Comparison across metros within a state
  - Demographic breakdowns (age, race, gender)
- [ ] **Download/export features** - Let users download filtered data as CSV
- [ ] **Custom scenarios** - Let users input specific policy numbers
- [ ] **Printable reports** - Generate PDF summaries for specific occupation × state
- [ ] **Mobile optimization** - Improve layout for phone/tablet viewing

### 4. Deployment Enhancements

- [ ] **Custom domain** - Point labor-gap.theipdhub.com to the app
- [ ] **Add authentication** - Restrict access if needed
- [ ] **Embed in website** - Add iframe to theipdhub.com
- [ ] **API endpoint** - Expose data via REST API for other tools

### 5. Research Extensions

- [ ] **Immigration exposure layer** - Add immigrant workforce share analysis
- [ ] **Regional competitiveness** - Compare training capacity across regions
- [ ] **Scenario comparison** - Side-by-side comparison of multiple policy packages
- [ ] **Cost-benefit analysis** - Estimate cost per gap-worker reduced for each policy

---

## File Locations

```
/Users/gregorywright/Library/CloudStorage/Dropbox/Projects/Bahar/
├── labor-gap-app/                    # Deployed Streamlit app
│   ├── app.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── gap_projections_cz.csv
│   │   └── gap_projections_state.csv
│   └── .streamlit/config.toml
├── gap_explorer.html                 # Standalone HTML version
├── build_demand_projections.py       # Demand projection pipeline
├── build_supply_projections.py       # Supply projection pipeline
├── calculate_gap.py                  # Gap calculation + scenarios
├── download_bls_oes.py               # BLS data download
├── download_state_projections.py     # State projections download
├── replacement_ratios_cz.csv         # Your existing supply-side data
├── training_capacity_cz.csv          # Your existing training data
└── regional_labor_shortage_data_summary.md  # Original methodology doc
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

## Contact / Resources

- **Streamlit Cloud Dashboard:** https://share.streamlit.io
- **BLS Employment Projections:** https://www.bls.gov/emp/
- **Projections Central:** https://projectionscentral.org/
- **IPEDS Data:** https://nces.ed.gov/ipeds/

---

*Last updated: January 26, 2026*
