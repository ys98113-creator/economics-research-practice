/* ============================================================
   GOLD LAYER: Data Exploration & Visualization
   Input:  silver/cleaned/housing_inflation_panel.dta
   Output: gold/outputs/ (graphs + summary tables)
   ============================================================ */

global silver  "~/economics-research-practice/silver/cleaned"
global output  "~/economics-research-practice/gold/outputs"

use "$silver/housing_inflation_panel.dta", clear

* ============================================================
* 1. SUMMARY STATISTICS
* ============================================================
estpost summarize hpi_yoy inflation_yoy core_inf_yoy, detail
esttab using "$output/summary_stats.csv", ///
    cells("mean sd min p25 p50 p75 max") ///
    label replace title("Summary Statistics (Monthly YoY %)")

* ============================================================
* 2. TIME SERIES: HPI Index Level
* ============================================================
twoway line hpi ym, ///
    title("U.S. National Home Price Index") ///
    subtitle("S&P/Case-Shiller, Seasonally Adjusted") ///
    xtitle("") ytitle("Index (Jan 2000 = 100)") ///
    lcolor(navy) lwidth(medthick) ///
    tlabel(, format(%tmMon-CY)) ///
    scheme(s2color)
graph export "$output/hpi_level.png", replace width(1200)

* ============================================================
* 3. TIME SERIES: YoY Growth Rates (HPI vs Inflation)
* ============================================================
twoway (line hpi_yoy ym, lcolor(navy) lwidth(medthick)) ///
       (line inflation_yoy ym, lcolor(cranberry) lwidth(medthick) lpattern(dash)) ///
       (line core_inf_yoy ym, lcolor(orange) lwidth(medium) lpattern(shortdash)), ///
    title("Housing Price Growth vs. Inflation") ///
    subtitle("Year-over-Year % Change, Monthly") ///
    xtitle("") ytitle("YoY Change (%)") ///
    legend(order(1 "HPI (Case-Shiller)" 2 "CPI Headline" 3 "CPI Core") ///
           position(6) rows(1)) ///
    yline(0, lcolor(gray) lpattern(dot)) ///
    tlabel(, format(%tmMon-CY)) ///
    scheme(s2color)
graph export "$output/hpi_vs_inflation_yoy.png", replace width(1200)

* ============================================================
* 4. SCATTER: HPI growth vs Inflation (correlation)
* ============================================================
twoway scatter hpi_yoy inflation_yoy, ///
    mlabel(ym) mlabsize(tiny) mcolor(navy%50) ///
    || lfit hpi_yoy inflation_yoy, lcolor(cranberry) ///
    title("Housing Price Growth vs. Headline Inflation") ///
    xtitle("CPI Inflation YoY (%)") ytitle("HPI Growth YoY (%)") ///
    legend(off) scheme(s2color)
graph export "$output/scatter_hpi_vs_cpi.png", replace width(1000)

* ============================================================
* 5. CORRELATION TABLE
* ============================================================
pwcorr hpi_yoy inflation_yoy core_inf_yoy, star(0.05) obs
estpost correlate hpi_yoy inflation_yoy core_inf_yoy, matrix listwise
esttab using "$output/correlation_table.csv", replace ///
    title("Pairwise Correlations: HPI Growth & Inflation")

* ============================================================
* 6. QUICK STATS: Print to console
* ============================================================
display "=== DATA EXPLORATION SUMMARY ==="
display "Time range: " %tm mofd(date[1]) " to " %tm mofd(date[_N])
display "Observations: " _N

qui sum hpi_yoy
display "Avg HPI YoY growth:   " %5.2f r(mean) "%  (min: " %5.2f r(min) "%, max: " %5.2f r(max) "%)"

qui sum inflation_yoy
display "Avg CPI inflation:    " %5.2f r(mean) "%  (min: " %5.2f r(min) "%, max: " %5.2f r(max) "%)"

qui sum core_inf_yoy
display "Avg Core inflation:   " %5.2f r(mean) "%  (min: " %5.2f r(min) "%, max: " %5.2f r(max) "%)"

display "Outputs saved to: $output"
display "Next step: run gold/analysis/04_forecast.do"
