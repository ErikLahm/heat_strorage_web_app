import copy
import re

import numpy as np
import numpy.typing as npt
import pandas as pd
import streamlit as st
from pde_calculations.environment import Environment
from pde_calculations.flow import Flow
from pde_calculations.heat_pde import HeatTransferEquation
from pde_calculations.medium import Medium
from pde_calculations.sim_enums import InitialStateType, SimType
from pde_calculations.simulations import (
    base_simulation,
    cooler_simulation,
    heater_simulation,
)
from pde_calculations.vessel import Vessel
from streamlit.elements.number_input import Number
from streamlit.runtime.uploaded_file_manager import UploadedFile
from web_application.analysis_calcs import (
    get_energy_consumption_data,
    get_in_out_energy_cons,
    raw_to_df,
)
from web_application.st_data_loader import df_to_np_temp_mass_array
from web_application.st_plot import plot_sim_results, plotly_raw_data

HEADER = "Wärmespeicher Simulation"

Heater = tuple[float, float, float, float]


def get_raw_data() -> tuple[UploadedFile | None, UploadedFile | None]:
    source_data_raw = st.sidebar.file_uploader(
        "Quellen laden",
        type=["xlsx"],
        help="Datensatz wählen",
    )
    sink_data_raw = st.sidebar.file_uploader(
        "Senken laden",
        type=["xlsx"],
        help="Senken laden",
    )
    if not (source_data_raw or sink_data_raw):
        st.error("Bitte mindestens einen Datensatz hochladen.")
    return source_data_raw, sink_data_raw


def display_vessel_widgets() -> Vessel:
    height = st.sidebar.number_input("Höhe in $m$", 0.0, 40.0, 8.0, 1.0)
    radius = st.sidebar.number_input("Radius in $m$", 0.0, 10.0, 2.0, 0.5)
    segmentation = st.sidebar.number_input("Segmentierung", 2, 20, 7, 1)
    initial_state = st.sidebar.selectbox(
        "Anfangszustand", [value.value for value in InitialStateType]
    )
    initial_high_temp = st.sidebar.number_input(
        "initiale Höchsttemperatur in $\degree C$", 0.0, 100.0, 70.0, 1.0  # type: ignore
    )
    initial_low_temp = st.sidebar.number_input(
        "initiale Niedertemperatur in $\degree C$", 0.0, 100.0, 20.0, 1.0  # type: ignore
    )
    vessel = Vessel(
        height=height,
        radius=radius,
        segmentation=int(segmentation),
        initial_state=InitialStateType(initial_state),
        min_value=initial_low_temp,
        max_value=initial_high_temp,
    )
    return vessel


def display_medium_widgets() -> Medium:
    st.sidebar.header("Medium")
    density = st.sidebar.number_input(
        "Dichte $\\varrho$ in $\\frac{kg}{m^3}$",
        min_value=0.0,
        value=1000.0,
    )
    c_p = st.sidebar.number_input(
        "Spezifische Wärmekapazität $c_p$ in $\\frac{J}{kg K}$",
        min_value=0.0,
        value=4184.0,
    )
    diffusivity = st.sidebar.number_input(
        "Fluid Diffusivity $\\alpha$ in $\\frac{m^2}{s}(10^{-7})$",
        min_value=0.0,
        value=1.43,
    )
    medium = Medium(density=density, alpha=diffusivity * 10 ** (-7), c_p=c_p)
    return medium


def display_environment() -> Environment:
    st.sidebar.header("Umgebungsvariablen")
    env_temp = st.sidebar.number_input(
        "Umgebungstemperatur $T_{\\text{ext}}$ in $\degree C$", value=20.0  # type: ignore
    )
    env = Environment(env_temp=env_temp)
    return env


