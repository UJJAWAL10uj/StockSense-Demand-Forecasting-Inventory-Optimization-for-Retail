# Dashboard compatibility update

This package replaces deprecated Streamlit `use_container_width=True` arguments with `width="stretch"` in chart and dataframe rendering calls. It also raises the minimum Streamlit version to 1.50, where the `width` option is supported by the calls used here.

The update preserves the dashboard logic and makes the displayed charts/tables stretch to their available container width. The terminal message recommending `streamlit skills` is optional guidance for developers and is not required to run this dashboard.

Run from this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
