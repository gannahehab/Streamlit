import streamlit as st
import pandas as pd
import numpy as np
import time

st.title("📈 Live Updating Data Chart")

chart = st.line_chart([])

for i in range(100):
    new_data = pd.DataFrame(np.random.randn(1, 3), columns=['A', 'B', 'C'])
    chart.add_rows(new_data)
    time.sleep(0.2)
