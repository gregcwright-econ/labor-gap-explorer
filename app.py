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
    page_title="Labor Gap Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for slicker design
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }

    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
    }

    /* Metric cards */
    .metric-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
        line-height: 1.2;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    .metric-delta {
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 0.2rem;
    }

    .metric-delta.positive { color: #dc2626; }
    .metric-delta.negative { color: #16a34a; }

    /* Chart cards */
    .chart-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }

    .chart-card h3 {
        color: #1e3a5f;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Policy impact banner */
    .policy-banner {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #a7f3d0;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
    }

    .policy-banner-text {
        color: #065f46;
        font-weight: 600;
        font-size: 1rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }

    section[data-testid="stSidebar"] label {
        color: rgba(255,255,255,0.9) !important;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: #1e3a5f;
        color: white;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 1.5rem 0;
    }

    /* Info boxes */
    .info-box {
        background: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }

    .info-box p {
        color: #0c4a6e;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Data path - handle both local and cloud deployment
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

def create_supply_demand_chart(data, title=""):
    """Create modern supply-demand comparison."""
    total_demand = data['emp_projected'].sum()
    total_supply = data['supply_projected'].sum()
    total_gap = data['stock_gap'].sum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Projected Demand',
        x=[''],
        y=[total_demand],
        marker_color='#ef4444',
        marker_line_width=0,
        width=0.35,
        text=[f'{total_demand/1e6:.2f}M'],
        textposition='outside',
        textfont=dict(size=14, color='#ef4444', family='Arial Black')
    ))

    fig.add_trace(go.Bar(
        name='Projected Supply',
        x=[''],
        y=[total_supply],
        marker_color='#3b82f6',
        marker_line_width=0,
        width=0.35,
        text=[f'{total_supply/1e6:.2f}M'],
        textposition='outside',
        textfont=dict(size=14, color='#3b82f6', family='Arial Black')
    ))

    gap_pct = total_gap / total_demand * 100

    fig.update_layout(
        barmode='group',
        bargap=0.3,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=12)
        ),
        margin=dict(t=60, b=40, l=60, r=40),
        height=380,
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title='',
            tickformat=',.0f'
        ),
        xaxis=dict(showticklabels=False),
        annotations=[
            dict(
                x=0.5, y=1.15,
                xref='paper', yref='paper',
                text=f"<b>Gap: {total_gap/1e6:.2f}M workers ({gap_pct:.1f}%)</b>",
                showarrow=False,
                font=dict(size=16, color='#ef4444')
            )
        ]
    )

    return fig


def create_waterfall_chart(data):
    """Create gap decomposition waterfall."""
    current_emp = data['total_emp'].sum()
    projected_demand = data['emp_projected'].sum()
    projected_supply = data['supply_projected'].sum()

    training_inflows = data['annual_training_inflows'].fillna(0).sum() * 5
    exits = current_emp - projected_supply + training_inflows + current_emp * 0.02 * 5
    growth = projected_demand - current_emp

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Current<br>Workforce", "Demand<br>Growth", "Workforce<br>Exits", "Training<br>Inflows", "Gap"],
        y=[current_emp, growth, -exits, training_inflows, 0],
        textposition="outside",
        text=[f"{current_emp/1e6:.1f}M", f"+{growth/1e6:.1f}M", f"-{exits/1e6:.1f}M",
              f"+{training_inflows/1e6:.2f}M", f"{(projected_demand-projected_supply)/1e6:.1f}M"],
        textfont=dict(size=11, family='Arial'),
        connector={"line": {"color": "#94a3b8", "width": 1}},
        decreasing={"marker": {"color": "#ef4444", "line": {"width": 0}}},
        increasing={"marker": {"color": "#22c55e", "line": {"width": 0}}},
        totals={"marker": {"color": "#f59e0b", "line": {"width": 0}}}
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        margin=dict(t=40, b=40, l=40, r=40),
        height=380,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title=''),
        xaxis=dict(tickfont=dict(size=10))
    )

    return fig


