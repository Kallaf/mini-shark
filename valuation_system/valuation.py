# Python code for valuating startup companies using multiple methods.
# This will run and print examples so you can see the outputs.
# The module includes: DCF, Venture Capital (VC) method, Comparable Multiples, Scorecard, Berkus, and Monte Carlo DCF.
# This cell executes the example/demo so you can view results immediately.

import math
import random
from typing import List, Dict, Tuple, Optional

class StartupValuator:
    """
    Startup valuation toolkit with several commonly used methods.
    Methods included:
      - Discounted Cash Flow (DCF)
      - Venture Capital (VC) method (post-money exit-based)
      - Comparable companies (multiples)
      - Scorecard method (angel investing heuristic)
      - Berkus method (early-stage heuristic)
      - Monte Carlo DCF (to model uncertainty in growth margins)
    """
    
    @staticmethod
    def dcf(ebitda0: float,
            revenue0: Optional[float] = None,
            revenue_growth: List[float] = None,
            ebitda_margin: List[float] = None,
            capex_pct: List[float] = None,
            change_in_wc_pct: List[float] = None,
            discount_rate: float = 0.30,
            terminal_growth: float = 0.02,
            tax_rate: float = 0.25,
            terminal_multiple: Optional[float] = None) -> Dict[str, float]:
        """
        Simple DCF on an explicit forecast period.
        Parameters:
          - ebitda0: current-year EBITDA (if you prefer to start from revenue set revenue0 and margins)
          - revenue0: current revenue (optional if ebitda0 given)
          - revenue_growth: list of expected annual revenue growth rates (length = n years)
          - ebitda_margin: list of expected EBITDA margins for each forecast year (length n)
          - capex_pct: CAPEX as % of revenue per year (list n). If None assumed 5%.
          - change_in_wc_pct: change in working capital as % of revenue per year (list n). If None assumed 0.
          - discount_rate: WACC / investor required return (e.g. 0.30 for startups)
          - terminal_growth: perpetual growth rate
          - tax_rate: corporate tax on EBIT
          - terminal_multiple: if provided, use exit multiple instead of Gordon growth
        Returns dict with NPV, terminal value and detailed cash flows.
        """
        if revenue_growth is None or ebitda_margin is None:
            raise ValueError("Please pass revenue_growth and ebitda_margin as lists for each forecast year.")
        n = len(revenue_growth)
        if revenue0 is None:
            # derive revenue0 from ebitda0 using first margin
            if ebitda_margin[0] == 0:
                raise ValueError("Cannot derive revenue0 because first-year margin is zero.")
            revenue0 = ebitda0 / ebitda_margin[0]
        capex_pct = capex_pct or [0.05] * n
        change_in_wc_pct = change_in_wc_pct or [0.0] * n
        # build projections
        revenues = []
        ebitdas = []
        capex = []
        change_in_wc = []
        unlevered_fcfs = []
        r = revenue0
        for i in range(n):
            g = revenue_growth[i]
            r = r * (1 + g)
            revenues.append(r)
            m = ebitda_margin[i]
            ebit = r * m
            ebitdas.append(ebit)
            c = r * capex_pct[i]
            capex.append(c)
            wc = r * change_in_wc_pct[i]
            change_in_wc.append(wc)
            # approximating EBIT(1 - tax) + non-cash (ebitda - ebit) - capex - change in WC
            # but since ebitda variable is actually EBITDA, we'll compute unlevered FCF as:
            # EBIT = EBITDA (here treated as proxy) * (1 - some depreciation). For simplicity:
            # Use unlevered FCF ≈ EBITDA*(1 - tax_rate) - CAPEX - change_in_wc
            ufcf = ebit * (1 - tax_rate) - c - wc
            unlevered_fcfs.append(ufcf)
        # discount and terminal
        npv = 0.0
        for i, cf in enumerate(unlevered_fcfs, start=1):
            npv += cf / ((1 + discount_rate) ** i)
        last_revenue = revenues[-1]
        last_ebitda = ebitdas[-1]
        if terminal_multiple is not None:
            terminal_value = last_ebitda * terminal_multiple
        else:
            # Gordon growth on next year's free cash flow estimate.
            last_ufcf = unlevered_fcfs[-1]
            if discount_rate <= terminal_growth:
                # fall back to multiple of EBITDA if unrealistic assumptions
                terminal_value = last_ebitda * 8.0
            else:
                terminal_value = last_ufcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
        discounted_terminal = terminal_value / ((1 + discount_rate) ** n)
        enterprise_value = npv + discounted_terminal
        return {
            "enterprise_value": enterprise_value,
            "npv_of_proj_fcfs": npv,
            "terminal_value": terminal_value,
            "discounted_terminal": discounted_terminal,
            "forecast_revenues": revenues,
            "forecast_ebitda": ebitdas,
            "forecast_ufcfs": unlevered_fcfs
        }
    
    @staticmethod
    def vc_method(exit_revenue: float,
                  exit_revenue_multiple: float,
                  investor_target_moic: float,
                  years_to_exit: int,
                  pre_money: Optional[float] = None) -> Dict[str, float]:
        """
        Venture Capital method (backsolves pre/post-money from desired return).
        - exit_revenue: expected revenue at exit year
        - exit_revenue_multiple: revenue multiple at exit (or EBITDA multiple if providing EBITDA)
        - investor_target_moic: investor wants e.g. 10x (10.0)
        - years_to_exit: years until exit
        Returns post-money valuation today (discount implicitly by target MOIC) and ownership required.
        """
        exit_value = exit_revenue * exit_revenue_multiple
        # Required investment today to achieve target MOIC ignoring discounting = exit_value / MOIC
        required_post_money = exit_value / investor_target_moic
        # If years_to_exit is used to annualize, we can compute annual required return:
        annual_return = investor_target_moic ** (1 / years_to_exit)
        # Discount exit value by annual_return to get present value
        pv = exit_value / (annual_return ** years_to_exit)
        # post-money (VC practitioners often use PV approach)
        post_money = pv
        if pre_money is None:
            pre_money = post_money - 0.0  # if you want to assume no current cash
        ownership = required_post_money / post_money if post_money != 0 else None
        return {
            "exit_value": exit_value,
            "required_post_money_by_moic": required_post_money,
            "annual_return_factor": annual_return,
            "post_money_present_value": post_money,
            "pre_money_assumed": pre_money,
            "ownership_required_estimate": ownership
        }
    
    @staticmethod
    def comparables(revenue: float, multiple: float, adjustments: float = 0.0) -> Dict[str, float]:
        """
        Comparable companies method using a revenue multiple (or EBITDA multiple if input is ebitda).
        adjustments: +/- value adjustments to apply (e.g. for size, growth, risk).
        """
        raw = revenue * multiple
        adj = raw + adjustments
        return {"raw_value": raw, "adjusted_value": adj, "multiple_used": multiple}
    
    @staticmethod
    def scorecard_method(baseline_valuation: float,
                         factors: Dict[str, float],
                         weights: Dict[str, float]) -> Dict[str, float]:
        """
        Scorecard method (used by angels): start with average pre-money for stage, adjust by weighted scores.
        factors: scored values for characteristics (e.g. team: 1.1, product: 0.9)
        weights: relative weights that sum to 1.0 across same keys.
        returns adjusted valuation.
        """
        if set(factors.keys()) != set(weights.keys()):
            raise ValueError("Factors and weights keys must match.")
        multiplier = 0.0
        for k in factors:
            multiplier += factors[k] * weights[k]
        adjusted = baseline_valuation * multiplier
        return {"baseline": baseline_valuation, "multiplier": multiplier, "adjusted_valuation": adjusted}
    
    @staticmethod
    def berkus_method(base: float = 0.0,
                      sound_idea: float = 0.0,
                      prototype: float = 0.0,
                      quality_team: float = 0.0,
                      strategic_partners: float = 0.0,
                      revenues: float = 0.0) -> Dict[str, float]:
        """
        Berkus method: assigns value to five success factors. Values are typically in ranges; pass your chosen estimates.
        Returns sum as pre-money valuation.
        """
        total = base + sound_idea + prototype + quality_team + strategic_partners + revenues
        return {"components": {
                    "base": base,
                    "sound_idea": sound_idea,
                    "prototype": prototype,
                    "quality_team": quality_team,
                    "strategic_partners": strategic_partners,
                    "revenues": revenues
                }, "berkus_valuation": total}
    
    @staticmethod
    def monte_carlo_dcf(revenue0: float,
                        revenue_growth_scenarios: List[Tuple[float, float]],
                        margin_scenarios: List[Tuple[float, float]],
                        years: int = 5,
                        n_simulations: int = 2000,
                        discount_rate: float = 0.30,
                        tax_rate: float = 0.25,
                        capex_pct_mean: float = 0.05) -> Dict[str, object]:
        """
        Monte Carlo DCF: revenue growth and margins are sampled from supplied ranges (low, high).
        revenue_growth_scenarios: list of (low, high) annual growth ranges for each forecast year, or a single tuple applied to all years.
        margin_scenarios: list or single tuple for EBITDA margin ranges.
        Returns distribution percentiles.
        """
        # normalize inputs to per-year lists
        if len(revenue_growth_scenarios) == 1:
            rg_list = [revenue_growth_scenarios[0]] * years
        else:
            rg_list = revenue_growth_scenarios[:years]
        if len(margin_scenarios) == 1:
            m_list = [margin_scenarios[0]] * years
        else:
            m_list = margin_scenarios[:years]
        sims = []
        for s in range(n_simulations):
            r = revenue0
            ufcfs = []
            for i in range(years):
                g = random.uniform(rg_list[i][0], rg_list[i][1])
                r = r * (1 + g)
                m = random.uniform(m_list[i][0], m_list[i][1])
                ebitda = r * m
                capex = r * capex_pct_mean
                ufcf = ebitda * (1 - tax_rate) - capex
                ufcfs.append(ufcf)
            # terminal value by simple multiple of last ebitda
            last_ebitda = r * m
            terminal = last_ebitda * 8.0
            # discount
            ev = 0.0
            for i, cf in enumerate(ufcfs, start=1):
                ev += cf / ((1 + discount_rate) ** i)
            ev += terminal / ((1 + discount_rate) ** years)
            sims.append(ev)
        sims.sort()
        def pct(p): return sims[int(max(0, min(len(sims)-1, math.floor((p/100.0)*len(sims)))))]
        return {
            "n_simulations": n_simulations,
            "p10": pct(10),
            "p25": pct(25),
            "p50": pct(50),
            "p75": pct(75),
            "p90": pct(90),
            "raw_simulation_values_sample": sims[:5]  # small sample to inspect
        }

