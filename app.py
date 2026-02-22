"""
Labor Market Tightness Explorer — Metro Edition
=================================================
Interactive dashboard showing projected labor market tightness across 260 US metro areas,
with immigration scenario toggles and occupation-specific wage elasticities.
"""

import streamlit as st
import pandas as pd
import numpy as np
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

    .scenario-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
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

# Default supply elasticity
TARGET_MEAN_ELASTICITY = 0.7

# Scenario configuration
SCENARIO_COLUMNS = {
    "Baseline": "supply_baseline",
    "Low Immigration": "supply_low_immigration",
    "No Immigration": "supply_no_immigration",
    "High Domestic": "supply_high_domestic",
}

SCENARIO_COLORS = {
    "Baseline": "#A0AEC0",
    "Low Immigration": "#F59E0B",
    "No Immigration": "#EF4444",
    "High Domestic": "#10B981",
}

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
def load_tightness_wage():
    """Load baseline tightness + wage pressure data (260 metros x 22 occs)."""
    fp = DATA_DIR / "tightness_wage_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    st.error("tightness_wage_metro.csv not found.")
    return None


@st.cache_data
def load_cohort_supply():
    """Load cohort supply projections with 4 immigration scenarios."""
    fp = DATA_DIR / "cohort_supply_projections_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_regression_gap():
    """Load regression-based demand/gap projections."""
    fp = DATA_DIR / "regression_gap_projections_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_regression_supply():
    """Load regression supply projections with confidence intervals."""
    fp = DATA_DIR / "regression_supply_projections_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_panel_cells():
    """Load metro-level demographic panel (3 periods)."""
    fp = DATA_DIR / "panel_cells_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_metro_centroids():
    """Load metro names and lat/lon coordinates."""
    fp = DATA_DIR / "metro_centroids.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_wage_elasticities():
    """Load occupation-specific wage elasticities."""
    fp = DATA_DIR / "wage_elasticities.csv"
    if fp.exists():
        df = pd.read_csv(fp)
        df = df[df['occ_group'] != '_POOLED'].copy()
        return df
    return None


# ============================================================================
# SCENARIO COMPUTATION
# ============================================================================

@st.cache_data
def compute_scenario_gap(scenario):
    """Compute adjusted gap/wage pressure for a given scenario.

    Baseline: use tightness_wage_metro directly.
    Other scenarios: adjust supply using cohort deltas, recompute gap & wage pressure.

    Returns a DataFrame with columns:
        met2013, occ_group, state_abbr, total_emp, stock_gap_pct,
        wage_pressure_pct, current_mean_wage, projected_wage_change_dollar,
        emp_projected, supply_elasticity, beta_iv
    """
    tw = load_tightness_wage()
    if tw is None:
        return None

    if scenario == "Baseline":
        return tw.copy()

    # Non-baseline: adjust supply using cohort projections
    cohort = load_cohort_supply()
    if cohort is None:
        return tw.copy()

    scenario_col = SCENARIO_COLUMNS[scenario]
    baseline_col = SCENARIO_COLUMNS["Baseline"]

    # Merge cohort data onto tightness data
    merged = tw.merge(
        cohort[["met2013", "occ_group", baseline_col, scenario_col]],
        on=["met2013", "occ_group"],
        how="left"
    )

    # Compute supply delta
    merged["delta_supply"] = merged[scenario_col] - merged[baseline_col]
    merged["delta_supply"] = merged["delta_supply"].fillna(0)

    # Adjust gap: if supply decreases (e.g. no immigration), gap gets worse (more positive)
    # stock_gap_pct is already (demand - supply) / emp * 100
    # delta_supply is the change in supply level
    merged["stock_gap_pct"] = (
        merged["stock_gap_pct"] - (merged["delta_supply"] / merged["total_emp"] * 100)
    )

    # Recompute wage pressure
    merged["wage_pressure_pct"] = merged["beta_iv"] * merged["stock_gap_pct"]
    merged["projected_wage_change_dollar"] = (
        merged["current_mean_wage"] * merged["wage_pressure_pct"] / 100
    )

    # Clean up
    result = merged.drop(columns=[baseline_col, scenario_col, "delta_supply"], errors="ignore")
    return result


# ============================================================================
# DATA AGGREGATION
# ============================================================================