def create_state_map(data, title=""):
    """Create choropleth map."""
    state_data = data.groupby('state_abbr').agg({
        'total_emp': 'sum',
        'emp_projected': 'sum',
        'supply_projected': 'sum',
        'stock_gap': 'sum'
    }).reset_index()

    state_data['gap_pct'] = state_data['stock_gap'] / state_data['emp_projected'] * 100

    fig = px.choropleth(
        state_data,
        locations='state_abbr',
        locationmode='USA-states',
        color='gap_pct',
        color_continuous_scale=[
            [0, '#22c55e'],
            [0.3, '#fbbf24'],
            [0.5, '#f97316'],
            [1, '#dc2626']
        ],
        range_color=[0, 40],
        scope='usa',
        labels={'gap_pct': 'Gap %'}
    )

    fig.update_layout(
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
            lakecolor='rgba(0,0,0,0)',
            landcolor='#f1f5f9',
            showlakes=False
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=20, l=20, r=20),
        height=420,
        coloraxis_colorbar=dict(
            title='Gap %',
            ticksuffix='%',
            len=0.6,
            thickness=15
        )
    )

    return fig


def create_occupation_bars(data, top_n=12):
    """Create horizontal bar chart for occupations."""
    occ_data = data.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum',
        'stock_gap': 'sum',
        'emp_projected': 'sum'
    }).reset_index()

    occ_data['gap_pct'] = occ_data['stock_gap'] / occ_data['emp_projected'] * 100
    occ_data = occ_data.nlargest(top_n, 'stock_gap')
    occ_data = occ_data.sort_values('stock_gap', ascending=True)

    # Truncate long names
    occ_data['occ_short'] = occ_data['occ_group'].apply(lambda x: x[:28] + '...' if len(x) > 30 else x)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=occ_data['occ_short'],
        x=occ_data['stock_gap'],
        orientation='h',
        marker=dict(
            color=occ_data['gap_pct'],
            colorscale=[
                [0, '#fbbf24'],
                [0.5, '#f97316'],
                [1, '#dc2626']
            ],
            line=dict(width=0)
        ),
        text=[f'{v/1e6:.1f}M' for v in occ_data['stock_gap']],
        textposition='outside',
        textfont=dict(size=10)
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        margin=dict(t=20, b=40, l=10, r=60),
        height=400,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title='Gap (Workers)'
        ),
        yaxis=dict(
            title='',
            tickfont=dict(size=11)
        ),
        showlegend=False
    )

    return fig


