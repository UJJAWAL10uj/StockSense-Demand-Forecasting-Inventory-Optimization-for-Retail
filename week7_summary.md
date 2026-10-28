# StockSense Week 7 — Dashboard & Insights

## What is included
- Streamlit dashboard (`app.py`) with controls for store, item, supplier lead time, review period, and service level.
- Historical weekly demand (260 weeks), 13-week seasonal-naive forecast, SKU-level reorder point and order-up-to calculations, variability indicators, and ABC class.
- Optional inventory-position CSV upload. Once real stock data is uploaded, the dashboard calculates `inventory position = on hand + on order − backorders` and labels rows `REORDER NOW` when inventory position is at/below the reorder point, otherwise `WATCH`/`OK` by configured coverage logic.
- Forecast and inventory-indicator overview plus prioritization by 13-week forecast volume and buffer requirement.
- Workbook data exports and chart images for use without running the app.

## Run the dashboard
1. Install Python 3.10+ (recommended) and packages from `requirements.txt`.
2. Run `streamlit run app.py` from this folder.
3. If available, upload a CSV with columns `store`, `item`, `on_hand_units`, `on_order_units`, `backorders_units`; use `inventory_position_template.csv` as the template and fill the blank columns with actual inventory data.

## Current state and caveats
Because the historical source includes sales only, the dashboard starts without true live replenishment alerts. Without an inventory upload, it shows proposed stock thresholds and explicitly marks live inventory status as unknown. The future forecast runs from 1 January to 26 March 2018 because the source history ends in 2017; the horizon is a reproducible example, not a current production forecast. Refresh the model with new transactions before operational use.