def display_heater() -> Heater:
    st.sidebar.header("Heizung")
    layer_section = st.sidebar.number_input(
        "kritische Kesselschicht",
        min_value=0.1,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Schichtdicke des Kessels, anhand derer die Referenztemperatur gemessen wird.",
    )
    critical_temp = st.sidebar.number_input(
        "kritische Temperatur",
        min_value=0.0,
        max_value=99.0,
        value=60.0,
        step=0.5,
        help="Ab welcher Temperatur soll die Heizung anspringen.",
    )
    turn_off_temp = st.sidebar.number_input(
        "Zieltemperatur",
        min_value=0.0,
        max_value=100.0,
        value=80.0,
        step=0.5,
        help="Ab welcher Temperatur schaltet die Heizung ab.",
    )
    heating_temp = st.sidebar.number_input(
        "Heiztemperatur",
        min_value=0.0,
        max_value=100.0,
        value=85.0,
        step=0.5,
        help="Auf welche Temperatur werden die Ströme aufgeheizt.",
    )
    return layer_section, critical_temp, turn_off_temp, heating_temp


def display_cooler_settings() -> Number:
    st.sidebar.header("Notkühler")
    desired_temp = st.sidebar.number_input(
        "Zieltemperatur",
        min_value=1.0,
        value=30.0,
        step=1.0,
        help="Auf welche Temperatur soll der Zulauf zu den Erzeugern abgekühlt werden.",
    )
    return desired_temp


def get_flows(medium: Medium) -> list[Flow]:
    flows: list[Flow] = []
    if "edited_source" in st.session_state:
        source_temps, source_masses = df_to_np_temp_mass_array(
            st.session_state.edited_source
        )
        flows.extend(
            [
                Flow(
                    flow_temp=source_temps[i],
                    volume_flow=source_masses[i],
                    input_type=SimType.SOURCE,
                    medium=medium,
                )
                for i, _ in enumerate(source_temps)
            ]
        )
    if "edited_sink" in st.session_state:
        sink_temps, sink_masses = df_to_np_temp_mass_array(st.session_state.edited_sink)
        flows.extend(
            [
                Flow(
                    flow_temp=sink_temps[i],
                    volume_flow=sink_masses[i],
                    input_type=SimType.SINK,
                    medium=medium,
                )
                for i, _ in enumerate(sink_temps)
            ]
        )
    return flows