def get_metro_data(scenario_data, selected_occ):
    """Aggregate scenario data to metro level for mapping.

    If a specific occupation is selected, filter first.
    If 'All Occupations', aggregate across all occs with employment weights.
    """
    centroids = load_metro_centroids()
    if centroids is None or scenario_data is None:
        return None

    if selected_occ != "All Occupations":
        data = scenario_data[scenario_data['occ_group'] == selected_occ].copy()
    else:
        data = scenario_data.copy()

    # Compute weighted wage pressure contribution
    data["wp_contrib"] = data["wage_pressure_pct"] * data["total_emp"]

    # Aggregate to metro level
    metro = data.groupby(["met2013", "state_abbr"]).agg({
        "total_emp": "sum",
        "stock_gap_pct": lambda x: np.nan,  # placeholder, recompute below
        "wp_contrib": "sum",
    }).reset_index()

    # Recompute gap_pct as sum(gap * emp) / sum(emp)
    gap_agg = data.groupby("met2013").apply(
        lambda g: (g["stock_gap_pct"] * g["total_emp"]).sum() / g["total_emp"].sum()
        if g["total_emp"].sum() > 0 else 0,
        include_groups=False
    ).reset_index(name="gap_pct")

    metro = metro.drop(columns=["stock_gap_pct"])
    metro = metro.merge(gap_agg, on="met2013")

    # Employment-weighted wage pressure
    metro["wage_pressure"] = np.where(
        metro["total_emp"] > 0,
        metro["wp_contrib"] / metro["total_emp"],
        0
    )
    metro = metro.drop(columns=["wp_contrib"])

    # Tightness percentile
    metro["tightness_percentile"] = metro["gap_pct"].rank(pct=True) * 100

    # Add centroid coordinates and names (drop state_abbr from centroids to avoid collision)
    metro = metro.merge(
        centroids.drop(columns=["state_abbr"], errors="ignore"),
        on="met2013", how="left"
    )

    return metro


def get_national_stats(scenario_data, selected_occ):
    """Compute national summary statistics for the given scenario and occupation."""
    if scenario_data is None:
        return {}

    if selected_occ != "All Occupations":
        data = scenario_data[scenario_data['occ_group'] == selected_occ]
    else:
        data = scenario_data

    total_emp = data["total_emp"].sum()
    if total_emp == 0:
        return {"total_emp": 0, "gap_pct": 0, "wage_pressure": 0}

    gap_pct = (data["stock_gap_pct"] * data["total_emp"]).sum() / total_emp
    wage_pressure = (data["wage_pressure_pct"] * data["total_emp"]).sum() / total_emp

    # Mean wage (employment-weighted)
    mean_wage = (data["current_mean_wage"] * data["total_emp"]).sum() / total_emp
    wage_dollar = mean_wage * wage_pressure / 100

    return {
        "total_emp": total_emp,
        "gap_pct": gap_pct,
        "wage_pressure": wage_pressure,
        "mean_wage": mean_wage,
        "wage_dollar": wage_dollar,
    }


# ============================================================================
# VISUALIZATIONS
# ============================================================================

