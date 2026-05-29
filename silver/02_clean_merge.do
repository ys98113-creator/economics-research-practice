/* ============================================================
   SILVER LAYER: Clean, merge, and compute derived variables
   Inputs:  bronze/raw_data/hpi_raw.dta
            bronze/raw_data/cpi_headline_raw.dta
            bronze/raw_data/cpi_core_raw.dta
   Output:  silver/cleaned/housing_inflation_panel.dta
   ============================================================ */

global bronze  "~/economics-research-practice/bronze/raw_data"
global silver  "~/economics-research-practice/silver/cleaned"

* ---------- Load and prep HPI ----------
use "$bronze/hpi_raw.dta", clear
rename CSUSHPISA hpi
rename daten date
sort date
save "$silver/hpi_clean.dta", replace

* ---------- Load and prep Headline CPI ----------
use "$bronze/cpi_headline_raw.dta", clear
rename CPIAUCSL cpi
rename daten date
sort date
save "$silver/cpi_clean.dta", replace

* ---------- Load and prep Core CPI ----------
use "$bronze/cpi_core_raw.dta", clear
rename CPILFESL cpi_core
rename daten date
sort date
save "$silver/cpi_core_clean.dta", replace

* ---------- Merge all three on date ----------
use "$silver/hpi_clean.dta", clear
merge 1:1 date using "$silver/cpi_clean.dta",     nogen keep(3)
merge 1:1 date using "$silver/cpi_core_clean.dta", nogen keep(3)

* ---------- Set monthly time series ----------
gen ym = mofd(date)
format ym %tm
tsset ym

* ---------- Compute year-over-year growth rates (%) ----------
gen hpi_yoy      = (hpi / L12.hpi - 1) * 100
gen inflation_yoy = (cpi / L12.cpi - 1) * 100
gen core_inf_yoy  = (cpi_core / L12.cpi_core - 1) * 100

label variable hpi          "Case-Shiller HPI (index level)"
label variable cpi          "CPI Headline (index level)"
label variable cpi_core     "CPI Core (index level)"
label variable hpi_yoy      "HPI YoY growth (%)"
label variable inflation_yoy "Headline CPI inflation YoY (%)"
label variable core_inf_yoy  "Core CPI inflation YoY (%)"

* ---------- Drop first 12 months (no lag available) ----------
drop if missing(hpi_yoy)

* ---------- Basic validation ----------
summarize hpi cpi cpi_core hpi_yoy inflation_yoy core_inf_yoy
mdesc

save "$silver/housing_inflation_panel.dta", replace
display "Silver layer complete. Merged panel saved."
