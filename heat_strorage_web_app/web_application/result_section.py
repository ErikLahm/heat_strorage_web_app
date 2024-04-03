import numpy as np
import numpy.typing as npt
import streamlit as st

from web_application.backend_connection import (
    get_analysis_results,
    get_source_sink_power_consumption,
)
from web_application.param_enums import Params
from web_application.st_plot import (
    plot_comparison,
    plot_sim_results,
)


def display_result_section(
    base_result: npt.NDArray[np.float64],
    heater_result: npt.NDArray[np.float64],
    heater_power: npt.NDArray[np.float64],
    cooler_power: npt.NDArray[np.float64],
):
    st.subheader("Simulationsergebnisse")
    display_temp_results(base_result=base_result, heater_result=heater_result)
    total_energy, cooler_energy, source_energy, sink_energy = get_analysis_results(
        base_result=base_result, heater_power=heater_power, cooler_power=cooler_power
    )
    source_power, sink_power = get_source_sink_power_consumption(
        simulation_result=heater_result
    )
    display_comparison(
        heater_power=heater_power,
        cooler_power=cooler_power,
        source_power=source_power,
        sink_power=sink_power,
    )
    display_analysis_section(
        total_energy=total_energy,
        cooler_energy=cooler_energy,
        source_energy=source_energy,
        sink_energy=sink_energy,
        num_sim_days=st.session_state[Params.DAYS.value],
    )


def display_comparison(
    heater_power: npt.NDArray[np.float64],
    cooler_power: npt.NDArray[np.float64],
    source_power: list[npt.NDArray[np.float64]],
    sink_power: list[npt.NDArray[np.float64]],
):
    labels = [f"Quellenleistung {i}" for i, _ in enumerate(source_power)]
    labels.extend([f"Senkenleistung {i}" for i, _ in enumerate(sink_power)])
    source_power.extend(sink_power)
    comp_fig = plot_comparison(
        source_power, labels, heater_power=heater_power, cooler_power=cooler_power
    )
    st.plotly_chart(comp_fig)  # type:ignore


def display_analysis_section(
    total_energy: float,
    cooler_energy: float,
    source_energy: npt.NDArray[np.float64],
    sink_energy: npt.NDArray[np.float64],
    num_sim_days: int,
) -> None:
    total_source_energy = source_energy.sum()  # type: ignore
    total_sink_energy = sink_energy.sum()  # type: ignore
    ana_col1, ana_col2, ana_col3, ana_col4, ana_col5 = st.columns(5)
    with ana_col1:
        st.metric("Energieverbrauch Quellen  \nin kWh", "%.2f" % total_source_energy)  # type: ignore
        st.metric("Jahreshochrechnung  \nEnergieverbrauch Quellen  \nin MWh", "%.2f" % (float(total_source_energy) * 365 / num_sim_days / 1000))  # type: ignore
    with ana_col2:
        st.metric("Energieverbrauch Senken  \nin kWh", "%.2f" % total_sink_energy)  # type: ignore
        st.metric("Jahreshochrechnung  \nEnergieverbrauch Senken  \nin MWh", "%.2f" % (float(total_sink_energy) * 365 / num_sim_days / 1000))  # type: ignore
    with ana_col3:
        st.metric("Differenz  \nin kWh", "%.2f" % abs(total_sink_energy - total_source_energy))  # type: ignore
        st.metric("Jahreshochrechnung  \nDifferenz  \nin MWh", "%.2f" % (float(abs(total_sink_energy - total_source_energy) * 365 / num_sim_days / 1000)))  # type: ignore
    with ana_col4:
        st.metric("Energieverbrauch Spitzen-  \nlastheizung in kWh", "%.2f" % total_energy)  # type: ignore
        st.metric("Jahreshochrechnung  \nEnergieverbrauch Spitzen-  \nin MWh", "%.2f" % (float(total_energy) * 365 / num_sim_days / 1000))  # type: ignore
    with ana_col5:
        st.metric("Energieverbrauch Notkühler  \nin kWh", "%.2f" % cooler_energy)  # type: ignore
        st.metric("Jahreshochrechnung  \nEnergieverbrauch Notkühler  \nin MWh", "%.2f" % (float(cooler_energy) * 365 / num_sim_days / 1000))  # type: ignore


def display_temp_results(
    base_result: npt.NDArray[np.float64], heater_result: npt.NDArray[np.float64]
):
    tab_normal_sim, tab_heater_sim = st.tabs(
        ["Simulation ohne Spitzenlastheizung", "Simulation mit Spitzenlastheizung"]
    )
    with tab_normal_sim:
        result_fig = plot_sim_results(base_result)
        st.plotly_chart(result_fig, use_container_width=True)  # type: ignore
    with tab_heater_sim:
        heater_result_fig = plot_sim_results(heater_result)
        st.plotly_chart(heater_result_fig, use_container_width=True)  # type: ignore