def create_bubble_map(metro_data, metric='tightness'):
    """Create a Scattermapbox bubble map of metro areas."""
    if metro_data is None or len(metro_data) == 0:
        return None

    df = metro_data.dropna(subset=["lat", "lon"]).copy()
    if len(df) == 0:
        return None

    # Bubble size: proportional to sqrt(employment)
    df["bubble_size"] = np.sqrt(df["total_emp"]) / 15
    df["bubble_size"] = df["bubble_size"].clip(lower=4, upper=50)

    # Choose color column
    if metric == 'tightness':
        color_col = 'tightness_percentile'
        color_label = 'Tightness Percentile'
        cmin, cmax = 0, 100
    else:
        color_col = 'wage_pressure'
        color_label = 'Wage Pressure %'
        p5 = df[color_col].quantile(0.05)
        p95 = df[color_col].quantile(0.95)
        cmin, cmax = p5, p95

    # Color scale
    color_scale = [
        [0, '#3B82F6'],
        [0.25, '#60A5FA'],
        [0.5, '#FDE68A'],
        [0.75, '#F97316'],
        [1, '#DC2626']
    ]

    # Display name
    display_name = df["metro_name_short"].fillna(df["metro_name"].fillna(""))

    # Hover text
    hover_text = []
    for _, r in df.iterrows():
        name = r.get("metro_name_short", r.get("metro_name", ""))
        state = r.get("state_abbr", "")
        emp = r["total_emp"]
        gap = r["gap_pct"]
        wp = r["wage_pressure"]
        hover_text.append(
            f"<b>{name}, {state}</b><br>"
            f"Employment: {emp:,.0f}<br>"
            f"Gap: {gap:+.1f}%<br>"
            f"Wage Pressure: {wp:+.1f}%"
        )

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat=df["lat"],
        lon=df["lon"],
        mode="markers",
        marker=dict(
            size=df["bubble_size"],
            color=df[color_col],
            colorscale=color_scale,
            cmin=cmin,
            cmax=cmax,
            colorbar=dict(
                title=dict(text=color_label, font=dict(color='#E0E0E0')),
                tickfont=dict(color='#E0E0E0'),
                len=0.6,
                thickness=12,
                bgcolor='#1A1D24',
            ),
            opacity=0.8,
            sizemode='diameter',
        ),
        text=hover_text,
        hoverinfo="text",
        customdata=df["met2013"].values,
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=3,
            center={"lat": 39.8, "lon": -98.6},
        ),
        paper_bgcolor='#0B0D11',
        plot_bgcolor='#0B0D11',
        margin=dict(t=10, b=10, l=10, r=10),
        height=500,
        font=dict(color='#E0E0E0'),
    )

    return fig


