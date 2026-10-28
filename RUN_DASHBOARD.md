# Run the StockSense Dashboard

1. Open this folder in a terminal.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Launch: `streamlit run app.py`.
4. Select store/item and change the assumed lead time, review period and service level in the sidebar.
5. For live replenishment status, upload a CSV with `store`, `item`, `on_hand_units`; optional columns are `on_order_units` and `backorders_units`. `inventory_position_template.csv` is a blank 500-row template to fill with actual stock data.

Without inventory data, the application intentionally shows planning thresholds and marks replenishment status as unknown; it does not claim actual stockouts.
