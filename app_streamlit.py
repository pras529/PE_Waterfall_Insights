import pandas as pd
import streamlit as st
from src.core.waterfall_logic import calculate_european_waterfall, calculate_american_waterfall

try:
    import plotly.express as px
except ImportError:
    px = None

try:
    import plotly.graph_objects as go
except ImportError:
    go = None


st.set_page_config(page_title="PE Waterfall Modeler", layout="wide")


def main():
    st.title("PE Waterfall Insights & Modeler")
    st.markdown("Welcome to the interface for modeling private equity waterfalls.")

    # --- Sidebar for Inputs ---
    st.sidebar.header("Fund Parameters")
    fund_model_type = st.sidebar.selectbox("Waterfall Model Type", ["European (Whole Fund)", "American (Deal-by-Deal)"])

    total_fund_size = st.sidebar.number_input("Total Fund Size (USD M)", min_value=0.0, value=100.0, step=10.0)
    lp_commitment = st.sidebar.number_input("LP Capital Commitment (USD M)", min_value=0.0, value=90.0, step=10.0)
    gp_commitment = st.sidebar.number_input("GP Capital Commitment (USD M)", min_value=0.0, value=10.0, step=1.0)
    preferred_return_pct = st.sidebar.number_input("Preferred Return / Hurdle Rate (%)", min_value=0.0, value=8.0,
                                                   step=0.5) / 100
    gp_catch_up_pct = st.sidebar.number_input("GP Catch-Up Percentage (%)", min_value=0.0, max_value=100.0, value=100.0,
                                              step=5.0) / 100
    carried_interest_gp_share_pct = st.sidebar.number_input("Carried Interest - GP Share (%)", min_value=0.0,
                                                            max_value=100.0, value=20.0, step=1.0) / 100

    st.sidebar.subheader("Cash Flow Input")
    uploaded_file = st.sidebar.file_uploader("Upload Cash Flow CSV", type=["csv"])

    # --- Main Area for Outputs ---
    st.subheader("Waterfall Analysis")

    if uploaded_file is not None:
        try:
            cash_flows_df = pd.read_csv(uploaded_file)
            st.write("Uploaded Cash Flows Preview:")
            st.dataframe(cash_flows_df.head())
            if st.button("Calculate Waterfall"):
                with st.spinner("Calculating..."):
                    if fund_model_type == "European (Whole Fund)":
                        results = calculate_european_waterfall(
                            lp_commitment=lp_commitment,
                            preferred_return_pct=preferred_return_pct,
                            gp_catch_up_pct=gp_catch_up_pct,
                            carried_interest_gp_share_pct=carried_interest_gp_share_pct,
                            cash_flows_df=cash_flows_df
                        )
                    else:
                        results = calculate_american_waterfall(
                            lp_commitment=lp_commitment,
                            preferred_return_pct=preferred_return_pct,
                            gp_catch_up_pct=gp_catch_up_pct,
                            carried_interest_gp_share_pct=carried_interest_gp_share_pct,
                            cash_flows_df=cash_flows_df
                        )

                    if results is not None:
                        st.success("Calculation Complete!")
                        st.write("Results:")
                        st.json(results)
                        st.balloons()

                        # Pie Chart visualization of distribution tiers
                        tiers = results.get("distribution_tiers", {}) if isinstance(results, dict) else {}
                        if tiers:
                            st.subheader("Distribution Breakdown (Pie)")
                            pie_df = pd.DataFrame({"Tier": list(tiers.keys()), "Amount": list(tiers.values())})

                            if px is None:
                                st.info("Install plotly to view the pie chart visualization.")
                            else:
                                fig = px.pie(pie_df, names="Tier", values="Amount", hole=0.3,
                                             title="LP/GP Distribution Tiers")
                                fig.update_traces(textposition="inside", textinfo="percent+label")
                                st.plotly_chart(fig, use_container_width=True)

                            
                            # Waterfall-style accumulation across tiers
                            st.subheader("Distribution Waterfall")
                            if go is None:
                                st.info("Install plotly to view the waterfall visualization.")
                            else:
                                wf_df = pie_df.copy()
                                waterfall_fig = go.Figure(
                                    go.Waterfall(
                                        name="Distribution",
                                        orientation="v",
                                        x=wf_df["Tier"],
                                        measure=["relative"] * len(wf_df),
                                        y=wf_df["Amount"],
                                    )
                                )
                                waterfall_fig.update_layout(title="Waterfall Allocation by Tier")
                                st.plotly_chart(waterfall_fig, use_container_width=True)

                        # Glossary for common terms
                        glossary_rows = [
                            {"Term": "IRR", "Definition": "Internal Rate of Return"},
                            {"Term": "MOIC", "Definition": "Multiple on Invested Capital"},
                            {"Term": "LP", "Definition": "Limited Partner"},
                            {"Term": "GP", "Definition": "General Partner"},
                            {"Term": "Preferred Return", "Definition": "Minimum return owed to LPs before carry"},
                            {"Term": "Catch-up", "Definition": "Phase where GP receives most cash until carry share is met"},
                            {"Term": "Carried Interest", "Definition": "GP share of profits after hurdles"},
                        ]
                        st.subheader("Glossary")
                        st.table(pd.DataFrame(glossary_rows))


        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.info("Please upload a cash flow CSV file to proceed.")



if __name__ == '__main__':
    # To run this from the root directory, and if src.core is structured as a package:
    # import sys
    # import os
    # sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    # from core.waterfall_logic import some_function # Example import
    main()