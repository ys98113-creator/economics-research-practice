# Economics Research Practice

Data pipeline following the **Medallion Architecture** (Bronze → Silver → Gold).

## Structure

```
bronze/       ← Raw, unmodified data (CSVs, API pulls, scraped data)
silver/       ← Cleaned and validated datasets
gold/         ← Final analysis, outputs, and publication-ready tables
auto_save.sh  ← Run this to save all work to GitHub
```

## Auto-Save

To push all your work to GitHub at any time, run:

```bash
bash ~/economics-research-practice/auto_save.sh
```
