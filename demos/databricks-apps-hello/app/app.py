import os

import streamlit as st

st.set_page_config(page_title="demo-app", page_icon=":wave:")
st.title("Hello from a Databricks App")
st.write("A minimal Streamlit app deployed with `databricks apps deploy`.")
st.caption(f"App name: {os.getenv('DATABRICKS_APP_NAME', 'local')}")