def get_dfs(
    source: UploadedFile | None, sink: UploadedFile | None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if source:
        source_df = raw_to_df(source)
        source_df_edit = source_df.copy()
        if "edited_source" not in st.session_state:
            st.session_state.edited_source = source_df_edit
    else:
        source_df = pd.DataFrame([])
        if "edited_source" in st.session_state:
            del st.session_state.edited_source
    if sink:
        sink_df = raw_to_df(sink)
        sink_df_edit = sink_df.copy()
        if "edited_sink" not in st.session_state:
            st.session_state.edited_sink = sink_df_edit
    else:
        sink_df = pd.DataFrame([])
        if "edited_sink" in st.session_state:
            del st.session_state.edited_sink
    return source_df, sink_df


def manipulate_source(header: str, original_df: pd.DataFrame) -> None:
    st.session_state.edited_source[header] = original_df[header].apply(  # type: ignore
        lambda x: x * st.session_state.source_factor
    )
    if re.search("Temperatur", st.session_state.source_select):
        st.session_state.edited_source[header][
            st.session_state.edited_source[header] > st.session_state.max_temp_source
        ] = st.session_state.max_temp_source
    else:
        st.session_state.edited_source[header][
            st.session_state.edited_source[header] > st.session_state.max_vol_source
        ] = st.session_state.max_vol_source


def manipulate_sink(header: str, original_df: pd.DataFrame) -> None:
    st.session_state.edited_sink[header] = original_df[header].apply(  # type: ignore
        lambda x: x * st.session_state.sink_factor
    )
    if re.search("Temperatur", st.session_state.sink_select):
        st.session_state.edited_sink[header][
            st.session_state.edited_sink[header] > st.session_state.max_temp_sink
        ] = st.session_state.max_temp_sink
    else:
        st.session_state.edited_source[header][
            st.session_state.edited_source[header] > st.session_state.max_vol_sink
        ] = st.session_state.max_vol_sink


def display_raw_data(source_df: pd.DataFrame, sink_df: pd.DataFrame) -> None:
    source_column, sink_column = st.columns(2, gap="medium")
    if not source_df.empty:
        with source_column:
            st.write("**Quellen**")  # type: ignore
            with st.expander("Datenmanipulation"):
                source_col3, source_col4 = st.columns([0.6, 0.4])
                st.write(st.session_state.edited_source)  # type: ignore
                with source_col3:
                    header_to_edit = st.selectbox(
                        "Datensatz wählen",
                        [str(header) for header in source_df.columns],  # type: ignore
                        key="source_select",
                    )
                with source_col4:
                    current_source_factor = (
                        st.session_state.edited_source[header_to_edit].min()
                        / source_df[header_to_edit].min()
                    )
                    st.number_input(
                        "Faktor",
                        0.1,
                        10.0,
                        current_source_factor,
                        0.25,
                        key="source_factor",
                        on_change=lambda: manipulate_source(
                            str(header_to_edit),
                            source_df,
                        ),
                    )
                    if re.search("Temperatur", st.session_state.source_select):
                        st.number_input(
                            "Maximale Temperatur",
                            1,
                            99,
                            85,
                            5,
                            key="max_temp_source",
                            on_change=lambda: manipulate_source(
                                str(header_to_edit),
                                source_df,
                            ),
                        )
                    else:
                        st.number_input(
                            "Maximaler Volumenstrom",
                            1,
                            99,
                            50,
                            5,
                            key="max_vol_source",
                            on_change=lambda: manipulate_source(
                                str(header_to_edit),
                                source_df,
                            ),
                        )
            tab1_source, tab2_source = st.tabs(["Temperaturen", "Volumenströme"])
            source_temp_fig, source_vol_fig = plotly_raw_data(
                st.session_state.edited_source
            )
            with tab1_source:
                st.plotly_chart(source_temp_fig, use_container_width=True)  # type: ignore
            with tab2_source:
                st.plotly_chart(source_vol_fig, use_container_width=True)  # type: ignore
    if not sink_df.empty:
        with sink_column:
            st.write("**Senken**")  # type: ignore
            with st.expander("Datenmanipulation"):
                sink_col3, sink_col4 = st.columns([0.6, 0.4])
                st.write(st.session_state.edited_sink)  # type: ignore
                with sink_col3:
                    header_to_edit_sink = st.selectbox(
                        "Datensatz wählen",
                        [str(header) for header in sink_df.columns],
                        key="sink_select",
                    )
                with sink_col4:
                    current_sink_factor = (
                        st.session_state.edited_sink[header_to_edit_sink].min()
                        / sink_df[header_to_edit_sink].min()
                    )
                    st.number_input(
                        "Faktor",
                        0.1,
                        10.0,
                        current_sink_factor,
                        0.25,
                        key="sink_factor",
                        on_change=lambda: manipulate_sink(
                            str(header_to_edit_sink),
                            sink_df,
                        ),
                    )
                    if re.search("Temperatur", st.session_state.sink_select):
                        st.number_input(
                            "Maximale Temperatur",
                            1,
                            99,
                            50,
                            5,
                            key="max_temp_sink",
                            on_change=lambda: manipulate_sink(
                                str(header_to_edit_sink),
                                sink_df,
                            ),
                        )
                    else:
                        st.number_input(
                            "Maximaler Volumenstrom",
                            1,
                            99,
                            50,
                            5,
                            key="max_vol_sink",
                            on_change=lambda: manipulate_sink(
                                str(header_to_edit_sink),
                                sink_df,
                            ),
                        )
            tab1_sink, tab2_sink = st.tabs(["Temperaturen", "Volumenströme"])
            sink_temp_fig, sink_vol_fig = plotly_raw_data(st.session_state.edited_sink)
            with tab1_sink:
                st.plotly_chart(sink_temp_fig, use_container_width=True)  # type: ignore
            with tab2_sink:
                st.plotly_chart(sink_vol_fig, use_container_width=True)  # type: ignore


def display_analysis_section(
    heater_pow: npt.NDArray[np.float64],
    cooler_power: npt.NDArray[np.float64],
    time_delta: int,
    flows: list[Flow],
    base_result: npt.NDArray[np.float64],
    num_sim_days: int,
) -> None:
    _, total_energy = get_energy_consumption_data(heater_pow, delta_t=int(time_delta))
    _, cooler_energy_total = get_energy_consumption_data(
        cooler_power, delta_t=int(time_delta)
    )
    source_energy, sink_energy = get_in_out_energy_cons(
        flows=flows, vessel_state=base_result
    )
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
        st.metric("Energieverbrauch Notkühler  \nin kWh", "%.2f" % cooler_energy_total)  # type: ignore
        st.metric("Jahreshochrechnung  \nEnergieverbrauch Notkühler  \nin MWh", "%.2f" % (float(cooler_energy_total) * 365 / num_sim_days / 1000))  # type: ignore


def main():
    st.set_page_config(
        page_title="Wärmespeicher Simulation",
        layout="wide",
        page_icon=":chart_with_downwards_trend:",
    )
    st.title(HEADER)
    st.sidebar.image("heat_strorage_web_app/resources/emv_logo.png")
    st.sidebar.header("Datensatz Import")
    st.subheader("Rohdaten")
    source, sink = get_raw_data()
    time_delta = st.sidebar.number_input(
        "Zeitdifferenz zw. Messwerten [s]",
        min_value=1,
        value=300,
        step=60,
        help="Was ist die Zeitdifferenz zwischen je zwei Messwerten im Datensatz.",
    )
    num_sim_days = st.sidebar.number_input(
        "Anzahl der Messtage", min_value=1, value=7, step=1
    )
    st.sidebar.divider()
    st.sidebar.header("Behältermaße")
    vessel = display_vessel_widgets()
    medium = display_medium_widgets()
    env = display_environment()
    layer_sec, crit_temp, turn_off, heating_temp = display_heater()
    desired_cooling_temp = display_cooler_settings()
    source_df, sink_df = get_dfs(source, sink)
    display_raw_data(source_df=source_df, sink_df=sink_df)
    st.divider()
    st.subheader("Simulationsergebnisse")
    flows = get_flows(medium=medium)
    pde = HeatTransferEquation(fluid=medium, vessel=vessel, env=env)
    if flows:
        base_result = base_simulation(hte=pde, flows=flows, delta_t=int(time_delta))
        heater_flows = [copy.deepcopy(flow) for flow in flows]
        heater_result, heater_pow = heater_simulation(
            hte=pde,
            flows=heater_flows,
            delta_t=int(time_delta),
            vessel_section=layer_sec,
            critical_temp=crit_temp,
            turn_off_temp=turn_off,
            heating_temp=heating_temp,
        )
        cooler_power = cooler_simulation(
            layer=heater_result[-2, 1:],
            desired_temp=desired_cooling_temp,
            flows=flows,
            c_p_fluid=medium.c_p,
        )
        st.header("Heizfreie Simulation")
        result_fig = plot_sim_results(base_result)
        st.plotly_chart(result_fig, use_container_width=True)  # type: ignore
        st.header("Simulation mit Heizung")
        heater_result_fig = plot_sim_results(heater_result)
        st.plotly_chart(heater_result_fig, use_container_width=True)  # type: ignore
        display_analysis_section(
            heater_pow=heater_pow,
            cooler_power=cooler_power,
            time_delta=int(time_delta),
            flows=flows,
            base_result=base_result,
            num_sim_days=int(num_sim_days),
        )


if __name__ == "__main__":
    main()
