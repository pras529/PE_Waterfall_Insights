import pandas as pd
import streamlit as st
from src.core.waterfall_logic import calculate_european_waterfall


st.set_page_config(page_title="PE Waterfall Modeler - Streamlit", layout="wide")


def main():
    st.title("PE Waterfall Insights & Modeler (Streamlit Version)")
    st.markdown("Welcome to the Streamlit interface for modeling private equity waterfalls.")

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
                        st.warning("American (Deal-by-Deal) model not implemented yet.")
                        results = None

                    if results is not None:
                        st.success("Calculation Complete!")
                        st.write("Results:")
                        st.json(results)
                        st.balloons()


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