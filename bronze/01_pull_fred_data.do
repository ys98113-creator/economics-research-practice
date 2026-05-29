/* ============================================================
   BRONZE LAYER: Pull raw data from FRED
   Series:
     CSUSHPISA  - S&P/Case-Shiller U.S. National Home Price Index (monthly, SA)
     CPIAUCSL   - CPI All Urban Consumers: All Items (monthly, SA)
     CPILFESL   - Core CPI ex. Food & Energy (monthly, SA)
   Period: Jan 2015 - present (~10 years)

   SETUP (run once in Stata):
     ssc install freduse
   Then get a free API key at: fred.stlouisfed.org -> My Account -> API Keys
   Replace YOUR_API_KEY_HERE below with your key.
   ============================================================ */

global fred_key "YOUR_API_KEY_HERE"
global bronze   "~/economics-research-practice/bronze/raw_data"

* ---------- Housing Price Index ----------
freduse CSUSHPISA, apikey($fred_key) clear
keep if daten >= td(01jan2015)
label variable CSUSHPISA "S&P/Case-Shiller National HPI (SA, Jan2000=100)"
save "$bronze/hpi_raw.dta", replace

* ---------- CPI (Headline) ----------
freduse CPIAUCSL, apikey($fred_key) clear
keep if daten >= td(01jan2015)
label variable CPIAUCSL "CPI All Urban Consumers, All Items (SA, 1982-84=100)"
save "$bronze/cpi_headline_raw.dta", replace

* ---------- Core CPI ----------
freduse CPILFESL, apikey($fred_key) clear
keep if daten >= td(01jan2015)
label variable CPILFESL "Core CPI ex. Food & Energy (SA, 1982-84=100)"
save "$bronze/cpi_core_raw.dta", replace

display "Bronze layer complete. Raw files saved to $bronze"
