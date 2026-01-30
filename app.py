"""
Labor Shortage Explorer
=======================
Interactive dashboard for exploring projected labor shortages by occupation and geography,
with policy scenario modeling.

V2.1: Fixed employment scaling (divided by 5 for pooled ACS years).
      Uses 22 occupation groups and 5 age bins for more reliable estimates.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Labor Market Tightness Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: #0B0D11;
        font-family: 'Inter', sans-serif;
    }

    section[data-testid="stSidebar"] {
        background: #1A1D24;
        border-right: 1px solid #2D3748;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #A0AEC0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 1.5rem;
    }

    .header {
        margin-bottom: 1rem;
        padding: 1rem 0;
    }

    .header h1 {
        font-size: 2rem;
        font-weight: 800;
        color: #FFA726;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.03em;
    }

    .header p {
        font-size: 0.95rem;
        color: #A0AEC0;
        margin: 0;
        font-weight: 400;
    }

    .chart-card {
        background: #1A1D24;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2D3748;
        margin-bottom: 1rem;
    }

    .chart-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #E0E0E0;
        margin-bottom: 1rem;
    }

    .county-panel {
        background: #1A1D24;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #FFA726;
        margin-bottom: 1rem;
    }

    .county-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFA726;
        margin-bottom: 0.5rem;
    }

    .county-subtitle {
        font-size: 0.8rem;
        color: #A0AEC0;
        margin-bottom: 1rem;
    }

    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: #0B0D11;
        border-radius: 8px;
        padding: 1rem;
        flex: 1;
        border: 1px solid #2D3748;
    }

    .metric-label {
        font-size: 0.7rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #E0E0E0;
    }

    .metric-value.shortage { color: #F97316; }
    .metric-value.surplus { color: #10B981; }

    .policy-impact {
        background: linear-gradient(135deg, #064E3B 0%, #065F46 100%);
        border: 1px solid #10B981;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        color: #A7F3D0;
        font-size: 0.875rem;
        font-weight: 500;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    .data-source {
        font-size: 0.7rem;
        color: #718096;
        margin-top: 1rem;
    }

    /* Methods tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: #1A1D24;
        padding: 0.5rem 1rem;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #A0AEC0;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        color: #FFA726;
    }

    /* Markdown tables in Methods */
    .stMarkdown table {
        background: #1A1D24;
        border-collapse: collapse;
        margin: 1rem 0;
        width: 100%;
    }

    .stMarkdown th {
        background: #2D3748;
        color: #E0E0E0;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        border: 1px solid #4A5568;
    }

    .stMarkdown td {
        padding: 0.75rem;
        border: 1px solid #2D3748;
        color: #E0E0E0;
    }

    .stMarkdown tr:hover td {
        background: #2D3748;
    }

    .stMarkdown code {
        background: #2D3748;
        color: #FFA726;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.875rem;
    }

    .stMarkdown pre {
        background: #1A1D24;
        border: 1px solid #2D3748;
        border-radius: 8px;
        padding: 1rem;
    }

    .stMarkdown h2 {
        color: #FFA726;
        margin-top: 2rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2D3748;
    }

    .stMarkdown h3 {
        color: #E0E0E0;
        margin-top: 1.5rem;
    }

    .stMarkdown hr {
        border: none;
        border-top: 1px solid #2D3748;
        margin: 2rem 0;
    }

    .stMarkdown a {
        color: #60A5FA;
    }

    .stMarkdown ul, .stMarkdown ol {
        color: #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

# Data path
try:
    DATA_DIR = Path(__file__).parent / "data"
except NameError:
    DATA_DIR = Path(".") / "data"

if not DATA_DIR.exists():
    DATA_DIR = Path(".") / "data"

# Occupation category groupings for sidebar organization
OCC_CATEGORIES = {
    "Healthcare": [
        "Healthcare Practitioners and Technical",
        "Healthcare Support"
    ],
    "Business & Office": [
        "Management",
        "Business and Financial Operations",
        "Office and Administrative Support",
        "Legal"
    ],
    "Technical & Science": [
        "Computer and Mathematical",
        "Architecture and Engineering",
        "Life, Physical, and Social Science"
    ],
    "Service": [
        "Food Preparation and Serving",
        "Personal Care and Service",
        "Protective Service",
        "Building and Grounds Cleaning and Maintenance",
        "Community and Social Service"
    ],
    "Trades & Production": [
        "Construction and Extraction",
        "Installation, Maintenance, and Repair",
        "Production",
        "Transportation and Material Moving"
    ],
    "Education & Creative": [
        "Education, Training, and Library",
        "Arts, Design, Entertainment, Sports, Media"
    ],
    "Sales & Agriculture": [
        "Sales and Related",
        "Farming, Fishing, and Forestry"
    ]
}


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_gap_data():
    """Load gap projections data."""
    filepath = DATA_DIR / "gap_projections_cz.csv"
    if filepath.exists():
        return pd.read_csv(filepath)
    else:
        st.error("Gap data not found.")
        return None


@st.cache_data
def load_crosswalk():
    """Load county-CZ crosswalk."""
    filepath = DATA_DIR / "county_cz_crosswalk.csv"
    if filepath.exists():
        return pd.read_csv(filepath)
    return None


@st.cache_data
def load_cz_centroids():
    """Load CZ centroid coordinates."""
    filepath = DATA_DIR / "cz_centroids.csv"
    if filepath.exists():
        return pd.read_csv(filepath)
    return None


@st.cache_data
def load_cz_geojson():
    """Load CZ boundary GeoJSON."""
    import json
    filepath = DATA_DIR / "cz_boundaries.geojson"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None


@st.cache_data
def load_entry_sources():
    """Load CZ-level entry sources data."""
    filepath = DATA_DIR / "cz_entry_sources.csv"
    if filepath.exists():
        return pd.read_csv(filepath)
    return None


@st.cache_data
def load_occ_entry_sources():
    """Load CZ × occupation entry sources data."""
    filepath = DATA_DIR / "cz_occ_entry_sources.csv"
    if filepath.exists():
        return pd.read_csv(filepath)
    return None


@st.cache_data
def get_occupation_summary(df):
    """Get occupation groups with their total gaps."""
    occ_summary = df.groupby('occ_group').agg({
        'stock_gap': 'sum',
        'total_emp': 'sum'
    }).reset_index()
    return occ_summary.sort_values('stock_gap', ascending=False)


@st.cache_data
def get_cz_data(gap_data, selected_occ):
    """Prepare CZ-level data for mapping."""
    centroids = load_cz_centroids()
    if centroids is None:
        return None

    # Filter by occupation if needed
    if selected_occ != "All Occupations":
        data = gap_data[gap_data['occ_group'] == selected_occ].copy()
    else:
        data = gap_data.copy()

    # Aggregate to CZ level
    cz_totals = data.groupby(['czone', 'cz_label', 'state_abbr']).agg({
        'stock_gap': 'sum',
        'total_emp': 'sum',
        'emp_projected': 'sum',
        'supply_projected': 'sum',
        'annual_training_inflows': 'sum',
        'annual_other_inflows': 'sum',
        'annual_total_exits': 'sum',
        # Weighted average of age shares
        'emp_55_64': 'sum',
        'emp_65_plus': 'sum',
    }).reset_index()

    # Calculate derived metrics
    cz_totals['gap_pct'] = (cz_totals['stock_gap'] / cz_totals['total_emp'] * 100).fillna(0)
    cz_totals['wage_pressure'] = (cz_totals['gap_pct'] / 0.7).clip(lower=0)
    cz_totals['share_55_plus'] = (cz_totals['emp_55_64'] + cz_totals['emp_65_plus']) / cz_totals['total_emp']
    cz_totals['exit_rate'] = cz_totals['annual_total_exits'] / cz_totals['total_emp']

    # Add centroid coordinates
    cz_data = cz_totals.merge(centroids, on='czone', how='left')

    return cz_data


# ============================================================================
# POLICY CALCULATIONS
# ============================================================================

def apply_policy_scenario(total_emp, baseline_gap, annual_exits, annual_training, annual_other,
                          share_55_plus, new_entrant_growth, retirement_delay, retention_improve):
    """
    Apply policy scenario to calculate adjusted gap.

    Uses BLS-calibrated rates:
    - Labor force exits: ~45% of total exits (retirement, disability, family)
    - Occupation transfers: ~55% of total exits (career changes)

    Policy effects:
    - New entrant growth: Increases labor force entrants (immigration, participation)
    - Retirement delay: Reduces labor force exit rate for 55+ workers
    - Retention improvement: Reduces occupation transfer rate
    """
    horizon = 5

    # Decompose exits into labor force exits and transfers
    # Based on BLS: 4.7% labor force exits, 5.7% transfers = 10.4% total
    labor_force_exit_share = 0.45
    transfer_share = 0.55

    annual_lf_exits = annual_exits * labor_force_exit_share
    annual_transfers = annual_exits * transfer_share

    # Policy 1: New entrant growth
    # Increases "other inflows" (new graduates, immigrants, labor force re-entrants)
    # A 10% increase means 10% more people entering the labor force for this occupation
    adj_other = annual_other * (1 + new_entrant_growth)

    # Policy 2: Retirement delay
    # Each year of delay reduces labor force exits for 55+ workers
    # 55+ workers have ~15% annual exit rate vs ~3% for younger workers
    # Delay shifts some of these exits into the future
    if retirement_delay > 0 and share_55_plus > 0:
        # Reduction in annual exits from delayed retirement
        # Assumes each year of delay reduces 55+ exit rate by ~15%
        retirement_reduction = min(retirement_delay * 0.15, 0.6)
        lf_exit_reduction = annual_lf_exits * share_55_plus * retirement_reduction
    else:
        lf_exit_reduction = 0

    # Policy 3: Retention improvement
    # Reduces occupation transfer rate (people switching occupations)
    transfer_reduction = annual_transfers * retention_improve

    # Calculate adjusted values
    adj_lf_exits = annual_lf_exits - lf_exit_reduction
    adj_transfers = annual_transfers - transfer_reduction
    adj_total_exits = adj_lf_exits + adj_transfers

    # Baseline supply change (should roughly match what's in the data)
    baseline_supply_change = (annual_training + annual_other - annual_exits) * horizon

    # Adjusted supply change with policies
    adj_supply_change = (annual_training + adj_other - adj_total_exits) * horizon

    # Gap reduction is the difference
    supply_increase = adj_supply_change - baseline_supply_change
    adj_gap = baseline_gap - supply_increase

    return adj_gap, supply_increase


# ============================================================================
# VISUALIZATIONS
# ============================================================================

def create_cz_map(cz_data, metric='tightness'):
    """Create CZ-level choropleth map with proper boundaries.

    Uses percentile-based coloring to show relative labor market tightness,
    highlighting which regions are tighter vs looser than average.
    """
    if cz_data is None or len(cz_data) == 0:
        return None

    # Load CZ GeoJSON
    cz_geojson = load_cz_geojson()
    if cz_geojson is None:
        return None

    # Prepare data
    cz_data = cz_data.copy()
    cz_data['czone'] = cz_data['czone'].astype(int)

    # Calculate tightness percentile (0-100 scale, higher = tighter labor market)
    # Based on gap_pct: positive gap = tight, negative gap = loose
    cz_data['tightness_percentile'] = cz_data['gap_pct'].rank(pct=True) * 100

    # Choose color column based on metric
    if metric == 'tightness':
        color_col = 'tightness_percentile'
        color_label = 'Tightness Percentile'
        # Full percentile range
        range_color = [0, 100]
    else:
        color_col = 'wage_pressure'
        color_label = 'Wage Pressure %'
        # Percentile-based range for wage pressure too
        p5 = cz_data[color_col].quantile(0.05)
        p95 = cz_data[color_col].quantile(0.95)
        range_color = [p5, p95]

    values = cz_data[color_col].dropna()
    if len(values) == 0:
        return None

    # Color scale: blue (loose) -> yellow (average) -> orange/red (tight)
    color_scale = [
        [0, '#3B82F6'],      # Blue - loose labor market
        [0.25, '#60A5FA'],   # Light blue
        [0.5, '#FDE68A'],    # Yellow - average
        [0.75, '#F97316'],   # Orange
        [1, '#DC2626']       # Red - tight labor market
    ]

    fig = px.choropleth_mapbox(
        cz_data,
        geojson=cz_geojson,
        locations='czone',
        featureidkey='properties.czone',
        color=color_col,
        color_continuous_scale=color_scale,
        range_color=range_color,
        mapbox_style="carto-darkmatter",
        zoom=3,
        center={"lat": 39.8, "lon": -98.6},
        opacity=0.75,
        hover_data={
            'cz_label': True,
            'state_abbr': True,
            'total_emp': ':,.0f',
            'gap_pct': ':+.1f',
            'tightness_percentile': ':.0f',
            'czone': False,
            color_col: False
        },
        labels={
            'cz_label': 'Region',
            'state_abbr': 'State',
            'total_emp': 'Employment',
            'gap_pct': 'Gap %',
            'tightness_percentile': 'Tightness'
        },
        custom_data=['czone']
    )

    fig.update_layout(
        paper_bgcolor='#0B0D11',
        plot_bgcolor='#0B0D11',
        margin=dict(t=10, b=10, l=10, r=10),
        height=500,
        coloraxis_colorbar=dict(
            title=dict(text=color_label, font=dict(color='#E0E0E0')),
            tickfont=dict(color='#E0E0E0'),
            len=0.6,
            thickness=12,
            bgcolor='#1A1D24'
        ),
        font=dict(color='#E0E0E0')
    )

    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def render_methods_tab():
    """Render the methodology documentation tab."""
    st.markdown("""
    <div class="header">
        <h1>Methodology</h1>
        <p>How we calculate labor supply, demand, and shortage projections</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ## Overview

    This dashboard shows **relative labor market tightness** across US commuting zones by comparing:
    - **Supply**: How many workers will be available in each occupation
    - **Demand**: How many workers employers will need

    **Gap = Projected Demand − Projected Supply**

    A positive gap indicates a tight labor market; a negative gap indicates a loose market.

    The map uses **percentile-based coloring** to show which regions are relatively tighter or looser than average, regardless of absolute gap sizes.

    ---

    ## Data Sources

    | Source | Used For | Years |
    |--------|----------|-------|
    | American Community Survey (ACS) | Current employment by age, occupation, geography | 2019-2023 (pooled) |
    | Bureau of Labor Statistics (BLS) | Employment projections, separation rates | 2024-2034 |
    | BLS OEWS | Validation of occupation distributions | May 2024 |

    ---

    ## Supply Projection Model

    We project labor supply using a cohort-based model with BLS-calibrated exit rates.

    ### Step 1: Current Employment by Age

    We extract employment counts for 5 age bins from ACS microdata:
    - 20-29, 30-44, 45-54, 55-64, 65+

    ### Step 2: Exit Rate Calculation

    Workers leave occupations through two channels:

    | Exit Type | Description | National Average |
    |-----------|-------------|------------------|
    | **Labor Force Exits** | Retirement, disability, family reasons | 4.7% annually |
    | **Occupation Transfers** | Switch to different occupation | 6.4% annually |
    | **Total Separations** | Sum of above | 11.1% annually |

    Exit rates vary by age (calibrated to BLS national data):

    | Age Group | Labor Force Exit | Occupation Transfer | Total |
    |-----------|------------------|---------------------|-------|
    | 20-29 | 2.5% | 12.0% | 14.5% |
    | 30-44 | 1.5% | 5.5% | 7.0% |
    | 45-54 | 2.5% | 4.0% | 6.5% |
    | 55-64 | 8.0% | 2.5% | 10.5% |
    | 65+ | 28.0% | 1.5% | 29.5% |

    Rates are adjusted by occupation using multipliers (high-turnover occupations like Food Prep: 1.35x; stable occupations like Healthcare Practitioners: 0.80x).

    ### Step 3: Inflow Calculation

    New workers enter occupations through:

    | Inflow Type | Rate | Description |
    |-------------|------|-------------|
    | **Immigration** | ~0.6% | Foreign-born workers arriving in US |
    | **Domestic Migration** | ~2.8% | Interstate and intercounty movers |
    | **Young Entrants** | ~5% | New labor force participants (ages 20-24) |
    | **Occupation Transfers In** | ~6.4% | Workers switching FROM other occupations |
    | **Labor Force Re-entrants** | ~0.6% | Workers returning after absence |

    These rates are measured from ACS migration and demographic data (see Labor Entry Sources section below).

    **Key insight**: High-turnover occupations have high exit rates AND high entry rates (they're "revolving doors"). We apply the same occupation multiplier to both exits and inflows.

    ### Step 4: Supply Projection Formula

    ```
    Supply(t+5) = Current Employment
                  − (Annual Exits × 5)
                  + (Annual Inflows × 5)
    ```

    ---

    ## Demand Projection Model

    Demand projections come from BLS 2024-2034 occupational employment projections, scaled to local geography using current employment shares.

    ### BLS Methodology

    BLS projects employment using:
    - Macroeconomic forecasts (GDP, productivity, demographics)
    - Industry-occupation matrices
    - Historical trends and expert judgment

    ### Geographic Allocation

    National BLS projections are allocated to commuting zones (CZs) proportional to current local employment in each occupation.

    ---

    ## Gap Calculation

    ### Employment Base Reconciliation

    ACS and BLS use different methodologies, resulting in different employment totals:
    - ACS employment: ~638M (includes self-employed, gig workers)
    - BLS employment: ~548M (payroll survey scope)

    We scale supply projections to match the BLS employment base to ensure apples-to-apples comparison.

    ### Final Gap

    ```
    Stock Gap = BLS Projected Employment − Scaled Supply Projection
    ```

    ### Tightness Percentile

    Since absolute gaps are small nationally, we rank CZs by gap % and display **percentile-based coloring**:
    - 0th percentile (blue) = Loosest labor market
    - 50th percentile (yellow) = Average
    - 100th percentile (red) = Tightest labor market

    ---

    ## Wage Pressure Estimate

    We estimate wage pressure using a simple labor market elasticity:

    ```
    Wage Pressure % = Gap % / 0.7
    ```

    This assumes a labor supply elasticity of 0.7 (a 1% wage increase attracts 0.7% more workers).

    ---

    ## Policy Scenario Model

    The dashboard allows you to model changes in immigration levels.

    **Immigration Scenario Box**

    When viewing a CZ detail, you'll see:
    1. **Current Immigration**: Annual immigration inflow (workers/year) calculated from ACS data
    2. **Adjustment Slider**: Directly adjust the number of immigrant workers per year
    3. **Impact Calculation**: Shows how the change affects the 5-year gap projection

    The model calculates:
    ```
    Current immigration = (Workforce × Recent immigration %) / 2
    Immigration change = New level − Current level
    5-year gap reduction = Immigration change × 5 years
    ```

    Example: If a CZ currently receives 500 immigrant workers/year and you increase to 750:
    - Immigration change: +250 workers/year
    - 5-year supply increase: +1,250 workers
    - Gap reduction: −1,250 (more supply = less shortage)

    ---

    ## Labor Entry Sources

    We track where workers come from using ACS migration and birthplace data (2019-2023 pooled):

    | Source | Measurement | National Average |
    |--------|-------------|------------------|
    | **Recent Immigration** | Foreign-born, arrived in past 2 years | ~0.6% of workforce |
    | **Interstate Migration** | Moved from different state (1-year) | ~0.4% of workforce |
    | **Intercounty Migration** | Moved from different county, same state | ~2.4% of workforce |
    | **Young Workers (20-24)** | Proxy for new labor force entrants | ~9.6% of workforce |

    These flows vary significantly by occupation:
    - **Farming**: 2.7% recent immigration (highest)
    - **Food Prep**: 25.6% young workers (highest turnover)
    - **Computer/Math**: 1.2% recent immigration (tech sector)

    ### Annual Flow Breakdown

    In the CZ detail view, we show how total worker inflows break down:

    | Component | Description |
    |-----------|-------------|
    | **Exits** | Workers leaving (retirements + transfers to other occupations) |
    | **Domestic Inflows** | Interstate/intercounty movers + young entrants + re-entrants |
    | **Immigration** | Foreign-born workers entering (adjustable via policy scenario) |
    | **Net Flow** | Total inflows − exits |

    The immigration component can be adjusted using the scenario slider to model policy changes.

    ---

    ## Occupation Groups

    We aggregate 401 detailed ACS occupations into 22 SOC major groups for statistical reliability:

    - Management
    - Business and Financial Operations
    - Computer and Mathematical
    - Architecture and Engineering
    - Life, Physical, and Social Science
    - Community and Social Service
    - Legal
    - Education, Training, and Library
    - Arts, Design, Entertainment, Sports, Media
    - Healthcare Practitioners and Technical
    - Healthcare Support
    - Protective Service
    - Food Preparation and Serving
    - Building and Grounds Cleaning and Maintenance
    - Personal Care and Service
    - Sales and Related
    - Office and Administrative Support
    - Farming, Fishing, and Forestry
    - Construction and Extraction
    - Installation, Maintenance, and Repair
    - Production
    - Transportation and Material Moving

    ---

    ## Geographic Units

    We use **commuting zones (CZs)** as the primary geographic unit:
    - 741 CZs covering the entire US
    - CZs are clusters of counties with strong commuting ties
    - Better captures local labor markets than state boundaries

    Counties are mapped to CZs for visualization.

    ---

    ## Data Validation: ACS vs OEWS

    We validated our ACS-based occupation distributions against BLS Occupational Employment and Wage Statistics (OEWS) May 2024 data.

    ### Comparison Results

    | Metric | Value |
    |--------|-------|
    | Correlation of occupation shares | 0.848 |
    | Mean absolute difference | 1.14 percentage points |

    ### Key Differences Explained

    | Occupation | ACS vs OEWS | Explanation |
    |------------|-------------|-------------|
    | **Management** | +5.8pp higher in ACS | ACS includes self-employed managers/owners; OEWS is payroll only |
    | **Food Prep/Serving** | −3.9pp lower in ACS | High-turnover payroll jobs better captured by employer survey |
    | **Healthcare Support** | −2.4pp lower in ACS | Same reason as Food Prep |
    | **Transportation** | −2.3pp lower in ACS | Trucking/logistics payroll jobs |

    ### Interpretation

    The high correlation (0.848) indicates our occupation distributions are reliable. The systematic differences reflect known methodological differences:

    - **ACS**: Household survey including self-employed, gig workers
    - **OEWS**: Employer survey of payroll jobs only

    These differences don't affect our analysis since we compare relative tightness across CZs using consistent ACS-based shares.

    ---

    ## Sample Size Analysis

    Our ACS data pools 5 years (2019-2023) for statistical reliability at the CZ level.

    | Metric | Value |
    |--------|-------|
    | Total CZ × occupation cells | 19,182 |
    | Mean sample size per cell | 570 observations |
    | Median sample size | 282 observations |
    | Cells with n < 100 | 19.1% (higher uncertainty) |

    Cells with fewer than 100 observations are flagged as having higher sampling error.

    ---

    ## Limitations

    1. **Projection uncertainty**: 5-year forecasts have substantial uncertainty
    2. **Local variation**: Some CZ-occupation cells have small sample sizes (see above)
    3. **Structural changes**: Model may not capture rapid shifts (AI, pandemics)
    4. **Wage response**: Actual wage changes depend on many factors beyond labor market tightness

    ---

    ## References

    - BLS Occupational Separations: [bls.gov/emp/documentation/separations.htm](https://www.bls.gov/emp/documentation/separations.htm)
    - BLS Employment Projections: [bls.gov/emp/](https://www.bls.gov/emp/)
    - BLS OEWS (Validation): [bls.gov/oes/](https://www.bls.gov/oes/)
    - ACS PUMS: [census.gov/programs-surveys/acs/microdata.html](https://www.census.gov/programs-surveys/acs/microdata.html)

    ---

    *Last updated: January 2026*
    """)


def main():
    # Initialize session state
    if 'selected_cz' not in st.session_state:
        st.session_state.selected_cz = None
    if 'selected_occ' not in st.session_state:
        st.session_state.selected_occ = "All Occupations"

    # Load data
    gap_data = load_gap_data()
    if gap_data is None:
        st.stop()

    # Get occupation summary
    occ_summary = get_occupation_summary(gap_data)
    total_gap = occ_summary['stock_gap'].sum()
    total_emp = occ_summary['total_emp'].sum()

    # Create main tabs
    tab_explorer, tab_methods = st.tabs(["Explorer", "Methods"])

    with tab_methods:
        render_methods_tab()

    with tab_explorer:
        render_explorer(gap_data, occ_summary, total_gap, total_emp)


def render_explorer(gap_data, occ_summary, total_gap, total_emp):
    """Render the main explorer view."""
    # Sidebar with hierarchical occupation list
    with st.sidebar:
        st.markdown("### Occupations")

        # All occupations option
        all_selected = st.session_state.selected_occ == "All Occupations"
        gap_str = f"+{total_gap/1e6:.0f}M" if total_gap >= 0 else f"{total_gap/1e6:.0f}M"
        if st.button(
            f"{'●' if all_selected else '○'} All Occupations  **{gap_str}**",
            key="all_occ",
            use_container_width=True
        ):
            st.session_state.selected_occ = "All Occupations"
            st.session_state.selected_cz = None
            st.rerun()

        # Hierarchical categories
        for category, occupations in OCC_CATEGORIES.items():
            cat_occs = occ_summary[occ_summary['occ_group'].isin(occupations)]
            cat_gap = cat_occs['stock_gap'].sum()
            gap_str = f"+{cat_gap/1e6:.1f}M" if cat_gap >= 0 else f"{cat_gap/1e6:.1f}M"

            with st.expander(f"{category}  **{gap_str}**"):
                for occ in occupations:
                    occ_row = occ_summary[occ_summary['occ_group'] == occ]
                    if len(occ_row) > 0:
                        occ_gap = occ_row['stock_gap'].values[0]
                        gap_str = f"+{occ_gap/1e6:.1f}M" if occ_gap >= 0 else f"{occ_gap/1e6:.1f}M"
                        is_selected = st.session_state.selected_occ == occ
                        short_name = occ[:25] + '...' if len(occ) > 25 else occ

                        if st.button(
                            f"{'●' if is_selected else '○'} {short_name}",
                            key=f"occ_{occ}",
                            use_container_width=True
                        ):
                            st.session_state.selected_occ = occ
                            st.session_state.selected_cz = None
                            st.rerun()

                        st.caption(f"   {gap_str}")

        st.markdown("---")
        st.markdown('<p class="data-source">Data: ACS, IPEDS, BLS 2024-2034</p>', unsafe_allow_html=True)

    # Main content
    selected_occ = st.session_state.selected_occ

    # Header
    st.markdown(f"""
    <div class="header">
        <h1>Labor Market Tightness Explorer</h1>
        <p>Click on any region to explore policy scenarios • Showing: {selected_occ}</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if a CZ is selected
    if st.session_state.selected_cz:
        render_cz_detail(gap_data, selected_occ)
    else:
        render_national_view(gap_data, selected_occ)


def render_national_view(gap_data, selected_occ):
    """Render the national map view."""
    # Metric toggle
    metric_toggle = st.radio(
        "METRIC",
        ["Market Tightness", "Wage Pressure"],
        horizontal=True,
        key="metric_toggle",
        label_visibility="collapsed"
    )
    metric_type = 'tightness' if metric_toggle == "Market Tightness" else 'wage'

    # Get CZ data
    cz_data = get_cz_data(gap_data, selected_occ)

    # Create map
    if cz_data is not None:
        map_fig = create_cz_map(cz_data, metric=metric_type)
        if map_fig:
            clicked = st.plotly_chart(
                map_fig,
                use_container_width=True,
                config={'displayModeBar': False},
                on_select="rerun",
                key="cz_map"
            )

            # Handle click events
            if clicked and clicked.selection and clicked.selection.points:
                point = clicked.selection.points[0]
                # customdata contains [czone] from the choropleth
                if 'customdata' in point and point['customdata']:
                    clicked_cz = point['customdata'][0]
                    st.session_state.selected_cz = int(clicked_cz)
                    st.rerun()
                elif 'location' in point:
                    # Fallback to location (czone_str)
                    clicked_cz = point['location']
                    st.session_state.selected_cz = int(clicked_cz)
                    st.rerun()

    # Summary stats
    if selected_occ == "All Occupations":
        filtered = gap_data
    else:
        filtered = gap_data[gap_data['occ_group'] == selected_occ]

    total_emp = filtered['total_emp'].sum()
    total_gap = filtered['stock_gap'].sum()
    total_exits = filtered['annual_total_exits'].sum()
    total_training = filtered['annual_training_inflows'].sum()
    gap_pct = total_gap / total_emp * 100 if total_emp > 0 else 0
    exit_rate = total_exits / total_emp * 100 if total_emp > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Employment", f"{total_emp/1e6:.1f}M")
    with col2:
        tightness_label = "Tight" if total_gap > 0 else "Loose"
        st.metric(f"Market: {tightness_label}", f"{abs(total_gap)/1e6:.1f}M gap")
    with col3:
        st.metric("Gap %", f"{gap_pct:+.1f}%")
    with col4:
        st.metric("Exit Rate", f"{exit_rate:.1f}%/yr")
    with col5:
        wage_pressure = gap_pct / 0.7
        st.metric("Wage Pressure", f"{wage_pressure:+.1f}%")


def create_cz_mini_map(czone, tightness_pct):
    """Create a small map showing just the selected CZ shape."""
    cz_geojson = load_cz_geojson()
    if cz_geojson is None:
        return None

    # Find the feature for this CZ
    cz_feature = None
    for feature in cz_geojson['features']:
        if feature['properties']['czone'] == czone:
            cz_feature = feature
            break

    if cz_feature is None:
        return None

    # Create a GeoJSON with just this CZ
    single_cz_geojson = {
        'type': 'FeatureCollection',
        'features': [cz_feature]
    }

    # Get bounds for centering
    coords = []
    geom = cz_feature['geometry']
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        for poly in geom['coordinates']:
            coords.extend(poly[0])

    if coords:
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        center_lon = (min(lons) + max(lons)) / 2
        center_lat = (min(lats) + max(lats)) / 2
        # Calculate zoom based on extent
        lon_range = max(lons) - min(lons)
        lat_range = max(lats) - min(lats)
        extent = max(lon_range, lat_range)
        if extent > 5:
            zoom = 4
        elif extent > 2:
            zoom = 5
        elif extent > 1:
            zoom = 6
        else:
            zoom = 7
    else:
        center_lon, center_lat, zoom = -98.6, 39.8, 4

    # Color based on tightness percentile
    # Blue (loose) -> Yellow (average) -> Red (tight)
    if tightness_pct <= 50:
        # Blue to yellow
        t = tightness_pct / 50
        r = int(59 + (253 - 59) * t)
        g = int(130 + (230 - 130) * t)
        b = int(246 + (138 - 246) * t)
    else:
        # Yellow to red
        t = (tightness_pct - 50) / 50
        r = int(253 + (220 - 253) * t)
        g = int(230 + (38 - 230) * t)
        b = int(138 + (38 - 138) * t)
    color = f'rgb({r},{g},{b})'

    # Create simple choropleth
    fig = go.Figure(go.Choroplethmapbox(
        geojson=single_cz_geojson,
        locations=[czone],
        featureidkey='properties.czone',
        z=[tightness_pct],
        colorscale=[[0, color], [1, color]],
        showscale=False,
        marker_opacity=0.8,
        marker_line_width=2,
        marker_line_color='#FFA726'
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=zoom,
            center={"lat": center_lat, "lon": center_lon},
        ),
        paper_bgcolor='#1A1D24',
        plot_bgcolor='#1A1D24',
        margin=dict(t=0, b=0, l=0, r=0),
        height=200,
    )

    return fig


def render_cz_detail(gap_data, selected_occ):
    """Render the CZ detail view with immigration policy scenario."""
    czone = st.session_state.selected_cz
    cz_data = get_cz_data(gap_data, selected_occ)

    if cz_data is None:
        st.error("CZ data not available")
        return

    cz_row = cz_data[cz_data['czone'] == czone]
    if len(cz_row) == 0:
        st.warning("Commuting zone not found")
        st.session_state.selected_cz = None
        st.rerun()
        return

    cz = cz_row.iloc[0]

    # Calculate tightness percentile for this CZ
    tightness_pct = cz_data['gap_pct'].rank(pct=True)[cz_row.index[0]] * 100

    # Back button
    if st.button("← Back to National Map", key="back_btn"):
        st.session_state.selected_cz = None
        st.rerun()

    # CZ header with mini-map
    header_col1, header_col2 = st.columns([1, 2])

    with header_col1:
        mini_map = create_cz_mini_map(czone, tightness_pct)
        if mini_map:
            st.plotly_chart(mini_map, use_container_width=True, config={'displayModeBar': False})

    with header_col2:
        state = cz.get('state_abbr', '')
        tightness_label = "Tight" if cz['gap_pct'] > 0 else "Loose"

        st.markdown(f"""
        <div class="county-panel" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div class="county-title">{state}</div>
            <div class="county-subtitle">{selected_occ}</div>
            <div style="margin-top: 0.5rem; color: #A0AEC0; font-size: 0.85rem;">
                Tightness: <strong>{tightness_pct:.0f}th percentile</strong> ({tightness_label})
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Extract metrics from CZ data
    total_emp = cz['total_emp']
    baseline_gap = cz['stock_gap']
    annual_other = cz.get('annual_other_inflows', 0) or 0
    annual_exits = cz.get('annual_total_exits', 0) or 0
    exit_rate = cz.get('exit_rate', 0.10) or 0.10

    # =========================================================================
    # SECTION 1: Historical Labor Entry Sources
    # =========================================================================
    st.markdown("### Where Workers Come From (2019-2023)")
    st.markdown("""
    <div style="color: #A0AEC0; font-size: 0.85rem; margin-bottom: 1rem;">
        Historical data showing the sources of labor supply in this region.
        These flows feed into the "Other Inflows" used in projections.
    </div>
    """, unsafe_allow_html=True)

    # Load entry sources data based on occupation filter
    entry = None
    nat_immig = nat_interstate = nat_intercounty = nat_young = 0

    if selected_occ != "All Occupations":
        entry_data = load_occ_entry_sources()
        if entry_data is not None:
            entry_row = entry_data[(entry_data['czone'] == czone) &
                                    (entry_data['occ_group'] == selected_occ)]
            if len(entry_row) > 0:
                entry = entry_row.iloc[0]
            # National averages for this occupation
            nat_occ = entry_data[entry_data['occ_group'] == selected_occ]
            nat_total = nat_occ['total_emp'].sum()
            if nat_total > 0:
                nat_immig = nat_occ['recent_immigrants'].sum() / nat_total * 100
                nat_interstate = nat_occ['interstate_movers'].sum() / nat_total * 100
                nat_intercounty = nat_occ['intercounty_movers'].sum() / nat_total * 100
                nat_young = nat_occ['young_entrants'].sum() / nat_total * 100
    else:
        entry_data = load_entry_sources()
        if entry_data is not None:
            entry_row = entry_data[entry_data['czone'] == czone]
            if len(entry_row) > 0:
                entry = entry_row.iloc[0]
            # National averages
            nat_total = entry_data['total_emp'].sum()
            if nat_total > 0:
                nat_immig = entry_data['recent_immigrants'].sum() / nat_total * 100
                nat_interstate = entry_data['interstate_movers'].sum() / nat_total * 100
                nat_intercounty = entry_data['intercounty_movers'].sum() / nat_total * 100
                nat_young = entry_data['young_entrants'].sum() / nat_total * 100

    # Calculate immigration inflow from entry sources
    if entry is not None:
        pct_immig = entry.get('pct_recent_immigrants', 0) or 0
        pct_interstate = entry.get('pct_interstate_movers', 0) or 0
        pct_intercounty = entry.get('pct_intercounty_movers', 0) or 0
        pct_young = entry.get('pct_young_entrants', 0) or 0
        pct_foreign = entry.get('pct_foreign_born', 0) or 0

        # Calculate actual annual immigration inflow
        # pct_immig is % of workforce who are recent immigrants
        # To convert to annual inflow: workforce × pct_immig / 2 (since it's 2-year window)
        annual_immigration = (total_emp * pct_immig / 100) / 2
    else:
        pct_immig = pct_interstate = pct_intercounty = pct_young = pct_foreign = 0
        annual_immigration = annual_other * 0.05  # Default 5% of inflows

    # Show entry sources in a compact row
    entry_col1, entry_col2, entry_col3, entry_col4 = st.columns(4)

    with entry_col1:
        delta_immig = f"{pct_immig - nat_immig:+.2f}pp" if entry is not None else None
        st.metric("Immigration", f"{pct_immig:.2f}%", delta=delta_immig,
                  help="Share who immigrated in past 2 years")

    with entry_col2:
        delta_interstate = f"{pct_interstate - nat_interstate:+.2f}pp" if entry is not None else None
        st.metric("Interstate", f"{pct_interstate:.2f}%", delta=delta_interstate,
                  help="Moved from another state (1-year)")

    with entry_col3:
        delta_intercounty = f"{pct_intercounty - nat_intercounty:+.2f}pp" if entry is not None else None
        st.metric("Intercounty", f"{pct_intercounty:.2f}%", delta=delta_intercounty,
                  help="Moved from another county (1-year)")

    with entry_col4:
        delta_young = f"{pct_young - nat_young:+.2f}pp" if entry is not None else None
        st.metric("Young (20-24)", f"{pct_young:.1f}%", delta=delta_young,
                  help="Share aged 20-24 (new entrants)")

    # =========================================================================
    # SECTION 2: Immigration Component Box
    # =========================================================================
    st.markdown("### Immigration Scenario")

    # Create a styled box for the immigration component
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1A1D24 0%, #252A34 100%);
                border-radius: 12px; padding: 1.5rem; margin: 1rem 0;
                border: 1px solid #3B82F6;">
    """, unsafe_allow_html=True)

    immig_col1, immig_col2 = st.columns([1, 2])

    with immig_col1:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="color: #A0AEC0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">
                Current Immigration
            </div>
            <div style="color: #3B82F6; font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">
                {annual_immigration:,.0f}
            </div>
            <div style="color: #718096; font-size: 0.85rem;">
                workers/year
            </div>
            <div style="color: #A0AEC0; font-size: 0.75rem; margin-top: 0.5rem;">
                ({pct_immig:.2f}% of workforce)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with immig_col2:
        st.markdown("""
        <div style="color: #E0E0E0; font-size: 0.9rem; margin-bottom: 0.75rem;">
            <strong>Adjust immigration level:</strong>
        </div>
        """, unsafe_allow_html=True)

        # Slider to adjust immigration - shows actual worker counts
        max_immigration = int(annual_immigration * 3) if annual_immigration > 0 else 1000
        min_immigration = 0
        step = max(1, int(annual_immigration / 20)) if annual_immigration > 0 else 10

        new_immigration = st.slider(
            "Annual immigration (workers/year)",
            min_value=min_immigration,
            max_value=max_immigration,
            value=int(annual_immigration),
            step=step,
            format="%d",
            label_visibility="collapsed"
        )

        # Show the change
        immigration_delta = new_immigration - annual_immigration
        pct_change = (immigration_delta / annual_immigration * 100) if annual_immigration > 0 else 0

        if immigration_delta != 0:
            change_color = "#10B981" if immigration_delta > 0 else "#EF4444"
            st.markdown(f"""
            <div style="color: {change_color}; font-size: 0.9rem; margin-top: 0.5rem;">
                {immigration_delta:+,.0f} workers/year ({pct_change:+.0f}% change)
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Calculate policy impact
    policy_active = immigration_delta != 0

    if policy_active:
        # Over 5 years, this changes supply
        supply_change_5yr = immigration_delta * 5

        # Gap decreases by this amount (more supply = less gap)
        adj_gap = baseline_gap - supply_change_5yr
        gap_change = baseline_gap - adj_gap
    else:
        adj_gap = baseline_gap
        gap_change = 0

    display_gap = adj_gap
    display_gap_pct = display_gap / total_emp * 100 if total_emp > 0 else 0
    display_wage_pressure = display_gap_pct / 0.7

    # =========================================================================
    # SECTION 3: Projected Outcomes
    # =========================================================================
    st.markdown("### 5-Year Projection")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("Current Employment", f"{total_emp:,.0f}")

    with metric_col2:
        gap_delta_str = f"{-gap_change:+,.0f}" if policy_active else None
        st.metric(
            "Projected Gap",
            f"{display_gap:+,.0f}",
            delta=gap_delta_str,
            delta_color="inverse"
        )

    with metric_col3:
        st.metric("Gap %", f"{display_gap_pct:+.1f}%")

    with metric_col4:
        st.metric("Wage Pressure", f"{display_wage_pressure:+.1f}%")

    # Impact summary
    if policy_active:
        baseline_gap_pct = baseline_gap / total_emp * 100 if total_emp > 0 else 0
        baseline_wage = baseline_gap_pct / 0.7
        impact_direction = "reduces" if immigration_delta > 0 else "increases"
        st.markdown(f"""
        <div style="background: #1A1D24; border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem;
                    border-left: 3px solid {'#10B981' if immigration_delta > 0 else '#EF4444'};">
            <span style="color: #E0E0E0; font-size: 0.85rem;">
                <strong>Impact:</strong> Changing immigration from {annual_immigration:,.0f} → {new_immigration:,.0f} workers/year
                {impact_direction} the 5-year gap by <strong>{abs(gap_change):,.0f}</strong> workers
            </span>
            <br/>
            <span style="color: #718096; font-size: 0.75rem;">
                Baseline: Gap {baseline_gap:+,.0f} ({baseline_gap_pct:+.1f}%) · Wage Pressure {baseline_wage:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # SECTION 4: Annual Flow Details
    # =========================================================================
    st.markdown("### Annual Flow Breakdown")

    flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

    with flow_col1:
        st.metric("Exits", f"{annual_exits:,.0f}/yr",
                  help=f"{exit_rate*100:.1f}% annual exit rate (retirements + transfers out)")

    with flow_col2:
        other_non_immig = annual_other - annual_immigration
        st.metric("Domestic Inflows", f"{other_non_immig:,.0f}/yr",
                  help="Interstate/intercounty movers, young entrants, re-entrants")

    with flow_col3:
        display_immig = new_immigration if policy_active else annual_immigration
        immig_delta_str = f"{immigration_delta:+,.0f}" if policy_active else None
        st.metric("Immigration", f"{display_immig:,.0f}/yr", delta=immig_delta_str,
                  help="Foreign-born workers entering this occupation")

    with flow_col4:
        total_inflows = other_non_immig + display_immig
        net_flow = total_inflows - annual_exits
        st.metric("Net Flow", f"{net_flow:+,.0f}/yr")


if __name__ == "__main__":
    main()
