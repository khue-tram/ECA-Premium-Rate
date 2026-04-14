"""
ECA Minimum Premium Rate (MPR) Calculator

Based on the OECD Arrangement on Officially Supported Export Credits
(TAD/PG(2023)7, effective 15 July 2023), Annex VI.

MPR Formula (for Country Risk Categories 1-7):
  MPR = { [(ai * HOR + bi) * max(PCC, PCP) / 0.95] * (1 - LCF)
        + [cin * PCC / 0.95 * HOR * (1 - CEF)] }
        * QPFi * PCFi * BTSF * (1 - min(TERM, 0.15))
"""

# ─── Coefficient Tables (Annex VI) ──────────────────────────────────────────────

# Country risk coefficients: a(i) and b(i) for categories 1-7
COUNTRY_RISK_A = {1: 0.090, 2: 0.200, 3: 0.350, 4: 0.550, 5: 0.740, 6: 0.900, 7: 1.100}
COUNTRY_RISK_B = {1: 0.350, 2: 0.350, 3: 0.350, 4: 0.350, 5: 0.750, 6: 1.200, 7: 1.800}

# Buyer risk coefficient c(i,n) — rows: buyer risk category, columns: country risk category
BUYER_RISK_C = {
    "SOV+":   {1: 0.000, 2: 0.000, 3: 0.000, 4: 0.000, 5: 0.000, 6: 0.000, 7: 0.000},
    "SOV/CC0": {1: 0.000, 2: 0.000, 3: 0.000, 4: 0.000, 5: 0.000, 6: 0.000, 7: 0.000},
    "CC1":    {1: 0.110, 2: 0.120, 3: 0.110, 4: 0.100, 5: 0.100, 6: 0.100, 7: 0.125},
    "CC2":    {1: 0.200, 2: 0.212, 3: 0.223, 4: 0.234, 5: 0.246, 6: 0.258, 7: 0.271},
    "CC3":    {1: 0.270, 2: 0.320, 3: 0.320, 4: 0.350, 5: 0.380, 6: 0.480, 7: None},
    "CC4":    {1: 0.405, 2: 0.459, 3: 0.495, 4: 0.540, 5: 0.621, 6: None,  7: None},
    "CC5":    {1: 0.630, 2: 0.675, 3: 0.720, 4: 0.810, 5: None,  6: None,  7: None},
}

# Quality of Product Factor (QPF) — rows: product quality, columns: country risk category
QPF_TABLE = {
    "below_standard": {1: 0.9965, 2: 0.9935, 3: 0.9850, 4: 0.9825, 5: 0.9825, 6: 0.9800, 7: 0.9800},
    "standard":       {1: 1.0000, 2: 1.0000, 3: 1.0000, 4: 1.0000, 5: 1.0000, 6: 1.0000, 7: 1.0000},
    "above_standard": {1: 1.0035, 2: 1.0065, 3: 1.0150, 4: 1.0175, 5: 1.0175, 6: 1.0200, 7: 1.0200},
}

# Percentage of Cover Coefficient for PCF calculation
PCC_COEFFICIENT = {1: 0.00000, 2: 0.00337, 3: 0.00489, 4: 0.01639, 5: 0.03657, 6: 0.05878, 7: 0.08598}

# CRA rating concordance to buyer risk category by country risk category
# Format: {country_risk_cat: {rating: buyer_risk_cat}}
CRA_CONCORDANCE = {
    1: {"AAA": "CC1", "AA+": "CC1", "AA": "CC1", "AA-": "CC1",
        "A+": "CC2", "A": "CC2", "A-": "CC2",
        "BBB+": "CC3", "BBB": "CC3", "BBB-": "CC3",
        "BB+": "CC4", "BB": "CC4",
        "BB-": "CC5", "B+": "CC5", "B": "CC5", "B-": "CC5",
        "CCC+": "CC5", "CCC": "CC5", "CCC-": "CC5"},
    2: {"A+": "CC1", "A": "CC1", "A-": "CC1",
        "BBB+": "CC2", "BBB": "CC2", "BBB-": "CC2",
        "BB+": "CC3", "BB": "CC3",
        "BB-": "CC4",
        "B+": "CC5", "B": "CC5", "B-": "CC5",
        "CCC+": "CC5", "CCC": "CC5", "CCC-": "CC5"},
    3: {"BBB+": "CC1", "BBB": "CC1", "BBB-": "CC1",
        "BB+": "CC2", "BB": "CC2",
        "BB-": "CC3",
        "B+": "CC4",
        "B": "CC5", "B-": "CC5",
        "CCC+": "CC5", "CCC": "CC5", "CCC-": "CC5"},
    4: {"BB+": "CC1", "BB": "CC1",
        "BB-": "CC2",
        "B+": "CC3",
        "B": "CC4",
        "B-": "CC5",
        "CCC+": "CC5", "CCC": "CC5", "CCC-": "CC5"},
    5: {"BB-": "CC1",
        "B+": "CC2",
        "B": "CC3",
        "B-": "CC4",
        "CCC+": "CC4", "CCC": "CC4", "CCC-": "CC4"},
    6: {"B+": "CC1",
        "B": "CC2",
        "B-": "CC3",
        "CCC+": "CC3", "CCC": "CC3", "CCC-": "CC3"},
    7: {"B": "CC1",
        "B-": "CC2",
        "CCC+": "CC2", "CCC": "CC2", "CCC-": "CC2"},
}

