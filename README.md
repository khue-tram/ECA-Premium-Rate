# ECA Minimum Premium Rate (MPR) Calculator

Calculator for the OECD Minimum Premium Rate for officially supported export credits, based on **TAD/PG(2023)7** (Arrangement on Officially Supported Export Credits, effective 15 July 2023), **Annex VI**.

---

## How to Run

Open a terminal in this folder and run:

```
python eca_premium_calculator.py
```

The program will display an input guide, then prompt you for each parameter step by step. Press **Enter** to accept the default value shown in `[brackets]`.

After the calculation it will ask if you want to run another transaction.

---

## Inputs — How to Identify Each Parameter

### 1. Country Risk Category (required)

| What it is | The OECD country risk classification of the **obligor's country** (not the exporter's country). |
|---|---|
| **Where to find it** | Published by the OECD at [oecd.org/en/topics/country-risk-classification](https://www.oecd.org/en/topics/country-risk-classification.html). Updated regularly. |
| **Range** | Integer **1** (lowest risk) to **7** (highest risk). |
| **Note** | Category **0** countries (e.g. USA, UK, Germany, Japan) are **Market Benchmark** transactions — they use a different pricing method and are **not** covered by this calculator. |

**Selected country examples:**

| Category | Countries (examples) |
|----------|---------------------|
| 0 | USA, UK, Germany, Japan, France, Australia, Canada |
| 1 | South Korea, Chile, Czech Republic |
| 2 | China, Saudi Arabia, Malaysia, Poland |
| 3 | Thailand, India, Indonesia, Mexico, Philippines |
| 4 | Vietnam, Brazil, Colombia, Côte d'Ivoire |
| 5 | Bangladesh, Kenya, Cambodia, Senegal |
| 6 | Nigeria, Egypt, Ghana, Tanzania |
| 7 | Pakistan, Ethiopia, Mozambique, Myanmar |

> Always verify the current classification on the OECD website — countries are reclassified periodically.

---

### 2. Disbursement Period (required)

| What it is | The time (in **months**) between the **first drawdown** of the credit and the **starting point of credit** (i.e. when repayment begins). |
|---|---|
| **Where to find it** | The loan/credit agreement or term sheet. |
| **Enter** | Number of months. Enter **0** if the full amount is disbursed in a single upfront payment. |
| **Example** | A construction project that draws down funds over 18 months → enter `18`. |

---

### 3. Repayment Period (required)

| What it is | The length of the **repayment period** in **years**, starting from the starting point of credit. |
|---|---|
| **Where to find it** | The loan/credit agreement or term sheet. |
| **Enter** | Number in years (decimals OK, e.g. `8.5` for 8 years 6 months). |
| **OECD max** | Typically 8.5 years for Cat 1 countries, up to 10 years for others (extended terms possible for certain sectors). |

---

### 4. Buyer Risk — CRA Rating or Buyer Risk Category (required)

You choose **one** of two methods:

#### Method A: CRA Credit Rating

| What it is | The **foreign currency, senior unsecured** credit rating of the **obligor** (or guarantor) from an accredited Credit Rating Agency (S&P, Moody's, Fitch). |
|---|---|
| **Where to find it** | Bloomberg, the CRA websites, or the obligor's financial disclosures. Use the **best available** rating if rated by multiple agencies. |
| **Valid values** | `AAA`, `AA+`, `AA`, `AA-`, `A+`, `A`, `A-`, `BBB+`, `BBB`, `BBB-`, `BB+`, `BB`, `BB-`, `B+`, `B`, `B-`, `CCC+`, `CCC`, `CCC-` |

The calculator automatically maps the CRA rating to the appropriate buyer risk category (CC1–CC5) based on the country risk category, using the OECD concordance table.

**Concordance overview** (which CRA ratings map to which buyer category depends on country risk):

| Country Risk | CC1 | CC2 | CC3 | CC4 | CC5 |
|:------------:|-----|-----|-----|-----|-----|
| 1 | AAA to AA- | A+ to A- | BBB+ to BBB- | BB+ to BB | BB- and below |
| 2 | A+ to A- | BBB+ to BBB- | BB+ to BB | BB- | B+ and below |
| 3 | BBB+ to BBB- | BB+ to BB | BB- | B+ | B and below |
| 4 | BB+ to BB | BB- | B+ | B | B- and below |
| 5 | BB- | B+ | B | B- to CCC- | n/a |
| 6 | B+ | B | B- to CCC- | n/a | n/a |
| 7 | B | B- to CCC- | n/a | n/a | n/a |

#### Method B: Direct Buyer Risk Category

| Category | Description |
|----------|-------------|
| **SOV+** | Better than Sovereign — obligor rated better than its sovereign by a CRA. Gets a 10% discount on the SOV rate. |
| **SOV/CC0** | Sovereign — the obligor is the government itself, or equivalent to sovereign risk. |
| **CC1** | Strongest non-sovereign category for the given country. |
| **CC2** | Good credit quality relative to the country. |
| **CC3** | Average credit quality. |
| **CC4** | Below average — higher risk. |
| **CC5** | Weakest category (not available for all country categories). |

> **Tip:** If the obligor is a government ministry, central bank, or sovereign entity → use **SOV/CC0**. If a private corporation with a CRA rating → use **Method A**.

---

### 5. Percentage of Cover (defaults: 95%)

| Parameter | What it is |
|-----------|------------|
| **PCC** — Commercial (buyer) risk cover | The % of the credit amount the ECA covers for **buyer default** risk (non-payment by the obligor). |
| **PCP** — Political (country) risk cover | The % of the credit amount the ECA covers for **political/country** risk (transfer restrictions, war, expropriation, etc.). |

| Where to find it | The ECA insurance policy or cover terms. |
|---|---|
| **Enter** | A number like `95` for 95% or `100` for 100%. |
| **Typical values** | Most ECAs cover 95%. Some provide up to 100%. |
| **Default** | 95% for both if you just press Enter. |

> When cover exceeds 95%, the MPR formula applies an additional Percentage of Cover Factor (PCF) that increases the premium — this is handled automatically.

---

### 6. Product Quality (default: Standard)

| Choice | Description | Examples |
|--------|-------------|---------|
| **1 — Below Standard** | Insurance **without** cover of accrued interest during the claims waiting period (or with a surcharge for that cover). | Basic political risk insurance |
| **2 — Standard** | Insurance **with** cover of accrued interest during the claims waiting period (no surcharge), or direct lending/financing by the ECA. | Most ECA-backed loans, direct ECA credits |
| **3 — Above Standard** | Unconditional guarantee of repayment by the ECA. | ECA guarantee wrapping a commercial bank loan |

| Where to find it | The ECA product description / policy terms. |
|---|---|
| **Default** | Standard (option 2) — this is the most common. |

---

### 7. Credit Enhancement Factor — CEF (default: 0)

| What it is | A discount factor (0 to 0.35) applied to the **buyer risk component** of the premium when the transaction benefits from credit enhancements that reduce buyer risk. |
|---|---|
| **Range** | `0.00` (no enhancement) to `0.35` (maximum allowed). |
| **Where to find it** | Determined by the ECA/Participant based on the type of security. |

**Types of enhancements (Annex X of the Arrangement):**

| Enhancement | Max CEF | Notes |
|-------------|---------|-------|
| Assignment of Contract Proceeds / Receivables | 0.10 | Enforceable assignment of borrower's contracts with strong off-takers |
| Asset-Based Security | 0.25 | Mobile, valuable assets (locomotives, medical/construction equipment) |
| Fixed Asset Security | 0.15 | Integrated equipment (turbines, manufacturing machinery) |
| Escrow Account | up to 0.10 | CEF = escrowed amount as % of credit, capped at 0.10 |
| **Combined maximum** | **0.35** | Asset-Based and Fixed Asset **cannot** be used together |

> Enter `0` if there are no buyer risk credit enhancements (most common).

---

### 8. Repayment Profile (default: Standard)

| Option | Description |
|--------|-------------|
| **Standard (Y)** | Equal semi-annual instalments of principal, beginning 6 months after the starting point of credit. This is the typical ECA repayment structure. |
| **Non-standard (N)** | Any other repayment schedule (e.g. bullet, balloon, sculpted). If selected, you must also provide the **Weighted Average Life (WAL)** of the repayment period in years. |

**How to calculate WAL** (if non-standard):

$$WAL = \frac{\sum (P_i \times t_i)}{\sum P_i}$$

Where $P_i$ is each principal repayment amount and $t_i$ is the time in years from the starting point of credit to that payment.

---

### 9. Local Currency Mitigation (default: No)

| What it is | A discount (up to 20%) on the **country risk component** of the premium when the loan is denominated in the **obligor's local currency**, reducing transfer/convertibility risk. |
|---|---|
| **When to use** | Only if the export credit is financed in the local currency of the obligor's country **and** is structured as a local currency country risk mitigation per Annex X. |
| **LCF range** | `0.00` to `0.20` |
| **Default** | No / 0 — most export credits are in USD or EUR. |

---

## Formula Reference

The full MPR formula (Annex VI):

$$MPR = \left[\left(a_i \cdot HOR + b_i\right) \cdot \frac{\max(PCC, PCP)}{0.95} \cdot (1 - LCF) + c_{i,n} \cdot \frac{PCC}{0.95} \cdot HOR \cdot (1 - CEF)\right] \times QPF_i \times PCF_i \times BTSF \times (1 - \min(TERM, 0.15))$$

Where:
- **HOR** = Disbursement period (years) × 0.5 + Repayment period (years)
- **PCF** = 1 if max(PCC,PCP) ≤ 0.95, otherwise adjusted upward
- **BTSF** = 0.9 if SOV+, otherwise 1.0
- **TERM** = 0.018 × (HOR − 10), only for speculative-grade obligors with HOR > 10, capped at 0.15
- **Result** is expressed as **% of principal** on a flat, upfront-equivalent basis

---

## Example

```
Country Risk Category     : 5  (e.g. Vietnam)
Disbursement Period       : 6 months
Repayment Period          : 10 years
Buyer Risk                : BB- (CRA rating → maps to CC1 for Cat 5)
Cover                     : 95% / 95%
Product Quality           : Standard
CEF                       : 0

→ HOR  = 0.5 × (6/12) + 10 = 10.25 years
→ MPR  = 9.3179%
```

---

## Source

OECD, *Arrangement on Officially Supported Export Credits*, TAD/PG(2023)7, July 2023.  
PDF included in this folder: `TAD-PG(2023)7.en.pdf`
