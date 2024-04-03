import streamlit as st
from web_application.raw_data_section import display_raw_data_section
from web_application.sidebar_builder import build_sidebar

from heat_strorage_web_app.web_application.backend_connection import (
    get_base_simulation_results,
    get_cooler_simulation_results,
    get_heater_simulation_results,
)
from heat_strorage_web_app.web_application.result_section import display_result_section
from pathlib import Path

path = Path(
    __file__
).parent.resolve()  # get the path to the folder that the current file is in


def main():
    st.set_page_config(
        page_title="Wärmespeicher Simulation",
        layout="wide",
        page_icon=":chart_with_downwards_trend:",
    )
    st.title("Wärmespeicher Simulation")
    build_sidebar()
    display_raw_data_section()
    if st.session_state.sim_button:
        base_result = get_base_simulation_results()
        heater_result, heater_power = get_heater_simulation_results()
        cooler_power = get_cooler_simulation_results(sim_result=heater_result)
        display_result_section(
            base_result=base_result,
            heater_result=heater_result,
            heater_power=heater_power,
            cooler_power=cooler_power,
        )


if __name__ == "__main__":
    main()