# Ratings considered speculative grade (BB+ or worse)
SPECULATIVE_GRADE_RATINGS = {
    "BB+", "BB", "BB-", "B+", "B", "B-",
    "CCC+", "CCC", "CCC-", "CC", "C", "D",
}

# Buyer risk categories equivalent to speculative grade per concordance table
# For each country risk category, which buyer categories correspond to BB+ or worse
SPECULATIVE_BUYER_CATS = {
    1: {"CC4", "CC5"},
    2: {"CC3", "CC4", "CC5"},
    3: {"CC2", "CC3", "CC4", "CC5"},
    4: {"CC1", "CC2", "CC3", "CC4", "CC5"},
    5: {"SOV+", "SOV/CC0", "CC1", "CC2", "CC3", "CC4"},
    6: {"SOV+", "SOV/CC0", "CC1", "CC2", "CC3"},
    7: {"SOV+", "SOV/CC0", "CC1", "CC2"},
}


def calculate_hor(disbursement_period_months: float,
                  repayment_period_years: float,
                  standard_profile: bool = True,
                  weighted_average_life: float | None = None) -> float:
    """
    Calculate the Horizon of Risk (HOR) in years.

    Args:
        disbursement_period_months: Length of disbursement period in months.
        repayment_period_years: Length of the repayment period in years.
        standard_profile: True for standard (equal semi-annual principal repayments).
        weighted_average_life: WAL of repayment period in years (required if non-standard).

    Returns:
        HOR in years.
    """
    disbursement_years = disbursement_period_months / 12.0
    if standard_profile:
        return disbursement_years * 0.5 + repayment_period_years
    else:
        if weighted_average_life is None:
            raise ValueError("weighted_average_life is required for non-standard profiles")
        equivalent_repayment = (weighted_average_life - 0.25) / 0.5
        return disbursement_years * 0.5 + equivalent_repayment


def get_buyer_risk_category(country_risk_cat: int,
                            cra_rating: str | None = None,
                            buyer_risk_cat: str | None = None) -> str:
    """
    Determine the buyer risk category.

    Either provide a CRA rating (which is mapped via the concordance table)
    or directly specify the buyer risk category.

    Args:
        country_risk_cat: Country risk category (1-7).
        cra_rating: Optional CRA letter rating (e.g. "BBB+", "BB-").
        buyer_risk_cat: Optional direct buyer risk category (e.g. "SOV+", "CC2").

    Returns:
        Buyer risk category string.
    """
    if buyer_risk_cat is not None:
        return buyer_risk_cat

    if cra_rating is not None:
        # Check for SOV designation
        if cra_rating.upper() in ("SOV", "SOV/CC0"):
            return "SOV/CC0"
        if cra_rating.upper() == "SOV+":
            return "SOV+"
        concordance = CRA_CONCORDANCE.get(country_risk_cat, {})
        cat = concordance.get(cra_rating)
        if cat is None:
            raise ValueError(
                f"CRA rating '{cra_rating}' not valid for country risk category {country_risk_cat}"
            )
        return cat

    raise ValueError("Either cra_rating or buyer_risk_cat must be provided")


def is_speculative_grade(cra_rating: str | None,
                         buyer_risk_cat: str,
                         country_risk_cat: int) -> bool:
    """
    Check if the obligor is speculative grade (BB+ or worse).
    Uses the CRA rating directly if available, otherwise checks the
    buyer category against the concordance-derived speculative grade
    mapping for the given country risk category.
    SOV+ and SOV/CC0 in country risk categories 5-7 are also considered
    speculative grade per Annex VI.
    """
    if cra_rating and cra_rating in SPECULATIVE_GRADE_RATINGS:
        return True
    spec_cats = SPECULATIVE_BUYER_CATS.get(country_risk_cat, set())
    return buyer_risk_cat in spec_cats