def create_metro_mini_map(met2013, metro_data):
    """Create a small map highlighting the selected metro among all metros."""
    if metro_data is None or len(metro_data) == 0:
        return None

    df = metro_data.dropna(subset=["lat", "lon"]).copy()
    selected = df[df["met2013"] == met2013]
    if len(selected) == 0:
        return None

    sel = selected.iloc[0]
    others = df[df["met2013"] != met2013]

    fig = go.Figure()

    # All other metros as small gray dots
    if len(others) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=others["lat"],
            lon=others["lon"],
            mode="markers",
            marker=dict(size=4, color="#4A5568", opacity=0.4),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Selected metro as large highlighted bubble
    tightness_pct = sel.get("tightness_percentile", 50)
    if tightness_pct >= 67:
        highlight_color = "#F56565"
        label = "Tight"
    elif tightness_pct <= 33:
        highlight_color = "#48BB78"
        label = "Loose"
    else:
        highlight_color = "#ECC94B"
        label = "Balanced"

    fig.add_trace(go.Scattermapbox(
        lat=[sel["lat"]],
        lon=[sel["lon"]],
        mode="markers+text",
        marker=dict(size=18, color=highlight_color, opacity=0.9),
        text=[f"<b>{tightness_pct:.0f}th</b> {label}"],
        textposition="top center",
        textfont=dict(size=14, color=highlight_color),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            zoom=5,
            center={"lat": sel["lat"], "lon": sel["lon"]},
        ),
        paper_bgcolor='#1A1D24',
        plot_bgcolor='#1A1D24',
        margin=dict(t=0, b=0, l=0, r=0),
        height=250,
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
        <p>How we project labor supply, demand, and market tightness</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ## Overview

    This dashboard shows **relative labor market tightness** across 260 US metropolitan areas by comparing projected supply and demand over 5 years.

    The map uses **bubble sizing** proportional to metro employment and **percentile-based coloring** to show which regions are relatively tighter or looser than average.

    ---

    ## Data Sources

    | Source | Used For | Years |
    |--------|----------|-------|
    | American Community Survey (ACS) | Current employment by age, occupation, geography | 2019-2023 (pooled) |
    | Bureau of Labor Statistics (BLS) | Employment projections, separation rates | 2024-2034 |
    | BLS OEWS | Wage data for validation | May 2024 |

    ---

    ## Supply Projection Model

    We project labor supply using two complementary approaches:

    ### 1. Regression Model (Baseline)

    A Bartik-style shift-share prediction model that leverages national occupation growth trends interacted with local employment composition. The model includes COVID contact-intensity interactions and achieves out-of-sample R² of 0.997 with median absolute prediction error of 3.6%.

    ### 2. Cohort-Flow Model (Immigration Scenarios)

    A demographic pipeline that ages the current workforce through:
    - **Aging**: Workers advance through age bins, with age-specific exit rates
    - **Migration**: Metro-specific internal migration patterns
    - **Education**: Educational attainment transitions
    - **Labor force participation**: Age-specific LFP rates
    - **Occupation allocation**: Entry into occupations based on local demand

    The cohort model generates supply projections under four immigration scenarios:

    | Scenario | Description |
    |----------|-------------|
    | **Baseline** | Current immigration trends continue |
    | **Low Immigration** | 50% reduction in immigrant inflows |
    | **No Immigration** | Zero new immigrant inflows |
    | **High Domestic** | Increased domestic labor force participation |

    ---

    ## Demand Projection

    Demand projections come from BLS 2024-2034 occupational employment projections, allocated to metro areas proportional to current local employment shares.

    ---

    ## Wage Pressure Estimate

    We estimate wage pressure using **occupation-specific** labor supply elasticities:

    ```
    Wage Pressure % = Gap % x (1 / elasticity)
    ```

    Each occupation has a different supply elasticity calibrated from education barriers and workforce aging. Higher-barrier occupations (e.g., Legal, Engineering) have lower elasticity, meaning tightness translates into larger wage increases. The employment-weighted average elasticity is 0.7.

    ---

    ## Geographic Units

    We use **metropolitan statistical areas (MSAs)** as the primary geographic unit:
    - 260 metro areas covering the majority of US employment
    - MSAs are clusters of counties with strong economic ties
    - Based on 2013-vintage CBSA delineations for consistency with ACS microdata

    ---

    ## Occupation Groups

    We aggregate detailed occupations into 22 SOC major groups:

    Healthcare & Science: Healthcare Practitioners, Healthcare Support, Life/Physical/Social Science

    Business & Legal: Management, Business/Financial Operations, Legal

    Technical: Computer/Mathematical, Architecture/Engineering

    Education & Arts: Education/Training/Library, Arts/Design/Entertainment/Sports/Media

    Service: Food Preparation/Serving, Building/Grounds Maintenance, Personal Care, Protective Service, Community/Social Service

    Sales & Office: Sales, Office/Administrative Support

    Trades & Production: Construction/Extraction, Installation/Maintenance/Repair, Production, Transportation/Material Moving, Farming/Fishing/Forestry

    ---

    ## Model Validation

    Both models were backtested out-of-sample at the metro level using three ACS periods: P1 (2010-14), P2 (2015-19), and P3 (2019-23).

    ### Regression Model

    Trained on P1→P2 growth, tested on P2→P3 (holdout), plus 5-fold cross-validation on pooled data.

    | Protocol | OOS R² | MdAPE | Direction Accuracy |
    |----------|--------|-------|--------------------|
    | Holdout (P2→P3) | **0.985** | **8.5%** | 73.2% |
    | 5-fold CV | 0.981 | 10.7% | 67.4% |
    | Naive random walk | 0.974 | 11.2% | 44.8% |
    | Log-linear trend | 0.938 | 15.3% | 52.8% |

    The regression model beats all benchmarks on every metric. The Bartik shift-share instrument is a strong predictor of local employment growth (first-stage t ≈ 21).

    ### Cohort-Flow Model

    Backtested P2→P3 across 260 metros × 22 occupation groups (5,215 cells). Rates extracted from P2 microdata (out-of-sample).

    | Variant | MdAPE | Key Insight |
    |---------|-------|-------------|
    | Best cohort (metro-specific rates) | 11.9% | Metro-specific LFP and occupation rates with shrinkage |
    | Calibrated baseline | 12.1% | Growth-rate approach anchored to actual P2 levels |
    | Naive random walk | 11.1% | Persistence dominates at metro level |
    | **Regression model** | **8.5%** | Best overall — used as baseline in dashboard |

    The cohort model's strength is generating *relative* differences across immigration scenarios, not absolute levels. This is why the dashboard uses the regression model for baseline projections and the cohort model for scenario deltas.

    ---

    ## Confidence Intervals

    Supply projection confidence intervals are derived from the regression model's cross-validated prediction error. The intervals reflect:
    - Model estimation uncertainty
    - Variation in Bartik shock predictive power across metros
    - Historical volatility in local employment growth

    ---

    ## Limitations

    1. **Projection uncertainty**: 5-year forecasts have substantial uncertainty; actual outcomes depend on economic conditions, policy changes, and technological shifts

    2. **Immigration scenarios**: The cohort model generates relative differences between scenarios, but absolute supply levels are anchored to the regression model

    3. **No vacancy data**: We project supply and demand but don't incorporate real-time job posting or vacancy data

    4. **Wage elasticity**: Occupation-specific elasticities are calibrated from education and demographic characteristics; actual responses depend on local conditions

    ---

    ## References

    - BLS Employment Projections: [bls.gov/emp/](https://www.bls.gov/emp/)
    - BLS Occupational Separations: [bls.gov/emp/documentation/separations.htm](https://www.bls.gov/emp/documentation/separations.htm)
    - ACS PUMS: [census.gov/programs-surveys/acs/microdata.html](https://www.census.gov/programs-surveys/acs/microdata.html)

    ---

    *Last updated: February 2026*
    """)


def main():
    # Initialize session state
    if 'selected_metro' not in st.session_state:
        st.session_state.selected_metro = None
    if 'selected_occ' not in st.session_state:
        st.session_state.selected_occ = "All Occupations"

    # Load core data
    tw = load_tightness_wage()
    if tw is None:
        st.stop()

    # Create main tabs
    tab_explorer, tab_methods = st.tabs(["Explorer", "Methods"])

    with tab_methods:
        render_methods_tab()

    with tab_explorer:
        render_explorer(tw)


def render_explorer(tw):
    """Render the main explorer view with sidebar controls."""

    # ---- Sidebar ----
    with st.sidebar:
        # Scenario toggle
        st.markdown("### Supply Scenario")
        scenario = st.radio(
            "Scenario",
            list(SCENARIO_COLUMNS.keys()),
            index=0,
            key="scenario_radio",
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Occupation picker
        st.markdown("### Occupations")

        all_selected = st.session_state.selected_occ == "All Occupations"
        if st.button(
            f"{'●' if all_selected else '○'} All Occupations",
            key="all_occ",
            use_container_width=True
        ):
            st.session_state.selected_occ = "All Occupations"
            st.session_state.selected_metro = None
            st.rerun()

        occ_groups_in_data = set(tw['occ_group'].unique())
        for category, occupations in OCC_CATEGORIES.items():
            with st.expander(category):
                for occ in occupations:
                    if occ not in occ_groups_in_data:
                        continue
                    is_selected = st.session_state.selected_occ == occ
                    short_name = occ[:28] + '...' if len(occ) > 28 else occ
                    if st.button(
                        f"{'●' if is_selected else '○'} {short_name}",
                        key=f"occ_{occ}",
                        use_container_width=True
                    ):
                        st.session_state.selected_occ = occ
                        st.session_state.selected_metro = None
                        st.rerun()

        st.markdown("---")
        st.markdown('<p class="data-source">Data: ACS 2019-23, BLS 2024-2034</p>',
                    unsafe_allow_html=True)

    # ---- Main content ----
    selected_occ = st.session_state.selected_occ

    # Compute scenario data
    scenario_data = compute_scenario_gap(scenario)
    if scenario_data is None:
        st.error("Could not load scenario data.")
        st.stop()

    # Header
    scenario_color = SCENARIO_COLORS.get(scenario, "#A0AEC0")
    scenario_badge = ""
    if scenario != "Baseline":
        scenario_badge = (
            f' <span class="scenario-badge" style="background: {scenario_color}22; '
            f'color: {scenario_color}; border: 1px solid {scenario_color};">'
            f'{scenario}</span>'
        )

    st.markdown(f"""
    <div class="header">
        <h1>Labor Market Tightness Explorer{scenario_badge}</h1>
        <p>Showing: {selected_occ} &middot; 260 Metro Areas</p>
    </div>
    """, unsafe_allow_html=True)

    # Route to national or detail view
    if st.session_state.selected_metro:
        render_metro_detail(scenario_data, selected_occ, scenario)
    else:
        render_national_view(scenario_data, selected_occ, scenario)


def render_national_view(scenario_data, selected_occ, scenario):
    """Render the national bubble map view."""

    # Metric toggle
    metric_toggle = st.radio(
        "METRIC",
        ["Market Tightness", "Wage Pressure"],
        horizontal=True,
        key="metric_toggle",
        label_visibility="collapsed"
    )
    metric_type = 'tightness' if metric_toggle == "Market Tightness" else 'wage'

    # Get metro-level data
    metro_data = get_metro_data(scenario_data, selected_occ)

    # Create map
    if metro_data is not None:
        map_fig = create_bubble_map(metro_data, metric=metric_type)
        if map_fig:
            clicked = st.plotly_chart(
                map_fig,
                use_container_width=True,
                config={'displayModeBar': False},
                on_select="rerun",
                key="metro_map"
            )

            # Handle click events
            if clicked and clicked.selection and clicked.selection.points:
                point = clicked.selection.points[0]
                if 'customdata' in point and point['customdata'] is not None:
                    cd = point['customdata']
                    clicked_metro = cd[0] if isinstance(cd, (list, tuple)) else cd
                    st.session_state.selected_metro = int(clicked_metro)
                    st.rerun()

    # National summary cards
    nat = get_national_stats(scenario_data, selected_occ)
    gap_pct = nat.get("gap_pct", 0)
    wage_pressure = nat.get("wage_pressure", 0)
    wage_dollar = nat.get("wage_dollar", 0)

    if gap_pct > 2:
        market_status = "Tight"
        status_color = "#F97316"
    elif gap_pct < -2:
        market_status = "Loose"
        status_color = "#3B82F6"
    else:
        market_status = "Balanced"
        status_color = "#10B981"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">5-Year Market Status</div>
            <div style="color: {status_color}; font-size: 2rem; font-weight: 600;">{market_status}</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">Gap: {gap_pct:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Projected Wage Pressure</div>
            <div style="color: #FFFFFF; font-size: 2rem; font-weight: 600;">{wage_pressure:+.1f}%</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">${wage_dollar:+,.0f}/yr per worker</div>
        </div>
        """, unsafe_allow_html=True)


def render_metro_detail(scenario_data, selected_occ, scenario):
    """Render the detail view for a selected metro area."""
    met2013 = st.session_state.selected_metro

    # Get metro-level aggregated data for the mini map
    metro_data = get_metro_data(scenario_data, selected_occ)
    if metro_data is None:
        st.error("Metro data not available.")
        return

    metro_row = metro_data[metro_data["met2013"] == met2013]
    if len(metro_row) == 0:
        st.warning("Metro not found.")
        st.session_state.selected_metro = None
        st.rerun()
        return

    mr = metro_row.iloc[0]

    # Back button
    if st.button("← Back to National Map", key="back_btn"):
        st.session_state.selected_metro = None
        st.rerun()

    # Metro header
    metro_name = mr.get("metro_name_short", mr.get("metro_name", f"Metro {met2013}"))
    state = mr.get("state_abbr", "")
    scenario_color = SCENARIO_COLORS.get(scenario, "#A0AEC0")

    scenario_text = ""
    if scenario != "Baseline":
        scenario_text = (
            f'<span class="scenario-badge" style="background: {scenario_color}22; '
            f'color: {scenario_color}; border: 1px solid {scenario_color};">'
            f'{scenario}</span>'
        )

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 1.5rem; font-weight: 600; color: #E2E8F0;">
            {metro_name}, {state} {scenario_text}
        </div>
        <div style="font-size: 1rem; color: #A0AEC0;">
            {selected_occ}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mini map
    mini_map = create_metro_mini_map(met2013, metro_data)
    if mini_map:
        st.plotly_chart(mini_map, use_container_width=True, config={'displayModeBar': False})

    # ---- 5-Year Projection ----
    st.markdown("### 5-Year Projection")

    # Get detailed occ-level data for this metro
    metro_occ = scenario_data[scenario_data["met2013"] == met2013].copy()
    if selected_occ != "All Occupations":
        metro_occ = metro_occ[metro_occ["occ_group"] == selected_occ]

    total_emp = metro_occ["total_emp"].sum()

    # Demand-side: emp_projected from regression_gap
    reg_gap = load_regression_gap()
    if reg_gap is not None:
        metro_reg = reg_gap[reg_gap["met2013"] == met2013]
        if selected_occ != "All Occupations":
            metro_reg = metro_reg[metro_reg["occ_group"] == selected_occ]
        emp_projected = metro_reg["emp_projected"].sum() if len(metro_reg) > 0 else total_emp
    else:
        emp_projected = total_emp

    job_growth_pct = (emp_projected - total_emp) / total_emp * 100 if total_emp > 0 else 0
    job_color = "#48BB78" if job_growth_pct >= 0 else "#F56565"

    # Supply-side: use scenario data
    # For the supply growth, use cohort supply if available
    cohort = load_cohort_supply()
    scenario_col = SCENARIO_COLUMNS.get(scenario, "supply_baseline")
    if cohort is not None:
        metro_cohort = cohort[cohort["met2013"] == met2013]
        if selected_occ != "All Occupations":
            metro_cohort = metro_cohort[metro_cohort["occ_group"] == selected_occ]
        if len(metro_cohort) > 0:
            supply_projected = metro_cohort[scenario_col].sum()
            current_emp_cohort = metro_cohort["current_emp"].sum()
            workforce_growth_pct = (
                (supply_projected - current_emp_cohort) / current_emp_cohort * 100
                if current_emp_cohort > 0 else 0
            )
        else:
            workforce_growth_pct = 0
    else:
        workforce_growth_pct = 0

    workforce_color = "#48BB78" if workforce_growth_pct >= 0 else "#F56565"

    # Wage pressure
    gap_pct = mr["gap_pct"]
    wage_pressure = mr["wage_pressure"]
    mean_wage = (metro_occ["current_mean_wage"] * metro_occ["total_emp"]).sum() / total_emp if total_emp > 0 else 0
    wage_dollar = mean_wage * wage_pressure / 100

    # National comparison
    nat = get_national_stats(scenario_data, selected_occ)
    nat_gap_pct = nat.get("gap_pct", 0)
    nat_wage_pressure = nat.get("wage_pressure", 0)

    # National job growth
    if reg_gap is not None:
        if selected_occ != "All Occupations":
            nat_reg = reg_gap[reg_gap["occ_group"] == selected_occ]
        else:
            nat_reg = reg_gap
        nat_emp_proj = nat_reg["emp_projected"].sum()
        nat_total_emp = nat_reg["total_emp"].sum()
        nat_job_growth = (nat_emp_proj - nat_total_emp) / nat_total_emp * 100 if nat_total_emp > 0 else 0
    else:
        nat_job_growth = 0

    proj_col1, proj_col2, proj_col3 = st.columns(3)

    with proj_col1:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Growth in Job Openings</div>
            <div style="color: {job_color}; font-size: 2rem; font-weight: 600;">{job_growth_pct:+.1f}%</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">national: {nat_job_growth:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with proj_col2:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Growth in Workforce</div>
            <div style="color: {workforce_color}; font-size: 2rem; font-weight: 600;">{workforce_growth_pct:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with proj_col3:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Wage Pressure</div>
            <div style="color: #FFFFFF; font-size: 2rem; font-weight: 600;">{wage_pressure:+.1f}%</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">
                ${wage_dollar:+,.0f}/yr &middot; national: {nat_wage_pressure:+.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---- Projection Confidence ----
    reg_supply = load_regression_supply()
    if reg_supply is not None:
        metro_rs = reg_supply[reg_supply["met2013"] == met2013]
        if selected_occ != "All Occupations":
            metro_rs = metro_rs[metro_rs["occ_group"] == selected_occ]
        if len(metro_rs) > 0:
            proj_lo = metro_rs["emp_proj_lo"].sum()
            proj_mid = metro_rs["emp_projected"].sum()
            proj_hi = metro_rs["emp_proj_hi"].sum()

            st.markdown("### Projection Confidence")
            ci_col1, ci_col2, ci_col3 = st.columns(3)
            with ci_col1:
                st.markdown(f"""
                <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                    <div style="color: #718096; font-size: 0.8rem;">Low Estimate</div>
                    <div style="color: #A0AEC0; font-size: 1.25rem; font-weight: 600;">{proj_lo:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with ci_col2:
                st.markdown(f"""
                <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #FFA726;">
                    <div style="color: #FFA726; font-size: 0.8rem;">Central Estimate</div>
                    <div style="color: #FFFFFF; font-size: 1.25rem; font-weight: 600;">{proj_mid:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with ci_col3:
                st.markdown(f"""
                <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                    <div style="color: #718096; font-size: 0.8rem;">High Estimate</div>
                    <div style="color: #A0AEC0; font-size: 1.25rem; font-weight: 600;">{proj_hi:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

    # ---- Wage Pressure by Occupation ----
    if selected_occ == "All Occupations":
        occ_detail = scenario_data[scenario_data["met2013"] == met2013].copy()
        occ_detail = occ_detail[occ_detail["total_emp"] >= 100]

        if len(occ_detail) > 0:
            occ_detail = occ_detail.sort_values("wage_pressure_pct", ascending=True)

            st.markdown("### Wage Pressure by Occupation")

            colors = []
            for wp in occ_detail["wage_pressure_pct"]:
                if wp <= 0:
                    colors.append('#3B82F6')
                elif wp <= 5:
                    colors.append('#10B981')
                elif wp <= 10:
                    colors.append('#F59E0B')
                elif wp <= 20:
                    colors.append('#F97316')
                else:
                    colors.append('#EF4444')

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=occ_detail["occ_group"],
                x=occ_detail["wage_pressure_pct"],
                orientation='h',
                marker_color=colors,
                text=[f"{wp:+.1f}%" for wp in occ_detail["wage_pressure_pct"]],
                textposition='outside',
                textfont=dict(size=10),
            ))

            fig.update_layout(
                height=max(300, len(occ_detail) * 25),
                margin=dict(l=0, r=40, t=10, b=10),
                xaxis_title="Projected Wage Pressure (%)",
                yaxis=dict(tickfont=dict(size=10)),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E0E0E0'),
                xaxis=dict(gridcolor='#2D3748', zeroline=True,
                           zerolinecolor='#4A5568', zerolinewidth=1),
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

    # ---- Demographic Profile ----
    panel = load_panel_cells()
    if panel is not None:
        # Use P3 (most recent period)
        p3 = panel[panel["period"] == "P3"]
        metro_demo = p3[p3["met2013"] == met2013]

        if selected_occ != "All Occupations":
            metro_demo = metro_demo[metro_demo["occ_group"] == selected_occ]

        if len(metro_demo) > 0:
            st.markdown("### Demographic Profile")

            demo_emp = metro_demo["total_emp"].sum()
            if demo_emp > 0:
                # Employment-weighted averages across occ groups
                w = metro_demo["total_emp"]
                share_20_29 = (metro_demo["share_20_29"] * w).sum() / demo_emp
                share_30_54 = (metro_demo["share_30_54"] * w).sum() / demo_emp
                share_55_plus = (metro_demo["share_55_plus"] * w).sum() / demo_emp
                share_college = (metro_demo["share_college"] * w).sum() / demo_emp
                share_fb = (metro_demo["share_foreign_born"] * w).sum() / demo_emp
                avg_wage = (metro_demo["mean_wage"] * w).sum() / demo_emp

                d1, d2, d3, d4 = st.columns(4)

                with d1:
                    st.markdown(f"""
                    <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                        <div style="color: #718096; font-size: 0.75rem; text-transform: uppercase;">Age Distribution</div>
                        <div style="color: #E0E0E0; font-size: 0.9rem; margin-top: 0.5rem;">
                            20-29: {share_20_29:.0%}<br>
                            30-54: {share_30_54:.0%}<br>
                            55+: {share_55_plus:.0%}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with d2:
                    st.markdown(f"""
                    <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                        <div style="color: #718096; font-size: 0.75rem; text-transform: uppercase;">College Share</div>
                        <div style="color: #E0E0E0; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;">{share_college:.0%}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with d3:
                    st.markdown(f"""
                    <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                        <div style="color: #718096; font-size: 0.75rem; text-transform: uppercase;">Foreign-Born</div>
                        <div style="color: #E0E0E0; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;">{share_fb:.0%}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with d4:
                    st.markdown(f"""
                    <div style="background: #1A1D24; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
                        <div style="color: #718096; font-size: 0.75rem; text-transform: uppercase;">Mean Wage</div>
                        <div style="color: #E0E0E0; font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;">${avg_wage:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
