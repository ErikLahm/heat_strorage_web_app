import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from heat_strorage_web_app.web_application.param_enums import Params


def display_something():
    for param in Params:
        st.text_area(label=param.value, value=st.session_state.get(param.value, 3))


display_something()
# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(usecols=list(range(len(Params) + 1))).dropna(how="all")
st.write(df)


def update_entry():
    for param in Params:
        st.write(st.session_state[param.value])  # = df[param.value][0]


st.button("update_entry", on_click=update_entry)

test_df = pd.DataFrame({"name": ["test"], "delta_t": [100]})
# df = df.append(test_df)
# st.write(df)
# if st.button("update"):
#     conn.update(worksheet="simulation_parameter", data=df)
