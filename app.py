"""
Labor Supply-Demand Gap Explorer
================================
Interactive dashboard for exploring projected labor gaps by occupation and geography,
with policy scenario modeling.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Labor Shortage Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, modern CSS
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        background: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar - clean light theme */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #1e293b;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1.5rem;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] label {
        color: #475569 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #e2e8f0;
        margin: 1rem 0;
    }

    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        color: white;
    }

    .header-card h1 {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        color: white;
    }

    .header-card p {
        font-size: 1rem;
        opacity: 0.8;
        margin: 0;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        flex: 1;
        border: 1px solid #e2e8f0;
        transition: box-shadow 0.2s;
    }

    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }

    .metric-value.highlight {
        color: #dc2626;
    }

    .metric-delta {
        font-size: 0.875rem;
        color: #dc2626;
        font-weight: 500;
        margin-top: 0.25rem;
    }

    /* Chart containers */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f1f5f9;
    }

    /* Policy banner */
    .policy-banner {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #86efac;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .policy-banner-icon {
        font-size: 1.25rem;
    }

    .policy-banner-text {
        color: #166534;
        font-weight: 500;
        font-size: 0.9375rem;
    }

    .policy-banner-text strong {
        color: #15803d;
    }

    /* Radio button as tabs styling */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stRadio"]) {
        background: white;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    div[data-testid="stRadio"] > div {
        gap: 0 !important;
    }

    div[data-testid="stRadio"] label {
        background: transparent;
        border-radius: 8px;
        padding: 0.5rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        color: #64748b !important;
        border: none !important;
        margin: 0 !important;
    }

    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #0f172a !important;
        color: white !important;
    }

    div[data-testid="stRadio"] label:hover {
        background: #f1f5f9;
    }

    div[data-testid="stRadio"] label[data-checked="true"]:hover {
        background: #0f172a !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Data source text */
    .data-source {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 1rem;
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

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_gap_data():
    """Load the gap projections data."""
    cz_file = DATA_DIR / "gap_projections_cz.csv"
    state_file = DATA_DIR / "gap_projections_state.csv"

    if cz_file.exists():
        return pd.read_csv(cz_file)
    elif state_file.exists():
        return pd.read_csv(state_file)
    else:
        st.error("Gap data not found.")
        return None


@st.cache_data
def get_occupation_list(df):
    """Get list of occupations with labels."""
    occ_summary = df.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum',
        'stock_gap': 'sum'
    }).reset_index()
    return occ_summary.sort_values('total_emp', ascending=False)


@st.cache_data
def get_state_list(df):
    """Get list of states."""
    return sorted(df['state_abbr'].dropna().unique())


# Target occupations
TARGET_OCCUPATIONS = {
    3130: "Registered Nurses",
    3600: "Home Health Aides",
    6230: "Electricians",
    7315: "HVAC Mechanics",
    6440: "Plumbers/Pipefitters",
    8140: "Welders",
    9130: "Truck Drivers",
    5120: "Bookkeeping Clerks",
}


# ============================================================================
# POLICY CALCULATIONS
# ============================================================================

def apply_policy_scenario(df, training_mult, retirement_delay, retention_improve):
    """Apply policy scenario adjustments."""
    result = df.copy()

    result['adj_training_inflows'] = result['annual_training_inflows'].fillna(0) * training_mult

    base_exit_rate = 0.05
    result['est_annual_exits'] = result['total_emp'] * base_exit_rate

    exit_reduction = min(retirement_delay * 0.15, 0.5)
    retirement_share = 0.4
    result['adj_annual_exits'] = result['est_annual_exits'] * (1 - exit_reduction * retirement_share)

    transfer_share = 0.4
    result['adj_annual_exits'] = result['adj_annual_exits'] * (1 - retention_improve * transfer_share)

    horizon = 5
    other_inflows = result['total_emp'] * 0.02

    result['adj_supply_projected'] = (
        result['total_emp'] +
        (result['adj_training_inflows'] + other_inflows - result['adj_annual_exits']) * horizon
    ).clip(lower=0)

    result['adj_stock_gap'] = result['emp_projected'] - result['adj_supply_projected']
    result['adj_gap_pct'] = result['adj_stock_gap'] / result['emp_projected']

    return result


# ============================================================================
# VISUALIZATIONS
# ============================================================================

def create_supply_demand_chart(data):
    """Create clean supply-demand comparison."""
    total_demand = data['emp_projected'].sum()
    total_supply = data['supply_projected'].sum()
    max_val = max(total_demand, total_supply)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Demand',
        x=['5-Year Projected'],
        y=[total_demand],
        marker_color='#ef4444',
        width=0.3,
        text=[f'{total_demand/1e6:.1f}M'],
        textposition='outside',
        textfont=dict(size=16, color='#ef4444', family='Inter'),
        cliponaxis=False
    ))

    fig.add_trace(go.Bar(
        name='Supply',
        x=['5-Year Projected'],
        y=[total_supply],
        marker_color='#3b82f6',
        width=0.3,
        text=[f'{total_supply/1e6:.1f}M'],
        textposition='outside',
        textfont=dict(size=16, color='#3b82f6', family='Inter'),
        cliponaxis=False
    ))

    fig.update_layout(
        barmode='group',
        bargap=0.4,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#475569'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=13)
        ),
        margin=dict(t=80, b=30, l=50, r=30),
        height=380,
        yaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            title='',
            tickformat=',.0f',
            zeroline=False,
            range=[0, max_val * 1.15]
        ),
        xaxis=dict(showticklabels=False)
    )

    return fig


def create_waterfall_chart(data):
    """Create clean gap decomposition waterfall."""
    current_emp = data['total_emp'].sum()
    projected_demand = data['emp_projected'].sum()
    projected_supply = data['supply_projected'].sum()

    training_inflows = data['annual_training_inflows'].fillna(0).sum() * 5
    exits = current_emp - projected_supply + training_inflows + current_emp * 0.02 * 5
    growth = projected_demand - current_emp
    gap = projected_demand - projected_supply

    # Calculate max height for y-axis range
    max_height = current_emp + growth

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Current", "Growth", "Exits", "Training", "Gap"],
        y=[current_emp, growth, -exits, training_inflows, 0],
        textposition="outside",
        text=[f"{current_emp/1e6:.1f}M", f"+{growth/1e6:.1f}M", f"-{exits/1e6:.1f}M",
              f"+{training_inflows/1e6:.2f}M", f"{gap/1e6:.1f}M"],
        textfont=dict(size=12, family='Inter', color='#475569'),
        connector={"line": {"color": "#e2e8f0", "width": 1}},
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#22c55e"}},
        totals={"marker": {"color": "#f59e0b"}},
        cliponaxis=False
    ))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#475569'),
        margin=dict(t=60, b=30, l=50, r=30),
        height=380,
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            title='',
            zeroline=False,
            range=[0, max_height * 1.15]
        ),
        xaxis=dict(tickfont=dict(size=12, color='#475569'))
    )

    return fig


def create_state_map(data):
    """Create choropleth map."""
    state_data = data.groupby('state_abbr').agg({
        'total_emp': 'sum',
        'emp_projected': 'sum',
        'supply_projected': 'sum',
        'stock_gap': 'sum'
    }).reset_index()

    state_data['gap_pct'] = state_data['stock_gap'] / state_data['emp_projected'] * 100

    # Use dynamic range based on actual data to show variation
    min_gap = state_data['gap_pct'].min()
    max_gap = state_data['gap_pct'].max()
    # Add small padding to range
    range_padding = (max_gap - min_gap) * 0.1
    color_min = max(0, min_gap - range_padding)
    color_max = max_gap + range_padding

    fig = px.choropleth(
        state_data,
        locations='state_abbr',
        locationmode='USA-states',
        color='gap_pct',
        color_continuous_scale='YlOrRd',
        range_color=[color_min, color_max],
        scope='usa',
        labels={'gap_pct': 'Gap %'}
    )

    fig.update_layout(
        geo=dict(
            bgcolor='white',
            lakecolor='white',
            landcolor='#f8fafc',
            showlakes=False
        ),
        paper_bgcolor='white',
        margin=dict(t=10, b=10, l=10, r=10),
        height=400,
        coloraxis_colorbar=dict(
            title='Gap %',
            ticksuffix='%',
            len=0.6,
            thickness=12
        )
    )

    return fig


def create_occupation_bars(data, top_n=10):
    """Create horizontal bar chart for occupations."""
    occ_data = data.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum',
        'stock_gap': 'sum',
        'emp_projected': 'sum'
    }).reset_index()

    occ_data['gap_pct'] = occ_data['stock_gap'] / occ_data['emp_projected'] * 100
    occ_data = occ_data.nlargest(top_n, 'stock_gap')
    occ_data = occ_data.sort_values('stock_gap', ascending=True)

    # Clean occupation names
    occ_data['occ_short'] = occ_data['occ_group'].apply(
        lambda x: x[:25] + '...' if len(x) > 28 else x
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=occ_data['occ_short'],
        x=occ_data['stock_gap'],
        orientation='h',
        marker=dict(
            color='#3b82f6',
            cornerradius=4
        ),
        text=[f'{v/1e6:.1f}M' for v in occ_data['stock_gap']],
        textposition='outside',
        textfont=dict(size=11, color='#475569')
    ))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#475569'),
        margin=dict(t=20, b=40, l=160, r=60),
        height=420,
        xaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            title='Projected Gap',
            title_font=dict(size=12),
            zeroline=False
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=11)
        ),
        showlegend=False
    )

    return fig


def create_gauge(value):
    """Create a clean gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(value, 100),
        number={'suffix': '%', 'font': {'size': 28, 'color': '#0f172a', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#cbd5e1', 'tickfont': {'size': 10}},
            'bar': {'color': '#3b82f6', 'thickness': 0.6},
            'bgcolor': '#f1f5f9',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 25], 'color': '#fee2e2'},
                {'range': [25, 50], 'color': '#fef3c7'},
                {'range': [50, 75], 'color': '#fef9c3'},
                {'range': [75, 100], 'color': '#dcfce7'}
            ]
        }
    ))

    fig.update_layout(
        paper_bgcolor='white',
        font=dict(family='Inter'),
        height=180,
        margin=dict(t=20, b=0, l=30, r=30)
    )

    return fig


