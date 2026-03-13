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


@st.cache_data
def load_ge_equilibrium():
    """Load GE equilibrium results (metro × occ)."""
    fp = DATA_DIR / "ge_equilibrium_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_ge_shortage():
    """Load GE shortage by wage ceiling (metro × occ)."""
    fp = DATA_DIR / "ge_shortage_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_ge_detailed():
    """Load GE equilibrium at SOC minor group level (~94 groups)."""
    fp = DATA_DIR / "ge_equilibrium_detailed_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
    return None


@st.cache_data
def load_ge_shortage_detailed():
    """Load GE shortage at SOC minor group level."""
    fp = DATA_DIR / "ge_shortage_detailed_metro.csv"
    if fp.exists():
        return pd.read_csv(fp)
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

    # Compute supply delta (in workers)
    merged["delta_supply"] = merged[scenario_col] - merged[baseline_col]
    merged["delta_supply"] = merged["delta_supply"].fillna(0)

    # Adjust gap: if supply decreases (e.g. no immigration), gap gets worse (more positive)
    # stock_gap_pct is a ratio (e.g., -0.05 = 5% surplus); delta_supply/total_emp is also a ratio
    merged["stock_gap_pct"] = (
        merged["stock_gap_pct"] - (merged["delta_supply"] / merged["total_emp"])
    )

    # Recompute tightness and wage pressure
    # tightness_index = stock_gap_pct * 100 (percentage points)
    # wage_pressure_pct = beta_iv * tightness_index
    merged["tightness_index"] = merged["stock_gap_pct"] * 100
    merged["wage_pressure_pct"] = merged["beta_iv"] * merged["tightness_index"]
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
            f"Gap: {gap*100:+.1f}%<br>"
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
        text=[f"{tightness_pct:.0f}th {label}"],
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
        <h1>Methods & Data</h1>
        <p>How we project labor supply, demand, and shortages</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ## About This Tool

    This dashboard accompanies the working paper:

    > **Bahar, D. and G.C. Wright (2026). "Projecting Occupation-Specific Labor Shortages at the Metropolitan Level."** Working paper.

    We project occupation-specific labor shortages for 260 U.S. metropolitan areas. The approach is simple in structure: we project supply and demand separately, solve for equilibrium using estimated elasticities, and define shortages as the additional workers needed when wages are constrained not to rise beyond a ceiling. Full methodological details, validation results, and robustness checks are in the paper.

    ---

    ## How It Works

    **1. Supply.** A demographic cohort-flow model projects how many workers each metro will have in each occupation, based on aging, occupational retention, labor force entry, and immigration. The model uses only demographic information from the American Community Survey — no demand-side data.

    **2. Demand.** We project how many workers employers will want using BLS Employment Projections, enriched with state-specific growth rates from Projections Central (produced by state workforce agencies). National projections are allocated to metros via Bartik shift-share instruments based on each metro's industry composition.

    **3. Equilibrium.** The raw supply-demand gap ignores the fact that wages adjust. We estimate supply elasticities from a nested logit occupation choice model and demand elasticities from Bartik-instrumented regressions. A tatonnement solver finds the wage vector that clears all 22 occupation markets simultaneously in each metro.

    **4. Shortage.** A "shortage" is defined as excess demand at a wage ceiling — the additional workers needed if wages are not allowed to rise more than a given percentage. The GE Model tab lets you adjust this ceiling.

    **5. Disaggregation.** The equilibrium model operates at the level of 22 SOC major groups. We disaggregate results to approximately 94 SOC minor groups using BLS Occupational Employment and Wage Statistics, with growth-adjusted shares and a minimum cell size threshold.

    ---

    ## Data Sources

    | Source | What We Use It For |
    |--------|-------------------|
    | **American Community Survey (ACS)** microdata, 2010-2024 | Employment, wages, demographics, migration, and immigration by metro × occupation |
    | **BLS Employment Projections** (2024-2034) | National occupation-level demand growth rates |
    | **Projections Central** (state workforce agencies) | State-specific occupation growth rates (2022-2032) |
    | **BLS Occupational Employment Statistics** (OES, 2024) | Metro-level employment by detailed SOC code for disaggregation |
    | **U.S. life tables** | Age-specific survival rates for demographic aging |

    ---

    ## Immigration Scenarios

    Immigration enters the supply model as an explicit, adjustable parameter:

    | Scenario | Description |
    |----------|-------------|
    | **Baseline** | Historical immigration rates continue unchanged |
    | **Low Immigration** | Immigration rates cut by 50% |
    | **No Immigration** | Immigration set to zero |
    | **High Domestic** | Immigration unchanged; domestic migration rates multiplied by 1.5x for growing metros |

    ---

    ## Validation

    We validated the supply model using a genuine out-of-sample test: demographic rates were extracted from the 2010 and 2020 ACS, used to project forward from 2014, and compared against actual 2024 outcomes — a strict 10-year test the model has never seen.

    | Component | RMSE | W-MAPE | Key finding |
    |-----------|------|--------|-------------|
    | Full supply model | 0.39 | 11.7% | Substantially beats naive random walk (0.47) |
    | New entrants | — | — | Critical component: RMSE drops from 0.53 to 0.39 when added |
    | Immigration | — | — | Neutral for accuracy; enables policy scenario variation |

    We also validate the supply-demand decomposition: metros where equilibrium employment exceeds demographic supply experience faster subsequent wage growth, confirming that the gap captures genuine demand pressure.

    ---

    ## Geographic & Occupation Units

    - **260 metropolitan statistical areas** (2013-vintage CBSA delineations)
    - **22 SOC major occupation groups** for the equilibrium model
    - **~94 SOC minor groups** for the disaggregation layer (with a minimum threshold of 1,000 workers per cell)

    ---

    ## Limitations

    1. **No endogenous migration.** Each metro is solved independently; workers do not move across metros in response to wage differences. This likely overstates shortages in high-wage metros and understates them elsewhere.

    2. **Projection uncertainty.** These are forward-looking projections. Actual outcomes depend on economic conditions, policy changes, and technology that the model does not anticipate.

    3. **Demand allocation.** National BLS projections are allocated to metros via Bartik shift-share, which captures differential industry exposure but assumes stable local staffing patterns.

    4. **Disaggregation error.** Splitting 22 broad groups into 94 minor groups reintroduces prediction error. The intermediate granularity and cell threshold reduce this, but within-group employment shifts are difficult to predict at the metro level.

    ---

    ## References

    - BLS Employment Projections: [bls.gov/emp/](https://www.bls.gov/emp/)
    - Projections Central: [projectionscentral.org](https://projectionscentral.org/)
    - ACS PUMS: [census.gov/programs-surveys/acs/microdata.html](https://www.census.gov/programs-surveys/acs/microdata.html)
    - BLS OES: [bls.gov/oes/](https://www.bls.gov/oes/)

    ---

    *Last updated: March 2026*
    """)


def render_ge_tab(ge_eq):
    """Render the General Equilibrium model tab with wage ceiling slider."""

    st.markdown("""
    <div class="header">
        <h1>General Equilibrium Model</h1>
        <p>Structural model: workers choose occupations, employers set wages, markets clear</p>
    </div>
    """, unsafe_allow_html=True)

    ge_short = load_ge_shortage()
    centroids = load_metro_centroids()

    # --- Sidebar controls for GE tab ---
    ceiling_pct = st.slider(
        "Max acceptable wage growth (%)",
        min_value=2, max_value=20, value=5, step=1,
        help="Shortage = additional workers needed to keep wages below this ceiling"
    )

    # Occupation filter
    occ_list = ["All Occupations"] + sorted(ge_eq['occ_group'].unique().tolist())
    selected_occ = st.selectbox("Occupation", occ_list, index=0, key="ge_occ_select")

    # --- Summary cards ---
    if selected_occ == "All Occupations":
        eq_filt = ge_eq.copy()
    else:
        eq_filt = ge_eq[ge_eq['occ_group'] == selected_occ].copy()

    avg_pct_change = np.average(eq_filt['pct_change'], weights=eq_filt['supply_eq'].clip(lower=1))
    n_wage_up = (eq_filt['pct_change'] > 0).sum()
    n_wage_down = (eq_filt['pct_change'] <= 0).sum()

    # Shortage at selected ceiling
    ceil_col = f'shortage_{ceiling_pct}pct'
    if ge_short is not None and ceil_col in ge_short.columns:
        if selected_occ == "All Occupations":
            total_shortage = ge_short[ceil_col].sum()
        else:
            short_filt = ge_short[ge_short['occ_group'] == selected_occ]
            total_shortage = short_filt[ceil_col].sum() if len(short_filt) > 0 else 0
    else:
        total_shortage = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#F97316" if avg_pct_change > 0 else "#3B82F6"
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Equilibrium Wage Change</div>
            <div style="color: {color}; font-size: 2rem; font-weight: 600;">{avg_pct_change:+.1f}%</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">{n_wage_up} up / {n_wage_down} down</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Shortage at {ceiling_pct}% Ceiling</div>
            <div style="color: #EF4444; font-size: 2rem; font-weight: 600;">{total_shortage/1e6:.2f}M</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">additional workers needed</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total_supply = eq_filt['supply_eq'].sum()
        total_demand = eq_filt['demand_eq'].sum()
        gap_pct = (total_demand - total_supply) / total_supply * 100 if total_supply > 0 else 0
        color = "#F97316" if gap_pct > 0 else "#3B82F6"
        st.markdown(f"""
        <div style="background: #1A1D24; padding: 1.25rem; border-radius: 8px; text-align: center; border: 1px solid #2D3748;">
            <div style="color: #CBD5E0; font-size: 1rem; margin-bottom: 0.5rem;">Supply-Demand Gap</div>
            <div style="color: {color}; font-size: 2rem; font-weight: 600;">{gap_pct:+.1f}%</div>
            <div style="color: #A0AEC0; font-size: 0.85rem;">at equilibrium wages</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Bubble map: color = wage change, size = shortage ---
    if centroids is not None and ge_short is not None and ceil_col in ge_short.columns:
        st.markdown("### Equilibrium Wage Changes & Shortages")

        # Aggregate to metro level
        metro_eq = eq_filt.groupby('met2013').apply(
            lambda g: pd.Series({
                'pct_change': np.average(g['pct_change'], weights=g['supply_eq'].clip(lower=1)),
                'supply_eq': g['supply_eq'].sum(),
                'demand_eq': g['demand_eq'].sum(),
            }),
            include_groups=False,
        ).reset_index()

        # Shortage at selected ceiling
        if selected_occ == "All Occupations":
            metro_short = ge_short.groupby('met2013')[ceil_col].sum().reset_index()
        else:
            short_filt = ge_short[ge_short['occ_group'] == selected_occ]
            metro_short = short_filt.groupby('met2013')[ceil_col].sum().reset_index()

        metro_eq = metro_eq.merge(metro_short, on='met2013', how='left')
        metro_eq[ceil_col] = metro_eq[ceil_col].fillna(0)
        metro_eq = metro_eq.merge(centroids, on='met2013', how='inner')

        # Bubble map
        max_short = metro_eq[ceil_col].quantile(0.95) if metro_eq[ceil_col].max() > 0 else 1
        metro_eq['bubble_size'] = np.clip(metro_eq[ceil_col] / max(max_short, 1) * 30, 3, 40)

        fig = go.Figure()
        fig.add_trace(go.Scattergeo(
            lon=metro_eq['lon'],
            lat=metro_eq['lat'],
            marker=dict(
                size=metro_eq['bubble_size'],
                color=metro_eq['pct_change'],
                colorscale='RdBu_r',
                cmid=0,
                cmin=-30,
                cmax=30,
                colorbar=dict(
                    title=dict(text="Wage %", font=dict(color='#A0AEC0', size=11)),
                    tickfont=dict(color='#A0AEC0', size=10),
                    bgcolor='rgba(0,0,0,0)',
                ),
                line=dict(width=0.5, color='rgba(255,255,255,0.3)'),
                opacity=0.8,
            ),
            text=metro_eq.apply(
                lambda r: (f"{r.get('metro_name', 'Metro ' + str(r['met2013']))}<br>"
                           f"Wage change: {r['pct_change']:+.1f}%<br>"
                           f"Shortage at {ceiling_pct}%: {r[ceil_col]:,.0f}"),
                axis=1),
            hoverinfo='text',
        ))

        fig.update_layout(
            geo=dict(
                scope='usa',
                bgcolor='rgba(0,0,0,0)',
                lakecolor='rgba(0,0,0,0)',
                landcolor='#1A1D24',
                showland=True,
                showlakes=True,
            ),
            height=450,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- Bar chart: equilibrium wages by occupation ---
    st.markdown("### Equilibrium Wage Change by Occupation")

    occ_eq = ge_eq.groupby('occ_group').apply(
        lambda g: pd.Series({
            'pct_change': np.average(g['pct_change'], weights=g['supply_eq'].clip(lower=1)),
            'supply_eq': g['supply_eq'].sum(),
        }),
        include_groups=False,
    ).reset_index().sort_values('pct_change', ascending=True)

    colors = ['#EF4444' if p > 10 else '#F97316' if p > 0 else '#3B82F6' if p > -10 else '#1D4ED8'
              for p in occ_eq['pct_change']]

    fig_occ = go.Figure()
    fig_occ.add_trace(go.Bar(
        y=occ_eq['occ_group'],
        x=occ_eq['pct_change'],
        orientation='h',
        marker_color=colors,
        text=[f"{p:+.1f}%" for p in occ_eq['pct_change']],
        textposition='outside',
        textfont=dict(size=10),
    ))

    fig_occ.update_layout(
        height=max(400, len(occ_eq) * 25),
        margin=dict(l=0, r=50, t=10, b=10),
        xaxis_title="Equilibrium Wage Change (%)",
        yaxis=dict(tickfont=dict(size=10)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E0E0E0'),
        xaxis=dict(gridcolor='#2D3748', zeroline=True,
                   zerolinecolor='#4A5568', zerolinewidth=1),
        showlegend=False,
    )

    st.plotly_chart(fig_occ, use_container_width=True)

    # --- Shortage by occupation at selected ceiling ---
    if ge_short is not None and ceil_col in ge_short.columns:
        st.markdown(f"### Shortage by Occupation (at {ceiling_pct}% ceiling)")

        occ_short = ge_short.groupby('occ_group')[ceil_col].sum().reset_index()
        occ_short = occ_short[occ_short[ceil_col] > 0].sort_values(ceil_col, ascending=True)

        if len(occ_short) > 0:
            fig_short = go.Figure()
            fig_short.add_trace(go.Bar(
                y=occ_short['occ_group'],
                x=occ_short[ceil_col] / 1000,
                orientation='h',
                marker_color='#EF4444',
                text=[f"{s/1000:,.0f}K" for s in occ_short[ceil_col]],
                textposition='outside',
                textfont=dict(size=10),
            ))

            fig_short.update_layout(
                height=max(300, len(occ_short) * 25),
                margin=dict(l=0, r=50, t=10, b=10),
                xaxis_title="Shortage (thousands of workers)",
                yaxis=dict(tickfont=dict(size=10)),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E0E0E0'),
                xaxis=dict(gridcolor='#2D3748'),
                showlegend=False,
            )

            st.plotly_chart(fig_short, use_container_width=True)

    # --- Sub-occupation drilldown ---
    ge_det = load_ge_detailed()
    ge_short_det = load_ge_shortage_detailed()
    if ge_det is not None:
        st.markdown("### Sub-Occupation Detail (SOC Minor Groups)")
        if selected_occ == "All Occupations":
            st.info("Select a specific occupation above to see the sub-occupation breakdown.")
        else:
            # Aggregate minor groups nationally for this occ_group
            det_filt = ge_det[ge_det['occ_group'] == selected_occ].copy()
            if len(det_filt) > 0:
                minor_agg = det_filt.groupby(['soc_code', 'soc_title']).agg(
                    supply=('supply_detailed', 'sum'),
                    demand=('demand_detailed', 'sum'),
                    median_wage=('current_wage_oes', 'median'),
                    bls_growth=('bls_growth_10yr', 'first'),
                ).reset_index()
                minor_agg['gap_pct'] = (minor_agg['demand'] - minor_agg['supply']) / minor_agg['supply'] * 100
                minor_agg = minor_agg.sort_values('supply', ascending=True)

                # Shortage detail
                if ge_short_det is not None and ceil_col in ge_short_det.columns:
                    short_minor = ge_short_det[ge_short_det['occ_group'] == selected_occ].groupby(
                        ['soc_code', 'soc_title']
                    )[ceil_col].sum().reset_index()
                    minor_agg = minor_agg.merge(short_minor, on=['soc_code', 'soc_title'], how='left')
                    minor_agg[ceil_col] = minor_agg[ceil_col].fillna(0)

                # Horizontal bar: supply by minor group
                fig_minor = go.Figure()
                fig_minor.add_trace(go.Bar(
                    y=minor_agg['soc_title'].str[:40],
                    x=minor_agg['supply'] / 1000,
                    orientation='h',
                    marker_color='#3B82F6',
                    name='Supply',
                    text=[f"{s/1000:,.0f}K" for s in minor_agg['supply']],
                    textposition='outside',
                    textfont=dict(size=10),
                ))
                fig_minor.add_trace(go.Bar(
                    y=minor_agg['soc_title'].str[:40],
                    x=minor_agg['demand'] / 1000,
                    orientation='h',
                    marker_color='#F97316',
                    name='Demand',
                    opacity=0.6,
                ))

                fig_minor.update_layout(
                    barmode='overlay',
                    height=max(300, len(minor_agg) * 35),
                    margin=dict(l=0, r=60, t=10, b=10),
                    xaxis_title="Workers (thousands)",
                    yaxis=dict(tickfont=dict(size=10)),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#E0E0E0'),
                    xaxis=dict(gridcolor='#2D3748'),
                    legend=dict(
                        orientation='h', yanchor='bottom', y=1.02,
                        xanchor='right', x=1, font=dict(size=11),
                    ),
                )
                st.plotly_chart(fig_minor, use_container_width=True)

                # Summary table
                display_df = minor_agg[['soc_code', 'soc_title', 'supply', 'demand',
                                         'median_wage', 'bls_growth']].copy()
                display_df.columns = ['SOC', 'Occupation', 'Supply', 'Demand',
                                      'Median Wage', 'BLS Growth (10yr)']
                display_df = display_df.sort_values('Supply', ascending=False)
                display_df['Supply'] = display_df['Supply'].apply(lambda x: f"{x:,.0f}")
                display_df['Demand'] = display_df['Demand'].apply(lambda x: f"{x:,.0f}")
                display_df['Median Wage'] = display_df['Median Wage'].apply(
                    lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
                display_df['BLS Growth (10yr)'] = display_df['BLS Growth (10yr)'].apply(
                    lambda x: f"{x:.1%}")
                st.dataframe(display_df, hide_index=True, use_container_width=True)

    # --- GE model explanation ---
    with st.expander("About the GE Model"):
        st.markdown("""
**General Equilibrium Model**

This tab shows results from a structural labor market model where:

1. **Workers choose occupations** based on relative wages (nested logit model).
   Higher wages in an occupation attract more workers, especially from less-educated
   tiers who have more occupational flexibility.

2. **Employers have downward-sloping demand curves** estimated via Bartik IV
   (shift-share instruments). When more workers are available, marginal productivity
   falls and wages decline.

3. **Markets clear**: the equilibrium wage is where supply equals demand in each
   metro x occupation cell simultaneously.

**Wage ceiling & shortage**: The slider sets a maximum acceptable wage growth rate.
The "shortage" is the number of additional workers that would be needed to keep wages
below this ceiling. At a 0% ceiling, the shortage equals the full supply-demand gap.
At a very high ceiling, the shortage approaches zero as the market clears naturally.

**Key parameters**:
- Supply elasticities (alpha): 0.25 (graduate) to 1.27 (no high school)
- Demand elasticities (eta): -0.15 to -2.0 by occupation
- 260 metros x 22 occupations = 5,720 markets solved simultaneously
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

    # Create main tabs — include GE tab if data available
    ge_eq = load_ge_equilibrium()
    if ge_eq is not None:
        tab_explorer, tab_ge, tab_methods = st.tabs(["Explorer", "GE Model", "Methods & Data"])
        with tab_ge:
            render_ge_tab(ge_eq)
    else:
        tab_explorer, tab_methods = st.tabs(["Explorer", "Methods & Data"])

    with tab_methods:
        render_methods_tab()

    with tab_explorer:
        render_explorer(tw)


def render_explorer(tw):
    """Render the main explorer view with sidebar controls."""

    # ---- Sidebar ----
    with st.sidebar:
        # Occupation picker (primary control)
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

        # Metric toggle (map coloring)
        st.markdown("### Map Metric")
        st.radio(
            "Metric",
            ["Market Tightness", "Wage Pressure"],
            index=0,
            key="metric_toggle",
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Immigration scenario toggle (secondary)
        st.markdown("### Immigration Scenario")
        scenario = st.radio(
            "Scenario",
            list(SCENARIO_COLUMNS.keys()),
            index=0,
            key="scenario_radio",
            label_visibility="collapsed",
        )

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

    # Metric type from sidebar toggle
    metric_type = 'tightness' if st.session_state.get("metric_toggle", "Market Tightness") == "Market Tightness" else 'wage'

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

    gap_pct_display = gap_pct * 100  # convert ratio to percentage points
    if gap_pct_display > 2:
        market_status = "Tight"
        status_color = "#F97316"
    elif gap_pct_display < -2:
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
            <div style="color: #A0AEC0; font-size: 0.85rem;">Gap: {gap_pct*100:+.1f}%</div>
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

    # Demand-side: projected demand from BLS + Bartik allocation
    reg_gap = load_regression_gap()
    if reg_gap is not None:
        metro_reg = reg_gap[reg_gap["met2013"] == met2013]
        if selected_occ != "All Occupations":
            metro_reg = metro_reg[metro_reg["occ_group"] == selected_occ]
        if len(metro_reg) > 0:
            demand_projected = metro_reg["metro_demand_projected"].sum()
            demand_current = metro_reg["metro_demand_current"].sum()
            job_growth_pct = (demand_projected - demand_current) / demand_current * 100 if demand_current > 0 else 0
        else:
            job_growth_pct = 0
    else:
        job_growth_pct = 0
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

    # National job growth (demand-side)
    if reg_gap is not None:
        if selected_occ != "All Occupations":
            nat_reg = reg_gap[reg_gap["occ_group"] == selected_occ]
        else:
            nat_reg = reg_gap
        nat_demand_proj = nat_reg["metro_demand_projected"].sum()
        nat_demand_curr = nat_reg["metro_demand_current"].sum()
        nat_job_growth = (nat_demand_proj - nat_demand_curr) / nat_demand_curr * 100 if nat_demand_curr > 0 else 0
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
