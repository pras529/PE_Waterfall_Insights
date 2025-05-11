import numpy as np
import numpy_financial as npf  # For IRR calculation


def calculate_moic(total_distributions, total_contributions):
    """
    Calculates the Multiple on Invested Capital (MOIC).
    Assumes total_contributions is a positive number.
    """
    if total_contributions <= 0:  # Changed to <= to handle zero contributions
        return 0.0
    return total_distributions / total_contributions


def calculate_irr(cash_flows):
    """
    Calculates the Internal Rate of Return for a series of cash flows.
    Cash flows should be a list or array where initial investments are negative
    and returns are positive.
    Example: [-100, 10, 20, 110]
    """
    if not cash_flows or len(cash_flows) < 2:
        return None  # Not enough cash flows for IRR calculation

    try:
        # numpy_financial.irr can sometimes fail for unusual cash flows;
        # you might want to add more sophisticated error handling or retries if needed.
        irr_value = npf.irr(cash_flows)
        if np.isnan(irr_value) or np.isinf(irr_value):  # Check for invalid IRR results
            return None
        return irr_value
    except Exception:
        # Broad exception catch for any issue during IRR calculation
        return None


if __name__ == '__main__':
    # Test MOIC
    moic1 = calculate_moic(total_distributions=150, total_contributions=100)
    print(f"Test MOIC: {moic1:.2f}x")  # Expected: 1.50x
    moic2 = calculate_moic(total_distributions=80, total_contributions=100)
    print(f"Test MOIC (Loss): {moic2:.2f}x")  # Expected: 0.80x
    moic3 = calculate_moic(total_distributions=100, total_contributions=0)
    print(f"Test MOIC (Zero Contribution): {moic3:.2f}x")  # Expected: 0.00x

    # Test IRR
    cf1 = [-100, 10, 20, 110]  # Investment, then returns
    irr1 = calculate_irr(cf1)
    print(f"Test IRR 1: {irr1 * 100:.2f}%" if irr1 is not None else "Test IRR 1: N/A")

    cf2 = [-100, 120]  # Simple one period return
    irr2 = calculate_irr(cf2)
    print(f"Test IRR 2: {irr2 * 100:.2f}%" if irr2 is not None else "Test IRR 2: N/A")  # Expected: 20.00%

    cf3 = [-100, 80]  # Loss
    irr3 = calculate_irr(cf3)
    print(f"Test IRR 3: {irr3 * 100:.2f}%" if irr3 is not None else "Test IRR 3: N/A")  # Expected: -20.00%

    cf4 = [0, 0, 0]  # No investment/return
    irr4 = calculate_irr(cf4)
    print(f"Test IRR 4 (zeros): {irr4 * 100:.2f}%" if irr4 is not None else "Test IRR 4 (zeros): N/A")

    cf5 = [-100]  # Only investment
    irr5 = calculate_irr(cf5)
    print(
        f"Test IRR 5 (only investment): {irr5 * 100:.2f}%" if irr5 is not None else "Test IRR 5 (only investment): N/A")