def create_policy_comparison(baseline_gap, scenario_gap):
    """Create policy impact comparison chart."""
    reduction = baseline_gap - scenario_gap
    reduction_pct = reduction / baseline_gap * 100 if baseline_gap > 0 else 0
    max_val = max(baseline_gap, scenario_gap)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Baseline', 'With Policy'],
        y=[baseline_gap, scenario_gap],
        marker_color=['#94a3b8', '#22c55e'],
        text=[f'{baseline_gap/1e6:.2f}M', f'{scenario_gap/1e6:.2f}M'],
        textposition='outside',
        textfont=dict(size=14, family='Inter'),
        width=0.5,
        cliponaxis=False
    ))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#475569'),
        margin=dict(t=60, b=40, l=50, r=40),
        height=320,
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='#f1f5f9',
            title='',
            zeroline=False,
            range=[0, max_val * 1.15]
        ),
        annotations=[
            dict(
                x=0.5, y=1.1,
                xref='paper', yref='paper',
                text=f"<b>{reduction/1e6:.2f}M reduction ({reduction_pct:.0f}%)</b>",
                showarrow=False,
                font=dict(size=14, color='#16a34a', family='Inter')
            )
        ]
    )

    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="header-card">
        <h1>Labor Shortage Explorer</h1>
        <p>Explore projected labor shortages by occupation and model policy interventions</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    gap_data = load_gap_data()
    if gap_data is None:
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### Filters")

        use_target = st.checkbox("Key shortage occupations only", value=True)

        if use_target:
            occ_options = {v: k for k, v in TARGET_OCCUPATIONS.items()}
            selected_occ_name = st.selectbox(
                "Occupation",
                options=list(occ_options.keys()),
                index=0
            )
            selected_occ = occ_options[selected_occ_name]
        else:
            occ_list = get_occupation_list(gap_data)
            occ_options = {f"{row['occ_group']}": row['occ2010'] for _, row in occ_list.head(50).iterrows()}
            selected_occ_name = st.selectbox("Occupation", options=list(occ_options.keys()))
            selected_occ = occ_options[selected_occ_name]

        state_list = ['All States'] + get_state_list(gap_data)
        selected_state = st.selectbox("Geography", state_list)

        st.markdown("---")
        st.markdown("### Policy Scenarios")

        training_mult = st.slider(
            "Training Expansion",
            min_value=1.0, max_value=3.0, value=1.0, step=0.1,
            format="%.1fx",
            help="Multiply training program completions"
        )

        retirement_delay = st.slider(
            "Retirement Delay",
            min_value=0, max_value=5, value=0,
            format="%d years",
            help="Average years workers delay retirement"
        )

        retention_improve = st.slider(
            "Retention Improvement",
            min_value=0.0, max_value=0.3, value=0.0, step=0.05,
            format="%.0f%%",
            help="Reduction in occupation transfers"
        )

        st.markdown("---")
        st.markdown('<p class="data-source">Data: ACS, IPEDS, BLS Projections</p>', unsafe_allow_html=True)

    # Filter data
    filtered_data = gap_data[gap_data['occ2010'] == selected_occ].copy()
    if selected_state != 'All States':
        filtered_data = filtered_data[filtered_data['state_abbr'] == selected_state]

    # Apply policy
    scenario_data = apply_policy_scenario(filtered_data, training_mult, retirement_delay, retention_improve)
    policy_active = (training_mult != 1.0 or retirement_delay > 0 or retention_improve > 0)

    # Calculate metrics - use policy-adjusted values when active
    total_emp = filtered_data['total_emp'].sum()
    total_demand = filtered_data['emp_projected'].sum()

    # Baseline values
    baseline_supply = filtered_data['supply_projected'].sum()
    baseline_gap = filtered_data['stock_gap'].sum()

    # Use adjusted values when policy is active
    if policy_active:
        total_supply = scenario_data['adj_supply_projected'].sum()
        total_gap = scenario_data['adj_stock_gap'].sum()
        supply_change = total_supply - baseline_supply
        gap_change = total_gap - baseline_gap
    else:
        total_supply = baseline_supply
        total_gap = baseline_gap
        supply_change = 0
        gap_change = 0

    gap_pct = total_gap / total_demand * 100 if total_demand > 0 else 0

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Employment</div>
            <div class="metric-value">{total_emp/1e6:.2f}M</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">5-Year Demand</div>
            <div class="metric-value">{total_demand/1e6:.2f}M</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        supply_delta = f'<div class="metric-delta" style="color: #16a34a;">+{supply_change/1e6:.2f}M from policy</div>' if policy_active and supply_change > 0 else ''
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">5-Year Supply</div>
            <div class="metric-value">{total_supply/1e6:.2f}M</div>
            {supply_delta}
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Show policy impact if active
        if policy_active:
            gap_delta = f'<div class="metric-delta" style="color: #16a34a;">{gap_change/1e6:.2f}M from policy</div>'
        else:
            gap_delta = f'<div class="metric-delta">+{gap_pct:.1f}% of demand</div>'
        # Only green if surplus (gap <= 0), otherwise red
        gap_color = '#16a34a' if total_gap <= 0 else '#dc2626'
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Shortage Gap</div>
            <div class="metric-value" style="color: {gap_color};">{total_gap/1e6:.2f}M</div>
            {gap_delta}
        </div>
        """, unsafe_allow_html=True)

    # Policy summary banner
    if policy_active:
        reduction = baseline_gap - total_gap
        reduction_pct = reduction / baseline_gap * 100 if baseline_gap > 0 else 0
        st.markdown(f"""
        <div class="policy-banner">
            <span class="policy-banner-icon">📉</span>
            <span class="policy-banner-text">
                Policy reduces gap by <strong>{reduction/1e6:.2f}M workers</strong> ({reduction_pct:.0f}% reduction from baseline of {baseline_gap/1e6:.2f}M)
            </span>
        </div>
        """, unsafe_allow_html=True)

    # View selector (using radio instead of tabs for persistence)
    if 'selected_view' not in st.session_state:
        st.session_state.selected_view = "Overview"

    selected_view = st.radio(
        "View",
        ["Overview", "Geography", "Compare"],
        horizontal=True,
        key="view_selector",
        label_visibility="collapsed"
    )

    if selected_view == "Overview":
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="chart-container">
                <div class="chart-title">Supply vs Demand — {selected_occ_name}</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_supply_demand_chart(filtered_data), use_container_width=True)

        with col2:
            st.markdown("""
            <div class="chart-container">
                <div class="chart-title">5-Year Gap Decomposition</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_waterfall_chart(filtered_data), use_container_width=True)

        # Training adequacy
        total_openings = filtered_data['annual_total_openings'].sum()
        total_training = filtered_data['annual_training_inflows'].fillna(0).sum()
        adequacy = total_training / total_openings * 100 if total_openings > 0 else 0

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("""
            <div class="chart-container" style="text-align: center;">
                <div class="chart-title">Training Adequacy</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_gauge(adequacy), use_container_width=True)
            st.caption("Training completions as % of annual job openings")

    elif selected_view == "Geography":
        if selected_state == 'All States':
            st.markdown(f"""
            <div class="chart-container">
                <div class="chart-title">Gap by State — {selected_occ_name}</div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_state_map(filtered_data), use_container_width=True)

            # State table
            st.markdown("""
            <div class="chart-container">
                <div class="chart-title">State Details</div>
            </div>
            """, unsafe_allow_html=True)

            state_summary = filtered_data.groupby('state_abbr').agg({
                'total_emp': 'sum', 'stock_gap': 'sum', 'emp_projected': 'sum'
            }).reset_index()
            state_summary['gap_pct'] = state_summary['stock_gap'] / state_summary['emp_projected'] * 100
            state_summary = state_summary.sort_values('stock_gap', ascending=False)
            state_summary.columns = ['State', 'Current Emp', 'Gap', 'Demand', 'Gap %']

            display_df = state_summary.head(15).copy()
            display_df['Current Emp'] = display_df['Current Emp'].apply(lambda x: f'{x:,.0f}')
            display_df['Gap'] = display_df['Gap'].apply(lambda x: f'{x:,.0f}')
            display_df['Demand'] = display_df['Demand'].apply(lambda x: f'{x:,.0f}')
            display_df['Gap %'] = display_df['Gap %'].apply(lambda x: f'{x:.1f}%')

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"Showing data for **{selected_state}**. Select 'All States' to see the map view.")

            st.dataframe(
                filtered_data[['total_emp', 'emp_projected', 'supply_projected', 'stock_gap']].describe(),
                use_container_width=True
            )

    elif selected_view == "Compare":
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">Top Shortage Occupations</div>
        </div>
        """, unsafe_allow_html=True)

        all_occ_data = gap_data.copy()
        if selected_state != 'All States':
            all_occ_data = all_occ_data[all_occ_data['state_abbr'] == selected_state]

        st.plotly_chart(create_occupation_bars(all_occ_data, top_n=10), use_container_width=True)


if __name__ == "__main__":
    main()
