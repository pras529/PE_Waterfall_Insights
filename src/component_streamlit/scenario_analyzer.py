import streamlit as st
import pandas as pd
import copy  # To deepcopy parameters for scenarios

# Attempt to import core logic
try:
    from src.core.waterfall_logic import calculate_european_waterfall  # Assuming European for simplicity here
    #from src.core.financial_utils import calculate_moic
except ImportError:
    st.warning("Could not import core logic for scenario analyzer.")


    def calculate_european_waterfall(*args, **kwargs):
        return {"lp_moic": 0, "gp_moic": 0, "gp_carried_interest": 0}


    def calculate_moic(*args, **kwargs):
        return 0.0


def display_scenario_analyzer():
    """
    Displays the scenario analyzer page.
    Allows users to define a base case and then compare scenarios by varying parameters.
    """
    st.header("Scenario Analyzer")
    st.markdown("""
    Define a base set of fund parameters and cash flows. Then, create scenarios
    by modifying selected parameters to see their impact on key metrics.
    (Currently supports European Model for scenario analysis).
    """)

    # --- Base Case Setup ---
    st.subheader("Base Case Parameters")
    # Use session state to store base parameters if needed across runs or for more complex interactions
    if 'base_params' not in st.session_state:
        st.session_state.base_params = {
            "lp_commitment": 90.0, "gp_commitment": 10.0,
            "preferred_return_pct": 0.08, "gp_catch_up_pct": 1.0,
            "carried_interest_gp_share_pct": 0.20
        }
    if 'base_cash_flows_df' not in st.session_state:
        st.session_state.base_cash_flows_df = None

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.base_params["lp_commitment"] = st.number_input("Base LP Commitment (M)",
                                                                        value=st.session_state.base_params[
                                                                            "lp_commitment"], key="sce_lp_commit")
        st.session_state.base_params["preferred_return_pct"] = st.number_input("Base Preferred Return (%)",
                                                                               value=st.session_state.base_params[
                                                                                         "preferred_return_pct"] * 100,
                                                                               key="sce_pref_ret") / 100
    with col2:
        st.session_state.base_params["gp_commitment"] = st.number_input("Base GP Commitment (M)",
                                                                        value=st.session_state.base_params[
                                                                            "gp_commitment"], key="sce_gp_commit")
        st.session_state.base_params["carried_interest_gp_share_pct"] = st.number_input("Base GP Carry (%)", value=
        st.session_state.base_params["carried_interest_gp_share_pct"] * 100, key="sce_gp_carry") / 100

    base_uploaded_file = st.file_uploader("Upload Base Case Cash Flow CSV (European Model)", type=["csv"],
                                          key="scenario_base_upload")
    if base_uploaded_file:
        try:
            st.session_state.base_cash_flows_df = pd.read_csv(base_uploaded_file)
            st.markdown("**Base Case Cash Flows Preview:**")
            st.dataframe(st.session_state.base_cash_flows_df.head(3))
        except Exception as e:
            st.error(f"Error loading base cash flows: {e}")
            st.session_state.base_cash_flows_df = None

    # --- Scenario Definition ---
    st.subheader("Define Scenarios")
    num_scenarios = st.number_input("Number of Scenarios to Compare", min_value=1, max_value=5, value=2,
                                    key="num_scenarios")

    scenarios_params_modifiers = []
    for i in range(num_scenarios):
        st.markdown(f"--- **Scenario {i + 1}** ---")
        expander = st.expander(f"Modify Parameters for Scenario {i + 1}", expanded=True)
        with expander:
            modifier = {}
            modifier["name"] = st.text_input(f"Scenario {i + 1} Name", value=f"Scenario {i + 1}", key=f"sce_name_{i}")
            # Example: Allow modification of preferred return and overall distribution multiple
            modifier["preferred_return_pct_new"] = st.slider(
                f"New Preferred Return (%) for Scenario {i + 1}", 0.0, 20.0,
                st.session_state.base_params["preferred_return_pct"] * 100, 0.5, key=f"sce_pref_mod_{i}"
            ) / 100

            modifier["distribution_multiplier"] = st.slider(
                f"Overall Distribution Multiplier for Scenario {i + 1}", 0.5, 3.0, 1.0, 0.1,
                help="Multiplies all 'TotalDistribution' values in the base cash flow.", key=f"sce_dist_mult_{i}"
            )
            scenarios_params_modifiers.append(modifier)

    # --- Analysis & Results ---
    if st.button("Run Scenario Analysis", key="run_scenario_analysis_button"):
        if st.session_state.base_cash_flows_df is None:
            st.error("Please upload base case cash flows before running analysis.")
        else:
            results_list = []

            # Base Case Calculation
            with st.spinner("Calculating Base Case..."):
                base_results = calculate_european_waterfall(
                    **st.session_state.base_params,
                    cash_flows_df=st.session_state.base_cash_flows_df.copy()  # Use a copy
                )
                results_list.append({
                    "Scenario Name": "Base Case",
                    "LP MOIC": base_results.get("lp_moic", "N/A"),  # Adjust key based on actual return
                    "GP MOIC": base_results.get("gp_moic", "N/A"),
                    "GP Carried Interest": base_results.get("gp_carried_interest", "N/A"),
                    "Preferred Return (%)": st.session_state.base_params["preferred_return_pct"] * 100,
                    "Distribution Multiplier": 1.0
                })

            # Scenario Calculations
            for i, mod in enumerate(scenarios_params_modifiers):
                with st.spinner(f"Calculating {mod['name']}..."):
                    scenario_params = copy.deepcopy(st.session_state.base_params)
                    scenario_params["preferred_return_pct"] = mod["preferred_return_pct_new"]

                    scenario_cash_flows_df = st.session_state.base_cash_flows_df.copy()
                    if 'TotalDistribution' in scenario_cash_flows_df.columns:
                        scenario_cash_flows_df['TotalDistribution'] = scenario_cash_flows_df['TotalDistribution'] * mod[
                            "distribution_multiplier"]
                    else:
                        st.warning(
                            f"Column 'TotalDistribution' not found in cash flows for {mod['name']}. Multiplier not applied.")

                    scenario_results = calculate_european_waterfall(
                        **scenario_params,
                        cash_flows_df=scenario_cash_flows_df
                    )
                    results_list.append({
                        "Scenario Name": mod["name"],
                        "LP MOIC": scenario_results.get("lp_moic", "N/A"),
                        "GP MOIC": scenario_results.get("gp_moic", "N/A"),
                        "GP Carried Interest": scenario_results.get("gp_carried_interest", "N/A"),
                        "Preferred Return (%)": mod["preferred_return_pct_new"] * 100,
                        "Distribution Multiplier": mod["distribution_multiplier"]
                    })

            st.subheader("Scenario Comparison Results")
            results_df = pd.DataFrame(results_list)
            st.dataframe(results_df)

            # Placeholder for comparative charts
            st.bar_chart(results_df.set_index('Scenario Name')[['LP MOIC', 'GP MOIC']])


if __name__ == '__main__':
    # This allows you to run this component page standalone for testing
    st.set_page_config(page_title="Scenario Analyzer Test", layout="wide")
    st.sidebar.info("Running scenario_analyzer.py directly for testing.")
    display_scenario_analyzer()