def calculate_pcf(pcc: float, pcp: float, country_risk_cat: int) -> float:
    """
    Calculate the Percentage of Cover Factor (PCF).

    Args:
        pcc: Commercial (buyer) risk percentage of cover (decimal, e.g. 0.95).
        pcp: Political (country) risk percentage of cover (decimal, e.g. 0.95).
        country_risk_cat: Country risk category (1-7).

    Returns:
        PCF value.
    """
    max_pc = max(pcc, pcp)
    if max_pc <= 0.95:
        return 1.0
    coeff = PCC_COEFFICIENT[country_risk_cat]
    return 1.0 + ((max_pc - 0.95) / 0.05) * coeff


def calculate_term_adjustment(hor: float,
                              cra_rating: str | None,
                              buyer_risk_cat: str,
                              country_risk_cat: int) -> float:
    """
    Calculate the Term Adjustment Factor (TERM).

    Only applicable for speculative grade obligors with HOR > 10 years.
    TERM = 0.018 * (HOR - 10), capped at 0.15.

    Returns:
        TERM value (0 if not applicable).
    """
    if not is_speculative_grade(cra_rating, buyer_risk_cat, country_risk_cat):
        return 0.0
    if hor <= 10.0:
        return 0.0
    return min(0.018 * (hor - 10.0), 0.15)


def calculate_mpr(
    country_risk_cat: int,
    disbursement_period_months: float,
    repayment_period_years: float,
    pcc: float = 0.95,
    pcp: float = 0.95,
    cra_rating: str | None = None,
    buyer_risk_cat: str | None = None,
    product_quality: str = "standard",
    cef: float = 0.0,
    local_currency_mitigation: bool = False,
    lcf: float = 0.0,
    standard_profile: bool = True,
    weighted_average_life: float | None = None,
) -> dict:
    """
    Calculate the OECD Minimum Premium Rate (MPR) for Country Risk Categories 1-7.

    Args:
        country_risk_cat: Country risk category (1-7).
        disbursement_period_months: Disbursement period in months.
        repayment_period_years: Repayment period in years.
        pcc: Commercial (buyer) risk percentage of cover as decimal (default 0.95).
        pcp: Political (country) risk percentage of cover as decimal (default 0.95).
        cra_rating: CRA letter rating of obligor (e.g. "BBB+", "BB-").
        buyer_risk_cat: Direct buyer risk category (e.g. "SOV+", "SOV/CC0", "CC1"-"CC5").
        product_quality: "below_standard", "standard", or "above_standard".
        cef: Credit Enhancement Factor (0 to 0.35).
        local_currency_mitigation: Whether local currency risk mitigation is applied.
        lcf: Local Currency Factor (0 to 0.2, only if local_currency_mitigation=True).
        standard_profile: True for standard repayment profile.
        weighted_average_life: WAL in years (required if standard_profile=False).

    Returns:
        Dictionary with MPR (%) and intermediate calculation values.
    """
    # Validate inputs
    if country_risk_cat not in range(1, 8):
        raise ValueError(f"country_risk_cat must be 1-7, got {country_risk_cat}")
    if not (0 < pcc <= 1.0):
        raise ValueError(f"pcc must be in (0, 1], got {pcc}")
    if not (0 < pcp <= 1.0):
        raise ValueError(f"pcp must be in (0, 1], got {pcp}")
    if product_quality not in QPF_TABLE:
        raise ValueError(f"product_quality must be one of {list(QPF_TABLE.keys())}")
    if not (0.0 <= cef <= 0.35):
        raise ValueError(f"cef must be in [0, 0.35], got {cef}")
    if local_currency_mitigation and not (0.0 <= lcf <= 0.2):
        raise ValueError(f"lcf must be in [0, 0.2], got {lcf}")

    # Determine buyer risk category
    brc = get_buyer_risk_category(country_risk_cat, cra_rating, buyer_risk_cat)

    # Get coefficients
    ai = COUNTRY_RISK_A[country_risk_cat]
    bi = COUNTRY_RISK_B[country_risk_cat]
    cin = BUYER_RISK_C[brc][country_risk_cat]
    if cin is None:
        raise ValueError(
            f"Buyer risk category '{brc}' is not available for "
            f"country risk category {country_risk_cat}"
        )

    # HOR
    hor = calculate_hor(
        disbursement_period_months, repayment_period_years,
        standard_profile, weighted_average_life
    )

    # LCF
    effective_lcf = lcf if local_currency_mitigation else 0.0

    # QPF
    qpf = QPF_TABLE[product_quality][country_risk_cat]

    # PCF
    pcf = calculate_pcf(pcc, pcp, country_risk_cat)

    # BTSF
    btsf = 0.9 if brc == "SOV+" else 1.0

    # TERM
    term = calculate_term_adjustment(hor, cra_rating, brc, country_risk_cat)

    # ─── MPR Formula ────────────────────────────────────────────────────────────
    max_pc = max(pcc, pcp)

    # Country risk component
    country_component = (ai * hor + bi) * max_pc / 0.95 * (1.0 - effective_lcf)

    # Buyer risk component
    buyer_component = cin * pcc / 0.95 * hor * (1.0 - cef)

    # Base MPR before adjustments
    base_mpr = country_component + buyer_component

    # Apply factors
    mpr = base_mpr * qpf * pcf * btsf * (1.0 - min(term, 0.15))

    return {
        "mpr_percent": round(mpr, 6),
        "country_risk_category": country_risk_cat,
        "buyer_risk_category": brc,
        "hor_years": round(hor, 4),
        "ai": ai,
        "bi": bi,
        "cin": cin,
        "pcc": pcc,
        "pcp": pcp,
        "max_pc": max_pc,
        "cef": cef,
        "lcf": effective_lcf,
        "qpf": qpf,
        "pcf": round(pcf, 6),
        "btsf": btsf,
        "term": round(term, 6),
        "country_component": round(country_component, 6),
        "buyer_component": round(buyer_component, 6),
        "product_quality": product_quality,
    }


