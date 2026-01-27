"""
Labor Supply-Demand Gap Explorer
================================
Interactive dashboard for exploring projected labor gaps by occupation and geography,
with policy scenario modeling.

Deploy to Streamlit Cloud or run locally with: streamlit run app.py
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

# Data path (relative for deployment)
DATA_DIR = Path(__file__).parent / "data"

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_gap_data():
    """Load the gap projections data."""
    # Try CZ-level first, fall back to state-level
    cz_file = DATA_DIR / "gap_projections_cz.csv"
    state_file = DATA_DIR / "gap_projections_state.csv"

    if cz_file.exists():
        return pd.read_csv(cz_file)
    elif state_file.exists():
        return pd.read_csv(state_file)
    else:
        st.error("Gap data not found. Please ensure data files are in the 'data' folder.")
        return None


@st.cache_data
def get_occupation_list(df):
    """Get list of occupations with labels."""
    occ_summary = df.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum',
        'stock_gap': 'sum'
    }).reset_index()
    occ_summary = occ_summary.sort_values('total_emp', ascending=False)
    return occ_summary


@st.cache_data
def get_state_list(df):
    """Get list of states."""
    return sorted(df['state_abbr'].dropna().unique())


# Target occupations for quick selection
TARGET_OCCUPATIONS = {
    3130: "Registered Nurses",
    3600: "Home Health Aides",
    6230: "Electricians",
    7315: "HVAC Mechanics",
    6440: "Plumbers/Pipefitters",
    8140: "Welders",
    9130: "Truck Drivers (Heavy)",
    5120: "Bookkeeping Clerks",
}


# ============================================================================
# POLICY SCENARIO CALCULATIONS
# ============================================================================

def apply_policy_scenario(df, training_mult, retirement_delay, retention_improve):
    """
    Apply policy scenario adjustments to the gap data.
    """
    result = df.copy()

    # Adjust training inflows
    result['adj_training_inflows'] = result['annual_training_inflows'].fillna(0) * training_mult

    # Estimate base annual exits from employment
    base_exit_rate = 0.05  # 5% annual turnover estimate
    result['est_annual_exits'] = result['total_emp'] * base_exit_rate

    # Adjust exits based on retirement delay
    exit_reduction = min(retirement_delay * 0.15, 0.5)
    retirement_share = 0.4
    result['adj_annual_exits'] = result['est_annual_exits'] * (1 - exit_reduction * retirement_share)

    # Adjust for retention improvement
    transfer_share = 0.4
    result['adj_annual_exits'] = result['adj_annual_exits'] * (1 - retention_improve * transfer_share)

    # Recalculate supply projection
    horizon = 5
    other_inflows = result['total_emp'] * 0.02

    result['adj_supply_projected'] = (
        result['total_emp'] +
        (result['adj_training_inflows'] + other_inflows - result['adj_annual_exits']) * horizon
    ).clip(lower=0)

    # Recalculate gap
    result['adj_stock_gap'] = result['emp_projected'] - result['adj_supply_projected']
    result['adj_gap_pct'] = result['adj_stock_gap'] / result['emp_projected']

    return result


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_supply_demand_bar(data, title="Supply vs Demand"):
    """Create the main supply-demand comparison bar chart."""
    total_demand = data['emp_projected'].sum()
    total_supply = data['supply_projected'].sum()
    total_gap = data['stock_gap'].sum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Projected Demand',
        x=['5-Year Projection'],
        y=[total_demand],
        marker_color='#EF553B',
        text=[f'{total_demand/1e6:.2f}M'],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='Projected Supply',
        x=['5-Year Projection'],
        y=[total_supply],
        marker_color='#636EFA',
        text=[f'{total_supply/1e6:.2f}M'],
        textposition='outside'
    ))

    gap_pct = total_gap / total_demand * 100
    gap_text = f"Gap: {total_gap/1e6:.2f}M ({gap_pct:+.1f}%)"

    fig.add_annotation(
        x=0.5, y=max(total_demand, total_supply) * 1.15,
        text=f"<b>{gap_text}</b>",
        showarrow=False,
        font=dict(size=16, color='#EF553B' if total_gap > 0 else '#00CC96')
    )

    fig.update_layout(
        title=title,
        barmode='group',
        yaxis_title='Workers',
        showlegend=True,
        height=400
    )

    return fig


def create_gap_waterfall(data):
    """Create waterfall chart showing gap components."""
    current_emp = data['total_emp'].sum()
    projected_demand = data['emp_projected'].sum()
    projected_supply = data['supply_projected'].sum()

    training_inflows = data['annual_training_inflows'].fillna(0).sum() * 5
    exits = current_emp - projected_supply + training_inflows + current_emp * 0.02 * 5
    growth = projected_demand - current_emp

    fig = go.Figure(go.Waterfall(
        name="Gap Components",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Current<br>Workforce", "Demand<br>Growth", "Workforce<br>Exits", "Training<br>Inflows", "Net Gap"],
        y=[current_emp, growth, -exits, training_inflows, 0],
        textposition="outside",
        text=[f"{current_emp/1e6:.1f}M", f"+{growth/1e6:.1f}M", f"-{exits/1e6:.1f}M",
              f"+{training_inflows/1e6:.1f}M", f"{(projected_demand-projected_supply)/1e6:.1f}M"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#EF553B"}},
        increasing={"marker": {"color": "#00CC96"}},
        totals={"marker": {"color": "#FFA15A"}}
    ))

    fig.update_layout(
        title="Gap Decomposition (5-Year)",
        showlegend=False,
        height=400
    )

    return fig


def create_state_map(data, title="Gap by State"):
    """Create choropleth map of gaps by state."""
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
        color_continuous_scale='RdYlGn_r',
        range_color=[0, 40],
        scope='usa',
        labels={'gap_pct': 'Gap %'},
        hover_data={
            'state_abbr': True,
            'total_emp': ':,.0f',
            'stock_gap': ':,.0f',
            'gap_pct': ':.1f'
        }
    )

    fig.update_layout(
        title=title,
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        height=500
    )

    return fig


def create_occupation_comparison(data, top_n=10):
    """Create horizontal bar chart comparing gaps across occupations."""
    occ_data = data.groupby(['occ2010', 'occ_group']).agg({
        'total_emp': 'sum',
        'stock_gap': 'sum',
        'emp_projected': 'sum'
    }).reset_index()

    occ_data['gap_pct'] = occ_data['stock_gap'] / occ_data['emp_projected'] * 100
    occ_data = occ_data.nlargest(top_n, 'stock_gap')

    fig = px.bar(
        occ_data,
        y='occ_group',
        x='stock_gap',
        orientation='h',
        color='gap_pct',
        color_continuous_scale='RdYlGn_r',
        labels={'stock_gap': 'Gap (Workers)', 'occ_group': 'Occupation', 'gap_pct': 'Gap %'}
    )

    fig.update_layout(
        title=f"Top {top_n} Occupations by Shortage",
        yaxis={'categoryorder': 'total ascending'},
        height=400
    )

    return fig


def create_policy_comparison(baseline_data, scenario_data, title="Policy Impact"):
    """Compare baseline and scenario gaps."""
    baseline_gap = baseline_data['stock_gap'].sum()
    scenario_gap = scenario_data['adj_stock_gap'].sum()
    reduction = baseline_gap - scenario_gap

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Baseline Gap',
        x=['Gap Comparison'],
        y=[baseline_gap],
        marker_color='#EF553B',
        text=[f'{baseline_gap/1e6:.2f}M'],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='With Policy',
        x=['Gap Comparison'],
        y=[scenario_gap],
        marker_color='#00CC96',
        text=[f'{scenario_gap/1e6:.2f}M'],
        textposition='outside'
    ))

    fig.add_annotation(
        x=0.5, y=max(baseline_gap, scenario_gap) * 1.15,
        text=f"<b>Reduction: {reduction/1e6:.2f}M ({reduction/baseline_gap*100:.1f}%)</b>",
        showarrow=False,
        font=dict(size=14, color='#00CC96')
    )

    fig.update_layout(
        title=title,
        barmode='group',
        yaxis_title='Workers',
        height=350
    )

    return fig


def create_training_adequacy_gauge(data):
    """Create gauge showing training adequacy."""
    total_openings = data['annual_total_openings'].sum()
    total_training = data['annual_training_inflows'].fillna(0).sum()
    adequacy = total_training / total_openings * 100 if total_openings > 0 else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=adequacy,
        title={'text': "Training Adequacy", 'font': {'size': 16}},
        number={'suffix': '%', 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#636EFA"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#EF553B'},
                {'range': [25, 50], 'color': '#FFA15A'},
                {'range': [50, 75], 'color': '#FECB52'},
                {'range': [75, 100], 'color': '#00CC96'}
            ]
        }
    ))

    fig.update_layout(height=250)
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.title("📊 Labor Supply-Demand Gap Explorer")
    st.markdown("""
    Explore projected labor shortages by occupation and geography,
    and see how policy interventions could close the gap.
    """)

    # Load data
    gap_data = load_gap_data()

    if gap_data is None:
        st.stop()

    # Sidebar - Filters
    st.sidebar.header("🔍 Filters")

    # Occupation selection
    st.sidebar.subheader("Occupation")
    use_target = st.sidebar.checkbox("Show target occupations only", value=True)

    if use_target:
        occ_options = {v: k for k, v in TARGET_OCCUPATIONS.items()}
        selected_occ_name = st.sidebar.selectbox(
            "Select occupation",
            options=list(occ_options.keys()),
            index=0
        )
        selected_occ = occ_options[selected_occ_name]
    else:
        occ_list = get_occupation_list(gap_data)
        occ_options = {f"{row['occ_group']} ({row['occ2010']})": row['occ2010']
                       for _, row in occ_list.iterrows()}
        selected_occ_name = st.sidebar.selectbox(
            "Select occupation",
            options=list(occ_options.keys())
        )
        selected_occ = occ_options[selected_occ_name]

    # State selection
    st.sidebar.subheader("Geography")
    state_list = ['All States'] + get_state_list(gap_data)
    selected_state = st.sidebar.selectbox("Select state", state_list)

    # Filter data
    filtered_data = gap_data[gap_data['occ2010'] == selected_occ].copy()
    if selected_state != 'All States':
        filtered_data = filtered_data[filtered_data['state_abbr'] == selected_state]

    # Sidebar - Policy Levers
    st.sidebar.header("🎛️ Policy Levers")
    st.sidebar.markdown("Adjust these to see policy impact:")

    training_mult = st.sidebar.slider(
        "Training Expansion",
        min_value=1.0, max_value=3.0, value=1.0, step=0.1,
        help="Multiplier for training program completions"
    )

    retirement_delay = st.sidebar.slider(
        "Retirement Delay (years)",
        min_value=0, max_value=5, value=0,
        help="Average years workers delay retirement"
    )

    retention_improve = st.sidebar.slider(
        "Retention Improvement",
        min_value=0.0, max_value=0.3, value=0.0, step=0.05,
        help="Fraction improvement in job retention"
    )

    # Apply policy scenario
    scenario_data = apply_policy_scenario(
        filtered_data, training_mult, retirement_delay, retention_improve
    )

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    total_emp = filtered_data['total_emp'].sum()
    total_demand = filtered_data['emp_projected'].sum()
    total_supply = filtered_data['supply_projected'].sum()
    total_gap = filtered_data['stock_gap'].sum()
    gap_pct = total_gap / total_demand * 100 if total_demand > 0 else 0

    with col1:
        st.metric("Current Employment", f"{total_emp/1e6:.2f}M")
    with col2:
        st.metric("5-Year Demand", f"{total_demand/1e6:.2f}M")
    with col3:
        st.metric("5-Year Supply", f"{total_supply/1e6:.2f}M")
    with col4:
        st.metric("Gap", f"{total_gap/1e6:.2f}M", f"{gap_pct:+.1f}%", delta_color="inverse")

    # Policy impact banner
    policy_adjusted = (training_mult != 1.0 or retirement_delay > 0 or retention_improve > 0)

    if policy_adjusted:
        st.markdown("---")
        new_gap = scenario_data['adj_stock_gap'].sum()
        reduction = total_gap - new_gap
        st.success(f"📈 **Policy Impact**: Gap reduced from {total_gap/1e6:.2f}M to {new_gap/1e6:.2f}M "
                   f"(**-{reduction/1e6:.2f}M, {reduction/total_gap*100:.1f}% reduction**)")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Geography", "📈 Occupations", "🔧 Policy Analysis"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                create_supply_demand_bar(filtered_data, title=f"Supply vs Demand: {selected_occ_name}"),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(create_gap_waterfall(filtered_data), use_container_width=True)

        st.plotly_chart(create_training_adequacy_gauge(filtered_data), use_container_width=True)

    with tab2:
        if selected_state == 'All States':
            st.plotly_chart(
                create_state_map(filtered_data, title=f"Gap by State: {selected_occ_name}"),
                use_container_width=True
            )

            st.subheader("State Details")
            state_summary = filtered_data.groupby('state_abbr').agg({
                'total_emp': 'sum', 'stock_gap': 'sum', 'emp_projected': 'sum'
            }).reset_index()
            state_summary['gap_pct'] = state_summary['stock_gap'] / state_summary['emp_projected'] * 100
            state_summary = state_summary.sort_values('stock_gap', ascending=False)
            state_summary.columns = ['State', 'Current Emp', 'Gap', 'Projected Demand', 'Gap %']
            st.dataframe(state_summary.style.format({
                'Current Emp': '{:,.0f}', 'Gap': '{:,.0f}',
                'Projected Demand': '{:,.0f}', 'Gap %': '{:.1f}%'
            }), use_container_width=True)
        else:
            st.info(f"Showing data for {selected_state}")
            st.dataframe(filtered_data[['total_emp', 'emp_projected', 'supply_projected', 'stock_gap']].describe())

    with tab3:
        st.subheader("Top Shortage Occupations")
        all_occ_data = gap_data.copy()
        if selected_state != 'All States':
            all_occ_data = all_occ_data[all_occ_data['state_abbr'] == selected_state]
        st.plotly_chart(create_occupation_comparison(all_occ_data, top_n=15), use_container_width=True)

    with tab4:
        st.subheader("🔧 Policy Scenario Analysis")
        st.markdown("""
        Adjust the policy levers in the sidebar to model different interventions:
        - **Training Expansion**: Increasing community college and vocational program capacity
        - **Retirement Delay**: Policies that encourage later retirement
        - **Retention Improvement**: Better wages/conditions reducing occupation exits
        """)

        if policy_adjusted:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_policy_comparison(filtered_data, scenario_data, title="Gap Reduction from Policy"),
                    use_container_width=True
                )
            with col2:
                baseline_gap = filtered_data['stock_gap'].sum()
                st.markdown("### Policy Contribution")

                t_only = apply_policy_scenario(filtered_data, training_mult, 0, 0)
                r_only = apply_policy_scenario(filtered_data, 1.0, retirement_delay, 0)
                ret_only = apply_policy_scenario(filtered_data, 1.0, 0, retention_improve)

                t_impact = baseline_gap - t_only['adj_stock_gap'].sum()
                r_impact = baseline_gap - r_only['adj_stock_gap'].sum()
                ret_impact = baseline_gap - ret_only['adj_stock_gap'].sum()

                st.markdown(f"""
                | Policy | Gap Reduction |
                |--------|--------------|
                | Training ({training_mult:.1f}x) | {t_impact/1e6:.2f}M ({t_impact/baseline_gap*100:.1f}%) |
                | Retirement (+{retirement_delay} yrs) | {r_impact/1e6:.2f}M ({r_impact/baseline_gap*100:.1f}%) |
                | Retention (+{retention_improve*100:.0f}%) | {ret_impact/1e6:.2f}M ({ret_impact/baseline_gap*100:.1f}%) |
                """)
        else:
            st.info("👈 Adjust the policy levers in the sidebar to see scenario analysis.")

    # Footer
    st.markdown("---")
    st.caption("Data sources: ACS, IPEDS, BLS Employment Projections. "
               "Note: Training data includes community college completions only.")


if __name__ == "__main__":
    main()