# --- Demo usage with hypothetical startup ---
if __name__ == "__main__":
    valuator = StartupValuator()
    # DCF example
    dcf_result = valuator.dcf(
        ebitda0=0.5e6,
        revenue0=2.0e6,
        revenue_growth=[0.5, 0.4, 0.3, 0.25, 0.2],
        ebitda_margin=[0.25, 0.28, 0.30, 0.33, 0.35],
        capex_pct=[0.06, 0.05, 0.04, 0.03, 0.03],
        change_in_wc_pct=[0.02, 0.01, 0.01, 0.0, 0.0],
        discount_rate=0.35,
        terminal_growth=0.03
    )
    print("DCF Enterprise Value: ${:,.0f}".format(dcf_result["enterprise_value"]))
    # VC method example
    vc_result = valuator.vc_method(exit_revenue=50e6, exit_revenue_multiple=3.0, investor_target_moic=10.0, years_to_exit=5)
    print("VC post-money present value estimate: ${:,.0f}".format(vc_result["post_money_present_value"]))
    # Comparables example
    comp = valuator.comparables(revenue=5e6, multiple=4.0, adjustments=-0.5e6)
    print("Comparables adjusted value: ${:,.0f}".format(comp["adjusted_value"]))
    # Scorecard example
    score = valuator.scorecard_method(baseline_valuation=2e6,
                                      factors={"team":1.1, "product":1.0, "market":1.05, "traction":0.9},
                                      weights={"team":0.3, "product":0.25, "market":0.2, "traction":0.25})
    print("Scorecard adjusted valuation: ${:,.0f}".format(score["adjusted_valuation"]))
    # Berkus example
    berkus = valuator.berkus_method(base=0.5e6, sound_idea=0.5e6, prototype=0.5e6, quality_team=1.0e6, strategic_partners=0.2e6, revenues=0.3e6)
    print("Berkus valuation: ${:,.0f}".format(berkus["berkus_valuation"]))
    # Monte Carlo DCF example
    mc = valuator.monte_carlo_dcf(revenue0=2e6,
                                  revenue_growth_scenarios=[(0.2, 0.6)],
                                  margin_scenarios=[(0.20, 0.35)],
                                  years=5,
                                  n_simulations=1000,
                                  discount_rate=0.35)
    print("Monte Carlo DCF median (p50) EV: ${:,.0f}".format(mc["p50"]))
