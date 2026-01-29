"""
Labor Shortage Explorer
=======================
Interactive dashboard for exploring projected labor shortages by occupation and geography,
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

# Modern, soft color palette CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #475569;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 1.5rem;
    }

    /* Header */
    .header {
        margin-bottom: 1.5rem;
    }

    .header h1 {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0 0 0.25rem 0;
    }

    .header p {
        font-size: 0.9rem;
        color: #64748b;
        margin: 0;
    }

    /* Hero cards for key metrics */
    .hero-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .hero-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }

    .hero-card.shortage {
        background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
        border-color: #fecdd3;
    }

    .hero-card.wage {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-color: #fde68a;
    }

    .hero-card.surplus {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border-color: #a7f3d0;
    }

    .hero-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .hero-card.shortage .hero-label { color: #be123c; }
    .hero-card.wage .hero-label { color: #b45309; }
    .hero-card.surplus .hero-label { color: #059669; }

    .hero-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .hero-card.shortage .hero-value { color: #e11d48; }
    .hero-card.wage .hero-value { color: #d97706; }
    .hero-card.surplus .hero-value { color: #10b981; }

    .hero-subtext {
        font-size: 0.875rem;
        line-height: 1.4;
    }

    .hero-card.shortage .hero-subtext { color: #9f1239; }
    .hero-card.wage .hero-subtext { color: #92400e; }
    .hero-card.surplus .hero-subtext { color: #047857; }

    .hero-note {
        font-size: 0.7rem;
        margin-top: 1rem;
        opacity: 0.7;
    }

    /* Secondary metrics */
    .secondary-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .secondary-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border: 1px solid #e2e8f0;
    }

    .secondary-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .secondary-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #334155;
    }

    .secondary-delta {
        font-size: 0.75rem;
        color: #10b981;
        font-weight: 500;
    }

    /* Policy banner */
    .policy-banner {
        background: white;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 0.875rem 1.25rem;
        margin-bottom: 1.5rem;
        font-size: 0.875rem;
        color: #475569;
    }

    .policy-banner strong {
        color: #059669;
    }

    /* View selector */
    .view-selector {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        background: white;
        padding: 0.25rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        width: fit-content;
    }

    /* Chart containers */
    .chart-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    .chart-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 1rem;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    .data-source {
        font-size: 0.7rem;
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
    occ_summary = df.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum', 'stock_gap': 'sum'
    }).reset_index()
    return occ_summary.sort_values('total_emp', ascending=False)


@st.cache_data
def get_state_list(df):
    return sorted(df['state_abbr'].dropna().unique())


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
    return result


# ============================================================================
# VISUALIZATIONS
# ============================================================================

def create_gap_breakdown_chart(current_emp, growth, exits, training, gap):
    """Simple horizontal breakdown."""
    fig = go.Figure()

    categories = ['Current<br>Workers', 'Growth<br>Demand', 'Worker<br>Exits', 'Training<br>Inflows', 'Net<br>Gap']
    values = [current_emp, growth, exits, training, gap]
    colors = ['#64748b', '#f97316', '#ef4444', '#10b981', '#e11d48' if gap > 0 else '#10b981']

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=[f'{v/1e6:.1f}M' for v in values],
        textposition='outside',
        textfont=dict(size=12, color='#475569'),
        cliponaxis=False
    ))

    max_val = max(values) * 1.2
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#64748b', size=11),
        margin=dict(t=40, b=20, l=40, r=40),
        height=280,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title='', zeroline=False, range=[0, max_val]),
        xaxis=dict(title='', tickfont=dict(size=10))
    )
    return fig


def create_state_map(data):
    state_data = data.groupby('state_abbr').agg({
        'total_emp': 'sum', 'emp_projected': 'sum', 'supply_projected': 'sum', 'stock_gap': 'sum'
    }).reset_index()
    state_data['gap_pct'] = state_data['stock_gap'] / state_data['emp_projected'] * 100

    min_gap = state_data['gap_pct'].min()
    max_gap = state_data['gap_pct'].max()
    padding = (max_gap - min_gap) * 0.1
    color_min = max(0, min_gap - padding)
    color_max = max_gap + padding

    fig = px.choropleth(
        state_data, locations='state_abbr', locationmode='USA-states',
        color='gap_pct', color_continuous_scale='OrRd',
        range_color=[color_min, color_max], scope='usa',
        labels={'gap_pct': 'Gap %'}
    )
    fig.update_layout(
        geo=dict(bgcolor='white', lakecolor='white', landcolor='#f8fafc', showlakes=False),
        paper_bgcolor='white',
        margin=dict(t=10, b=10, l=10, r=10),
        height=380,
        coloraxis_colorbar=dict(title='Gap %', ticksuffix='%', len=0.6, thickness=12)
    )
    return fig


def create_occupation_bars(data, top_n=8):
    occ_data = data.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum', 'stock_gap': 'sum', 'emp_projected': 'sum'
    }).reset_index()
    occ_data = occ_data.nlargest(top_n, 'stock_gap').sort_values('stock_gap', ascending=True)
    occ_data['occ_short'] = occ_data['occ_group'].apply(lambda x: x[:22] + '...' if len(x) > 25 else x)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=occ_data['occ_short'], x=occ_data['stock_gap'], orientation='h',
        marker=dict(color='#f97316', cornerradius=4),
        text=[f'{v/1e6:.1f}M' for v in occ_data['stock_gap']],
        textposition='outside', textfont=dict(size=11, color='#64748b')
    ))
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Inter', color='#64748b'),
        margin=dict(t=20, b=40, l=140, r=60), height=340,
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', title='', zeroline=False),
        yaxis=dict(title='', tickfont=dict(size=11)),
        showlegend=False
    )
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="header">
        <h1>Labor Shortage Explorer</h1>
        <p>5-year projected shortages by occupation with policy scenario modeling</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    gap_data = load_gap_data()
    if gap_data is None:
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### Occupation")
        use_target = st.checkbox("Key occupations only", value=True)

        if use_target:
            occ_options = {v: k for k, v in TARGET_OCCUPATIONS.items()}
            selected_occ_name = st.selectbox("Select", options=list(occ_options.keys()), label_visibility="collapsed")
            selected_occ = occ_options[selected_occ_name]
        else:
            occ_list = get_occupation_list(gap_data)
            occ_options = {f"{row['occ_group']}": row['occ2010'] for _, row in occ_list.head(50).iterrows()}
            selected_occ_name = st.selectbox("Select", options=list(occ_options.keys()), label_visibility="collapsed")
            selected_occ = occ_options[selected_occ_name]

        st.markdown("### Geography")
        state_list = ['All States'] + get_state_list(gap_data)
        selected_state = st.selectbox("Select", state_list, label_visibility="collapsed")

        st.markdown("### Policy Scenarios")
        training_mult = st.slider("Training expansion", 1.0, 3.0, 1.0, 0.1, format="%.1fx")
        retirement_delay = st.slider("Retirement delay", 0, 5, 0, format="%d yrs")
        retention_improve = st.slider("Retention improvement", 0.0, 0.3, 0.0, 0.05, format="%.0f%%")

        st.markdown("---")
        st.markdown('<p class="data-source">Data: ACS, IPEDS, BLS 2024-2034 Projections</p>', unsafe_allow_html=True)

    # Filter data
    filtered_data = gap_data[gap_data['occ2010'] == selected_occ].copy()
    if selected_state != 'All States':
        filtered_data = filtered_data[filtered_data['state_abbr'] == selected_state]

    # Apply policy
    policy_active = (training_mult != 1.0 or retirement_delay > 0 or retention_improve > 0)
    scenario_data = apply_policy_scenario(filtered_data, training_mult, retirement_delay, retention_improve)

    # Calculate metrics
    total_emp = filtered_data['total_emp'].sum()
    total_demand = filtered_data['emp_projected'].sum()
    baseline_supply = filtered_data['supply_projected'].sum()
    baseline_gap = filtered_data['stock_gap'].sum()

    if policy_active:
        total_supply = scenario_data['adj_supply_projected'].sum()
        total_gap = scenario_data['adj_stock_gap'].sum()
    else:
        total_supply = baseline_supply
        total_gap = baseline_gap

    # Wage pressure calculation
    gap_pct_emp = (total_gap / total_emp * 100) if total_emp > 0 else 0
    if gap_pct_emp > 0:
        wage_low = gap_pct_emp / 1.75
        wage_mid = gap_pct_emp / 0.7
        wage_high = gap_pct_emp / 0.25
    else:
        wage_low = wage_mid = wage_high = 0

    # Gap breakdown values
    training_inflows = filtered_data['annual_training_inflows'].fillna(0).sum() * 5
    exits = total_emp - baseline_supply + training_inflows + total_emp * 0.02 * 5
    growth = total_demand - total_emp

    # =========== HERO SECTION ===========
    col1, col2 = st.columns(2)

    with col1:
        card_class = "surplus" if total_gap <= 0 else "shortage"
        gap_label = "Projected Surplus" if total_gap <= 0 else "Projected Shortage"
        gap_display = abs(total_gap)

        policy_note = ""
        if policy_active:
            reduction = baseline_gap - total_gap
            policy_note = f'<div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid rgba(0,0,0,0.1); font-size:0.8rem;">With policy: {reduction/1e6:+.2f}M improvement from baseline</div>'

        st.markdown(f"""
        <div class="hero-card {card_class}">
            <div class="hero-label">{gap_label}</div>
            <div class="hero-value">{gap_display/1e6:.1f}M</div>
            <div class="hero-subtext">workers over next 5 years for {selected_occ_name}</div>
            {policy_note}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if total_gap > 0:
            st.markdown(f"""
            <div class="hero-card wage">
                <div class="hero-label">Implied Wage Pressure</div>
                <div class="hero-value">+{wage_mid:.0f}%</div>
                <div class="hero-subtext">estimated wage increase to clear market</div>
                <div class="hero-note">Range: +{wage_low:.0f}% to +{wage_high:.0f}% based on elasticity assumptions (supply: 0.1–1.0, demand: -0.15 to -0.75)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="hero-card surplus">
                <div class="hero-label">Wage Pressure</div>
                <div class="hero-value">None</div>
                <div class="hero-subtext">No shortage-driven wage pressure</div>
            </div>
            """, unsafe_allow_html=True)

    # =========== SECONDARY METRICS ===========
    supply_delta_html = ""
    if policy_active and total_supply > baseline_supply:
        supply_delta_html = f'<div class="secondary-delta">+{(total_supply-baseline_supply)/1e6:.2f}M from policy</div>'

    gap_pct_demand = total_gap / total_demand * 100 if total_demand > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="secondary-card"><div class="secondary-label">Current Employment</div><div class="secondary-value">{total_emp/1e6:.2f}M</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="secondary-card"><div class="secondary-label">5-Year Demand</div><div class="secondary-value">{total_demand/1e6:.2f}M</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="secondary-card"><div class="secondary-label">5-Year Supply</div><div class="secondary-value">{total_supply/1e6:.2f}M</div>{supply_delta_html}</div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="secondary-card"><div class="secondary-label">Gap as % of Demand</div><div class="secondary-value">{gap_pct_demand:.1f}%</div></div>', unsafe_allow_html=True)

    # =========== DETAIL VIEWS ===========
    view = st.radio("", ["Breakdown", "Geography", "Compare"], horizontal=True, label_visibility="collapsed")

    if view == "Breakdown":
        st.markdown(f'<div class="chart-card"><div class="chart-title">5-Year Gap Components — {selected_occ_name}</div></div>', unsafe_allow_html=True)
        st.plotly_chart(create_gap_breakdown_chart(total_emp, growth, exits, training_inflows, baseline_gap), use_container_width=True)

    elif view == "Geography":
        if selected_state == 'All States':
            st.markdown(f'<div class="chart-card"><div class="chart-title">Shortage by State — {selected_occ_name}</div></div>', unsafe_allow_html=True)
            st.plotly_chart(create_state_map(filtered_data), use_container_width=True)

            # State table
            state_summary = filtered_data.groupby('state_abbr').agg({
                'total_emp': 'sum', 'stock_gap': 'sum', 'emp_projected': 'sum'
            }).reset_index()
            state_summary['gap_pct'] = state_summary['stock_gap'] / state_summary['emp_projected'] * 100
            state_summary = state_summary.sort_values('stock_gap', ascending=False).head(12)
            state_summary.columns = ['State', 'Employment', 'Gap', 'Demand', 'Gap %']

            display_df = state_summary.copy()
            display_df['Employment'] = display_df['Employment'].apply(lambda x: f'{x:,.0f}')
            display_df['Gap'] = display_df['Gap'].apply(lambda x: f'{x:,.0f}')
            display_df['Demand'] = display_df['Demand'].apply(lambda x: f'{x:,.0f}')
            display_df['Gap %'] = display_df['Gap %'].apply(lambda x: f'{x:.1f}%')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"Showing {selected_state}. Select 'All States' for map view.")

    elif view == "Compare":
        st.markdown('<div class="chart-card"><div class="chart-title">Top Shortage Occupations</div></div>', unsafe_allow_html=True)
        all_occ_data = gap_data.copy()
        if selected_state != 'All States':
            all_occ_data = all_occ_data[all_occ_data['state_abbr'] == selected_state]
        st.plotly_chart(create_occupation_bars(all_occ_data), use_container_width=True)


if __name__ == "__main__":
    main()
