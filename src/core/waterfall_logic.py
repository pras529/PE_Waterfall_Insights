from .financial_utils import calculate_irr, calculate_moic


def calculate_european_waterfall(
        lp_commitment,  # Total LP commitment (used for pref calculation base)
        preferred_return_pct,  # Annual preferred return (e.g., 0.08 for 8%)
        gp_catch_up_pct,  # GP catch-up proportion (e.g., 1.0 for 100%)
        carried_interest_gp_share_pct,  # GP's share in final split (e.g., 0.20 for 20%)
        cash_flows_df  # DataFrame with 'Period', 'LP_Contribution', 'GP_Contribution', 'Gross_Fund_Proceeds'
):
    """
    Calculates distributions for a simplified European (Whole Fund) waterfall.
    Assumes preferred return is simple (not compounded) and calculated on total LP capital committed/called,
    paid after all LP capital is returned.
    """
    num_periods = len(cash_flows_df)

    # Initialize tracking variables
    total_lp_capital_called = cash_flows_df['LP_Contribution'].sum()
    total_gp_capital_called = cash_flows_df['GP_Contribution'].sum()

    lp_capital_returned = 0
    gp_capital_returned = 0
    lp_pref_paid = 0
    gp_catch_up_profit_paid = 0
    lp_final_profit_share_paid = 0
    gp_carried_interest_paid = 0  # GP's share from final split

    # Store distributions per period for LP and GP (for IRR calculation)
    lp_distributions_by_period = [0.0] * num_periods
    gp_distributions_by_period = [0.0] * num_periods

    # --- Simplified Preferred Return Calculation ---
    # Total preferred return due to LPs over the fund life before GP catch-up/carry.
    # This is a simplification; real pref is often per annum on outstanding capital.
    # Here, we'll calculate it as a hurdle: X% of total LP capital called.
    total_lp_pref_due = lp_commitment * preferred_return_pct
    # If your pref_return_pct is annual, and you have average fund life, you might do:
    # total_lp_pref_due = total_lp_capital_called * preferred_return_pct * avg_fund_life_years
    # For this example, we'll treat preferred_return_pct as the total hurdle percentage.

    for index, row in cash_flows_df.iterrows():
        period = row['Period']  # For assigning distributions to the correct period index
        available_for_distribution = row['Gross_Fund_Proceeds']

        # Tier 1: Return LP Capital
        if available_for_distribution > 0 and lp_capital_returned < total_lp_capital_called:
            payment = min(available_for_distribution, total_lp_capital_called - lp_capital_returned)
            lp_distributions_by_period[period] += payment
            lp_capital_returned += payment
            available_for_distribution -= payment

        # Tier 2: Return GP Capital
        if available_for_distribution > 0 and gp_capital_returned < total_gp_capital_called:
            payment = min(available_for_distribution, total_gp_capital_called - gp_capital_returned)
            gp_distributions_by_period[period] += payment
            gp_capital_returned += payment
            available_for_distribution -= payment

        # Tier 3: LP Preferred Return
        if available_for_distribution > 0 and lp_pref_paid < total_lp_pref_due:
            payment = min(available_for_distribution, total_lp_pref_due - lp_pref_paid)
            lp_distributions_by_period[period] += payment
            lp_pref_paid += payment
            available_for_distribution -= payment

        # Tier 4: GP Catch-up
        # GP receives gp_catch_up_pct (e.g., 100%) of distributable cash until GP's share of
        # total profits (LP pref + GP catch-up + subsequent profit) reaches carried_interest_gp_share_pct.
        # Simplified catch-up: GP gets 100% of profits until their share of (LP_pref_paid + GP_profit_so_far)
        # equals carried_interest_gp_share_pct of that total.
        # This means GP needs to receive: (lp_pref_paid / (1 - carried_interest_gp_share_pct)) - lp_pref_paid
        if available_for_distribution > 0 and carried_interest_gp_share_pct > 0:  # Ensure there's a carry to catch up to
            # Target GP profit share relative to LP pref (this is one way to model catch-up)
            target_gp_profit_for_catchup = (lp_pref_paid / (
                        1 - carried_interest_gp_share_pct)) * carried_interest_gp_share_pct \
                if (1 - carried_interest_gp_share_pct) > 0 else float('inf')

            if gp_catch_up_profit_paid < target_gp_profit_for_catchup:
                payment_needed_for_catchup = target_gp_profit_for_catchup - gp_catch_up_profit_paid
                # GP gets gp_catch_up_pct of available cash, up to the payment_needed_for_catchup
                actual_catch_up_payment_potential = available_for_distribution * gp_catch_up_pct
                payment = min(actual_catch_up_payment_potential, payment_needed_for_catchup)

                gp_distributions_by_period[period] += payment
                gp_catch_up_profit_paid += payment
                available_for_distribution -= payment

        # Tier 5: Final Split (Carried Interest)
        if available_for_distribution > 0:
            lp_share_final_split = available_for_distribution * (1 - carried_interest_gp_share_pct)
            gp_share_final_split = available_for_distribution * carried_interest_gp_share_pct

            lp_distributions_by_period[period] += lp_share_final_split
            lp_final_profit_share_paid += lp_share_final_split

            gp_distributions_by_period[period] += gp_share_final_split
            gp_carried_interest_paid += gp_share_final_split  # This is the actual carry from this tier
            available_for_distribution = 0  # All distributed

    # --- Prepare IRR Cash Flows ---
    lp_irr_cash_flows = [-cf for cf in cash_flows_df['LP_Contribution']]
    for p in range(num_periods):
        lp_irr_cash_flows[p] += lp_distributions_by_period[p]

    gp_irr_cash_flows = [-cf for cf in cash_flows_df['GP_Contribution']]
    for p in range(num_periods):
        gp_irr_cash_flows[p] += gp_distributions_by_period[p]

    # --- Calculate Metrics ---
    total_lp_distributions_received = sum(lp_distributions_by_period)
    total_gp_distributions_received = sum(gp_distributions_by_period)

    lp_irr = calculate_irr(lp_irr_cash_flows)
    gp_irr = calculate_irr(gp_irr_cash_flows)
    lp_moic = calculate_moic(total_lp_distributions_received, total_lp_capital_called)
    gp_moic = calculate_moic(total_gp_distributions_received, total_gp_capital_called)

    results = {
        "summary_metrics": {
            "LP Total Capital Called": total_lp_capital_called,
            "GP Total Capital Called": total_gp_capital_called,
            "LP Total Distributions Received": total_lp_distributions_received,
            "GP Total Distributions Received": total_gp_distributions_received,
            "LP MOIC": lp_moic,
            "GP MOIC": gp_moic,
            "LP IRR": lp_irr,
            "GP IRR": gp_irr,
        },
        "distribution_tiers": {
            "LP Capital Returned": lp_capital_returned,
            "GP Capital Returned": gp_capital_returned,
            "LP Preferred Return Paid": lp_pref_paid,
            "GP Catch-up Profit Paid": gp_catch_up_profit_paid,
            "LP Final Profit Share Paid": lp_final_profit_share_paid,
            "GP Carried Interest Paid (from Final Split)": gp_carried_interest_paid,
        },
        "notes": {
            "Preferred Return Due (Simplified Total Hurdle)": total_lp_pref_due,
            "GP Total Profit (Catch-up + Carry)": gp_catch_up_profit_paid + gp_carried_interest_paid
        },
        # "debug_cash_flows": { # Optional: for debugging
        #     "lp_irr_cf": lp_irr_cash_flows,
        #     "gp_irr_cf": gp_irr_cash_flows,
        #     "lp_dist_by_period": lp_distributions_by_period,
        #     "gp_dist_by_period": gp_distributions_by_period
        # }
    }
    return results


def calculate_american_waterfall(*args, **kwargs):
    # Placeholder - significantly more complex
    return {"status": "American waterfall model not implemented yet."}