# ─── Interactive CLI ─────────────────────────────────────────────────────────────

VALID_CRA_RATINGS = [
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
    "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
    "B+", "B", "B-", "CCC+", "CCC", "CCC-",
]

VALID_BUYER_CATS = ["SOV+", "SOV/CC0", "CC1", "CC2", "CC3", "CC4", "CC5"]


def print_instructions():
    """Print detailed instructions for all inputs."""
    print("""
================================================================================
              OECD ECA MINIMUM PREMIUM RATE (MPR) CALCULATOR
              Based on TAD/PG(2023)7, Annex VI (July 2023)
================================================================================

This tool calculates the Minimum Premium Rate for export credits with obligors
in Country Risk Categories 1-7. All results are expressed as a percentage of
principal (flat, upfront-equivalent basis).

────────────────────────────────────────────────────────────────────────────────
                           INPUT GUIDE
────────────────────────────────────────────────────────────────────────────────

 1) COUNTRY RISK CATEGORY  (required, integer 1-7)
    ─ The OECD country risk classification of the obligor's country.
    ─ Category 0 is NOT covered here (Market Benchmark rules apply).
    ─ Published at: https://www.oecd.org/trade/topics/export-credits/
    ─ Examples: USA=0, UK=0, Thailand=3, Vietnam=5, Nigeria=6

 2) DISBURSEMENT PERIOD  (required, in months, can be 0)
    ─ The time from first drawdown to the starting point of credit.
    ─ Enter 0 if the full amount is disbursed upfront.

 3) REPAYMENT PERIOD  (required, in years, e.g. 8.5)
    ─ The length of the repayment period.
    ─ Standard profile: equal semi-annual instalments of principal.

 4) BUYER RISK  (required, choose ONE method)
    Method A — CRA Credit Rating of the obligor:
      AAA, AA+, AA, AA-, A+, A, A-, BBB+, BBB, BBB-,
      BB+, BB, BB-, B+, B, B-, CCC+, CCC, CCC-
      The rating is mapped to a buyer risk category (CC1-CC5) based on
      the country risk category via the concordance table.

    Method B — Direct buyer risk category:
      SOV+       = Better than Sovereign (10% discount on SOV rate)
      SOV/CC0    = Sovereign
      CC1 to CC5 = Corporate buyer categories (CC5 = worst)

 5) COMMERCIAL RISK COVER (PCC)  (default: 95%)
    ─ The percentage of buyer/commercial risk covered by the ECA.
    ─ Enter as a number, e.g. 95 for 95%, or 100 for 100%.

 6) POLITICAL RISK COVER (PCP)  (default: 95%)
    ─ The percentage of political/country risk covered by the ECA.
    ─ Enter as a number, e.g. 95 for 95%, or 100 for 100%.

 7) PRODUCT QUALITY  (default: standard)
    1 = Below standard  (insurance without interest cover during waiting period)
    2 = Standard        (insurance with interest cover / direct lending)
    3 = Above standard  (guarantee)

 8) CREDIT ENHANCEMENT FACTOR (CEF)  (default: 0)
    ─ Reflects buyer risk credit enhancements (e.g. asset security, escrow).
    ─ Range: 0.00 to 0.35.  Enter 0 if none.

 9) REPAYMENT PROFILE  (default: standard)
    ─ Standard = equal semi-annual principal repayments.
    ─ If non-standard, you will also need to provide the Weighted Average
      Life (WAL) of the repayment period in years.

10) LOCAL CURRENCY MITIGATION  (default: No)
    ─ If the transaction uses local currency financing as country risk
      mitigation, enter the Local Currency Factor (LCF, max 0.20).
================================================================================
""")


