"""
Minimal Streamlit App for Testing
"""
import streamlit as st

st.title("Simple Test App")
st.write("If you can see this, Streamlit is working correctly!")

st.write("Testing package imports:")

try:
    import ta
    st.success("✅ ta package is installed")
except ImportError:
    st.error("❌ ta package is NOT installed")

try:
    import flask
    st.success("✅ flask package is installed")
except ImportError:
    st.error("❌ flask package is NOT installed")

try:
    import pandas as pd
    st.success("✅ pandas package is installed")
except ImportError:
    st.error("❌ pandas package is NOT installed")

try:
    import numpy as np
    st.success("✅ numpy package is installed")
except ImportError:
    st.error("❌ numpy package is NOT installed")

st.write("Testing complete!") 