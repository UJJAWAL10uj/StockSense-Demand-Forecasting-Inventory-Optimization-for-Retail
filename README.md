# StockSense Week 7 — Dashboard & Insights

Interactive Streamlit app, historical and future demand series, SKU inventory indicators, and optional inventory-position upload.

## Important data limitations
The source data contains daily units sold by date, store, and item; it does not contain on-hand inventory, on-order units, backorders, supplier lead times, stockout events, or costs. Default 95% cycle service level, 2-week lead time and 1-week review period are illustrative assumptions, clearly marked in the outputs. Replace them with measured inputs before operating the policy.

## Main outputs
- `data/`: calculated CSVs for audit and reuse.
- `charts/`: visual summaries.
- `assumptions.json`: input assumptions and formulas.
- Week 7 includes `app.py`, `requirements.txt`, and `inventory_position_template.csv`.