def prompt_float(msg, default=None, min_val=None, max_val=None):
    """Prompt for a float with optional default and range validation."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {msg}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            val = float(raw)
        except ValueError:
            print(f"    ** Invalid number. Please try again.")
            continue
        if min_val is not None and val < min_val:
            print(f"    ** Must be >= {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"    ** Must be <= {max_val}.")
            continue
        return val


def prompt_int(msg, default=None, min_val=None, max_val=None):
    """Prompt for an integer with optional default and range validation."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {msg}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
        except ValueError:
            print(f"    ** Invalid integer. Please try again.")
            continue
        if min_val is not None and val < min_val:
            print(f"    ** Must be >= {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"    ** Must be <= {max_val}.")
            continue
        return val


def prompt_choice(msg, choices, default=None):
    """Prompt for a choice from a list."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"  {msg}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        if raw.upper() in [c.upper() for c in choices]:
            # return the properly-cased version
            for c in choices:
                if c.upper() == raw.upper():
                    return c
        print(f"    ** Invalid choice. Options: {', '.join(choices)}")


def prompt_yes_no(msg, default="n"):
    """Prompt for yes/no."""
    while True:
        suffix = f" [{'Y/n' if default == 'y' else 'y/N'}]"
        raw = input(f"  {msg}{suffix}: ").strip().lower()
        if raw == "":
            return default == "y"
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("    ** Please enter y or n.")


def interactive_calculate():
    """Run the interactive MPR calculator."""
    print_instructions()
    print("Enter your transaction parameters below.")
    print("Press Enter to accept [default] values shown in brackets.\n")

    # ── 1. Country Risk Category ────────────────────────────────────────────
    print("─── 1. COUNTRY RISK CATEGORY ───")
    country_cat = prompt_int("Country risk category (1-7)", min_val=1, max_val=7)

    # ── 2. Disbursement Period ──────────────────────────────────────────────
    print("\n─── 2. DISBURSEMENT PERIOD ───")
    disb_months = prompt_float("Disbursement period in months", default=0, min_val=0)

    # ── 3. Repayment Period ─────────────────────────────────────────────────
    print("\n─── 3. REPAYMENT PERIOD ───")
    repay_years = prompt_float("Repayment period in years", min_val=0.5)

    # ── 4. Buyer Risk ───────────────────────────────────────────────────────
    print("\n─── 4. BUYER RISK ───")
    print("  Choose input method:")
    print("    A = CRA credit rating (e.g. BBB+, BB-, B)")
    print("    B = Direct buyer risk category (e.g. SOV/CC0, CC1, CC3)")
    method = prompt_choice("Method (A or B)", ["A", "B"])

    cra_rating = None
    buyer_risk_cat = None
    if method == "A":
        print(f"  Valid ratings: {', '.join(VALID_CRA_RATINGS)}")
        cra_rating = prompt_choice("CRA rating", VALID_CRA_RATINGS)
    else:
        print(f"  Valid categories: {', '.join(VALID_BUYER_CATS)}")
        buyer_risk_cat = prompt_choice("Buyer risk category", VALID_BUYER_CATS)

    # ── 5. Percentage of Cover ──────────────────────────────────────────────
    print("\n─── 5. PERCENTAGE OF COVER ───")
    pcc_pct = prompt_float("Commercial (buyer) risk cover % (e.g. 95)", default=95, min_val=1, max_val=100)
    pcp_pct = prompt_float("Political (country) risk cover % (e.g. 95)", default=95, min_val=1, max_val=100)
    pcc = pcc_pct / 100.0
    pcp = pcp_pct / 100.0

    # ── 6. Product Quality ──────────────────────────────────────────────────
    print("\n─── 6. PRODUCT QUALITY ───")
    print("    1 = Below standard (insurance w/o interest cover)")
    print("    2 = Standard (insurance with interest cover / direct lending)")
    print("    3 = Above standard (guarantee)")
    pq_choice = prompt_int("Product quality (1/2/3)", default=2, min_val=1, max_val=3)
    product_quality = {1: "below_standard", 2: "standard", 3: "above_standard"}[pq_choice]

    # ── 7. Credit Enhancement Factor ────────────────────────────────────────
    print("\n─── 7. CREDIT ENHANCEMENT FACTOR (CEF) ───")
    cef = prompt_float("CEF (0.00 to 0.35, 0=none)", default=0, min_val=0, max_val=0.35)

    # ── 8. Repayment Profile ────────────────────────────────────────────────
    print("\n─── 8. REPAYMENT PROFILE ───")
    standard_profile = prompt_yes_no("Standard repayment profile (equal semi-annual)?", default="y")
    wal = None
    if not standard_profile:
        wal = prompt_float("Weighted average life of repayment period (years)", min_val=0.25)

    # ── 9. Local Currency Mitigation ────────────────────────────────────────
    print("\n─── 9. LOCAL CURRENCY MITIGATION ───")
    lc_mit = prompt_yes_no("Apply local currency mitigation?", default="n")
    lcf = 0.0
    if lc_mit:
        lcf = prompt_float("Local Currency Factor (0.00 to 0.20)", default=0.1, min_val=0, max_val=0.2)

    # ── Calculate ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  CALCULATING...")
    print("=" * 70)

    try:
        result = calculate_mpr(
            country_risk_cat=country_cat,
            disbursement_period_months=disb_months,
            repayment_period_years=repay_years,
            pcc=pcc,
            pcp=pcp,
            cra_rating=cra_rating,
            buyer_risk_cat=buyer_risk_cat,
            product_quality=product_quality,
            cef=cef,
            local_currency_mitigation=lc_mit,
            lcf=lcf,
            standard_profile=standard_profile,
            weighted_average_life=wal,
        )
    except ValueError as e:
        print(f"\n  !! ERROR: {e}")
        return

    # ── Print Results ───────────────────────────────────────────────────────
    print(f"""
================================================================================
                          MPR CALCULATION RESULTS
================================================================================

  INPUTS
  ──────
  Country Risk Category     : {result['country_risk_category']}
  Buyer Risk Category       : {result['buyer_risk_category']}
  Disbursement Period       : {disb_months} months
  Repayment Period          : {repay_years} years
  {"Weighted Average Life     : " + str(wal) + " years" if wal else "Repayment Profile         : Standard (equal semi-annual)"}
  Commercial Risk Cover     : {result['pcc']*100:.1f}%
  Political Risk Cover      : {result['pcp']*100:.1f}%
  Product Quality           : {result['product_quality'].replace('_', ' ').title()}
  Credit Enhancement (CEF)  : {result['cef']}
  Local Currency Factor     : {result['lcf']}

  COEFFICIENTS
  ────────────
  a(i)  - country coeff     : {result['ai']}
  b(i)  - country constant  : {result['bi']}
  c(i,n)- buyer coeff       : {result['cin']}
  QPF   - quality factor    : {result['qpf']}
  PCF   - cover factor      : {result['pcf']:.6f}
  BTSF  - better than sov   : {result['btsf']}
  TERM  - term adjustment   : {result['term']:.6f}

  CALCULATION
  ───────────
  Horizon of Risk (HOR)     : {result['hor_years']} years
  Country Risk Component    : {result['country_component']:.4f}%
  Buyer Risk Component      : {result['buyer_component']:.4f}%

  ╔══════════════════════════════════════════════════╗
  ║                                                  ║
  ║   MINIMUM PREMIUM RATE (MPR) = {result['mpr_percent']:>8.4f}%         ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝

  (expressed as % of principal, flat upfront-equivalent basis)
================================================================================
""")


if __name__ == "__main__":
    while True:
        interactive_calculate()
        again = prompt_yes_no("\nCalculate another transaction?", default="y")
        if not again:
            print("\nGoodbye!")
            break