def create_gauge(value, title="Training Adequacy"):
    """Create a modern gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': '%', 'font': {'size': 32, 'color': '#1e3a5f'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#94a3b8'},
            'bar': {'color': '#3b82f6', 'thickness': 0.7},
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
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        height=200,
        margin=dict(t=30, b=10, l=30, r=30)
    )

    return fig


def create_policy_comparison(baseline_gap, scenario_gap):
    """Create policy impact comparison chart."""
    reduction = baseline_gap - scenario_gap
    reduction_pct = reduction / baseline_gap * 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Baseline', 'With Policy'],
        y=[baseline_gap, scenario_gap],
        marker_color=['#94a3b8', '#22c55e'],
        marker_line_width=0,
        text=[f'{baseline_gap/1e6:.2f}M', f'{scenario_gap/1e6:.2f}M'],
        textposition='outside',
        textfont=dict(size=14, family='Arial Black'),
        width=0.5
    ))

    fig.add_annotation(
        x=1, y=scenario_gap,
        ax=0, ay=baseline_gap,
        xref='x', yref='y',
        axref='x', ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor='#22c55e'
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif'),
        margin=dict(t=60, b=40, l=60, r=40),
        height=320,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', title=''),
        annotations=[
            dict(
                x=0.5, y=1.12,
                xref='paper', yref='paper',
                text=f"<b>↓ {reduction/1e6:.2f}M reduction ({reduction_pct:.0f}%)</b>",
                showarrow=False,
                font=dict(size=15, color='#16a34a')
            )
        ]
    )

    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Custom header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Labor Supply-Demand Gap Explorer</h1>
        <p>Explore projected labor shortages and model policy interventions</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    gap_data = load_gap_data()
    if gap_data is None:
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        st.markdown("---")

        # Occupation
        st.markdown("**Occupation**")
        use_target = st.checkbox("Target occupations only", value=True)

        if use_target:
            occ_options = {v: k for k, v in TARGET_OCCUPATIONS.items()}
            selected_occ_name = st.selectbox(
                "Select",
                options=list(occ_options.keys()),
                index=0,
                label_visibility="collapsed"
            )
            selected_occ = occ_options[selected_occ_name]
        else:
            occ_list = get_occupation_list(gap_data)
            occ_options = {f"{row['occ_group']}": row['occ2010'] for _, row in occ_list.head(50).iterrows()}
            selected_occ_name = st.selectbox("Select", options=list(occ_options.keys()), label_visibility="collapsed")
            selected_occ = occ_options[selected_occ_name]

        st.markdown("")
        st.markdown("**Geography**")
        state_list = ['All States'] + get_state_list(gap_data)
        selected_state = st.selectbox("Select state", state_list, label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### 🎛️ Policy Levers")
        st.markdown("")

        training_mult = st.slider(
            "Training Expansion",
            min_value=1.0, max_value=3.0, value=1.0, step=0.1,
            format="%.1fx"
        )

        retirement_delay = st.slider(
            "Retirement Delay",
            min_value=0, max_value=5, value=0,
            format="%d years"
        )

        retention_improve = st.slider(
            "Retention Improvement",
            min_value=0.0, max_value=0.3, value=0.0, step=0.05,
            format="%.0f%%"
        )

        st.markdown("---")
        st.caption("Data: ACS, IPEDS, BLS")

    # Filter data
    filtered_data = gap_data[gap_data['occ2010'] == selected_occ].copy()
    if selected_state != 'All States':
        filtered_data = filtered_data[filtered_data['state_abbr'] == selected_state]

    # Apply policy
    scenario_data = apply_policy_scenario(filtered_data, training_mult, retirement_delay, retention_improve)
    policy_active = (training_mult != 1.0 or retirement_delay > 0 or retention_improve > 0)

    # Calculate metrics
    total_emp = filtered_data['total_emp'].sum()
    total_demand = filtered_data['emp_projected'].sum()
    total_supply = filtered_data['supply_projected'].sum()
    total_gap = filtered_data['stock_gap'].sum()
    gap_pct = total_gap / total_demand * 100 if total_demand > 0 else 0

    # Metrics row
    cols = st.columns(4)

    metrics = [
        ("Current Employment", f"{total_emp/1e6:.2f}M", None),
        ("5-Year Demand", f"{total_demand/1e6:.2f}M", None),
        ("5-Year Supply", f"{total_supply/1e6:.2f}M", None),
        ("Shortage Gap", f"{total_gap/1e6:.2f}M", f"+{gap_pct:.1f}%")
    ]

    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            delta_html = f'<div class="metric-delta positive">{delta}</div>' if delta else ''
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                {delta_html}
            </div>
            """, unsafe_allow_html=True)

    # Policy impact banner
    if policy_active:
        new_gap = scenario_data['adj_stock_gap'].sum()
        reduction = total_gap - new_gap
        st.markdown(f"""
        <div class="policy-banner">
            <span class="policy-banner-text">
                📈 Policy Impact: Gap reduced from {total_gap/1e6:.2f}M to {new_gap/1e6:.2f}M
                — <b>{reduction/1e6:.2f}M fewer workers short ({reduction/total_gap*100:.0f}% reduction)</b>
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Geography", "📈 Compare", "🔧 Policy"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="chart-card">
                <h3>Supply vs Demand — {selected_occ_name}</h3>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_supply_demand_chart(filtered_data), use_container_width=True)

        with col2:
            st.markdown("""
            <div class="chart-card">
                <h3>Gap Decomposition (5-Year)</h3>
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
            <div class="chart-card" style="text-align: center;">
                <h3>Training Adequacy</h3>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_gauge(adequacy), use_container_width=True)
            st.caption("Training completions as % of annual job openings")

    with tab2:
        if selected_state == 'All States':
            st.markdown(f"""
            <div class="chart-card">
                <h3>Gap by State — {selected_occ_name}</h3>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(create_state_map(filtered_data), use_container_width=True)

            # State table
            st.markdown("""
            <div class="chart-card">
                <h3>State Details</h3>
            </div>
            """, unsafe_allow_html=True)

            state_summary = filtered_data.groupby('state_abbr').agg({
                'total_emp': 'sum', 'stock_gap': 'sum', 'emp_projected': 'sum'
            }).reset_index()
            state_summary['gap_pct'] = state_summary['stock_gap'] / state_summary['emp_projected'] * 100
            state_summary = state_summary.sort_values('stock_gap', ascending=False)
            state_summary.columns = ['State', 'Current Emp', 'Gap', 'Demand', 'Gap %']

            st.dataframe(
                state_summary.head(15).style.format({
                    'Current Emp': '{:,.0f}',
                    'Gap': '{:,.0f}',
                    'Demand': '{:,.0f}',
                    'Gap %': '{:.1f}%'
                }).background_gradient(subset=['Gap %'], cmap='OrRd'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.markdown(f"""
            <div class="info-box">
                <p>Showing detailed data for <b>{selected_state}</b>. Select "All States" to see the map view.</p>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(
                filtered_data[['total_emp', 'emp_projected', 'supply_projected', 'stock_gap']].describe(),
                use_container_width=True
            )

    with tab3:
        st.markdown("""
        <div class="chart-card">
            <h3>Top Shortage Occupations</h3>
        </div>
        """, unsafe_allow_html=True)

        all_occ_data = gap_data.copy()
        if selected_state != 'All States':
            all_occ_data = all_occ_data[all_occ_data['state_abbr'] == selected_state]

        st.plotly_chart(create_occupation_bars(all_occ_data, top_n=12), use_container_width=True)

    with tab4:
        st.markdown("""
        <div class="chart-card">
            <h3>Policy Scenario Analysis</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-box">
            <p>Adjust the <b>Policy Levers</b> in the sidebar to model different interventions and see their impact on the labor gap.</p>
        </div>
        """, unsafe_allow_html=True)

        if policy_active:
            col1, col2 = st.columns(2)

            baseline_gap = filtered_data['stock_gap'].sum()
            new_gap = scenario_data['adj_stock_gap'].sum()

            with col1:
                st.plotly_chart(create_policy_comparison(baseline_gap, new_gap), use_container_width=True)

            with col2:
                st.markdown("### Policy Breakdown")

                t_only = apply_policy_scenario(filtered_data, training_mult, 0, 0)
                r_only = apply_policy_scenario(filtered_data, 1.0, retirement_delay, 0)
                ret_only = apply_policy_scenario(filtered_data, 1.0, 0, retention_improve)

                t_impact = baseline_gap - t_only['adj_stock_gap'].sum()
                r_impact = baseline_gap - r_only['adj_stock_gap'].sum()
                ret_impact = baseline_gap - ret_only['adj_stock_gap'].sum()

                policy_df = pd.DataFrame({
                    'Policy': [
                        f'Training ({training_mult:.1f}x)',
                        f'Retirement (+{retirement_delay} yrs)',
                        f'Retention (+{int(retention_improve*100)}%)'
                    ],
                    'Gap Reduction': [
                        f'{t_impact/1e6:.2f}M',
                        f'{r_impact/1e6:.2f}M',
                        f'{ret_impact/1e6:.2f}M'
                    ],
                    'Impact %': [
                        f'{t_impact/baseline_gap*100:.1f}%',
                        f'{r_impact/baseline_gap*100:.1f}%',
                        f'{ret_impact/baseline_gap*100:.1f}%'
                    ]
                })

                st.dataframe(policy_df, use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #64748b;">
                <p style="font-size: 1.2rem;">👈 Adjust the policy levers in the sidebar to see scenario analysis</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
