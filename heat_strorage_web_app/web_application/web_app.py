import copy
import os
import sys
from typing import Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

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
    calc_mix_power,
    heater_simulation,
    power_to_energy,
)
from pde_calculations.vessel import Vessel
from st_data_loader import df_to_np_temp_mass_array
from st_plot import plot_sim_results, plotly_raw_data
from streamlit.elements.number_input import Number
from streamlit.runtime.uploaded_file_manager import UploadedFile

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


def raw_to_df(raw_data: UploadedFile) -> pd.DataFrame:
    df = pd.read_excel(raw_data, skiprows=1, header=None)
    header = [f"Temperatur {i}" for i in range(int(len(df.columns) / 2))]
    header.extend([f"Volumenstrom {i}" for i in range(int(len(df.columns) / 2))])
    rename_dict = {
        list(df.columns)[i]: new_header for (i, new_header) in enumerate(header)
    }
    df.rename(columns=rename_dict, inplace=True)
    return df


def display_vessel_widgets() -> Vessel:
    height = st.sidebar.number_input("Höhe in $m$", 0.0, 40.0, 8.0, 1.0)
    radius = st.sidebar.number_input("Radius in $m$", 0.0, 10.0, 2.0, 0.5)
    segmentation = st.sidebar.number_input("Segmentierung", 2, 20, 7, 1)
    initial_state = st.sidebar.selectbox(
        "Anfangszustand", [value.value for value in InitialStateType]
    )
    initial_high_temp = st.sidebar.number_input(
        "initiale Höchsttemperatur in $\degree C$", 0.0, 100.0, 70.0, 1.0
    )
    initial_low_temp = st.sidebar.number_input(
        "initiale Niedertemperatur in $\degree C$", 0.0, 100.0, 20.0, 1.0
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
        "Umgebungstemperatur $T_{\\text{ext}}$ in $\degree C$", value=20.0
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
    st.session_state.edited_source[header] = original_df[header].apply(
        lambda x: x * st.session_state.source_factor
    )


def manipulate_sink(header: str, original_df: pd.DataFrame) -> None:
    st.session_state.edited_sink[header] = original_df[header].apply(
        lambda x: x * st.session_state.sink_factor
    )


def display_raw_data(source_df: pd.DataFrame, sink_df: pd.DataFrame) -> None:
    source_column, sink_column = st.columns(2, gap="medium")
    if not source_df.empty:
        with source_column:
            st.write("**Quellen**")
            with st.expander("Datenmanipulation"):
                source_col3, source_col4 = st.columns([0.6, 0.4])
                st.write(st.session_state.edited_source)
                with source_col3:
                    header_to_edit = st.selectbox(
                        "Datensatz wählen",
                        [str(header) for header in source_df.columns],
                        key="source_select",
                    )
                with source_col4:
                    current_source_factor = (
                        st.session_state.edited_source[header_to_edit][0]
                        / source_df[header_to_edit][0]
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
            tab1_source, tab2_source = st.tabs(["Temperaturen", "Volumenströme"])
            source_temp_fig, source_vol_fig = plotly_raw_data(
                st.session_state.edited_source
            )
            with tab1_source:
                st.plotly_chart(source_temp_fig, use_container_width=True)
            with tab2_source:
                st.plotly_chart(source_vol_fig, use_container_width=True)
    if not sink_df.empty:
        with sink_column:
            st.write("**Senken**")
            with st.expander("Datenmanipulation"):
                sink_col3, sink_col4 = st.columns([0.6, 0.4])
                st.write(st.session_state.edited_sink)
                with sink_col3:
                    header_to_edit_sink = st.selectbox(
                        "Datensatz wählen",
                        [str(header) for header in sink_df.columns],
                        key="sink_select",
                    )
                with sink_col4:
                    current_sink_factor = (
                        st.session_state.edited_sink[header_to_edit_sink][0]
                        / sink_df[header_to_edit_sink][0]
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
            tab1_sink, tab2_sink = st.tabs(["Temperaturen", "Volumenströme"])
            sink_temp_fig, sink_vol_fig = plotly_raw_data(st.session_state.edited_sink)
            with tab1_sink:
                st.plotly_chart(sink_temp_fig, use_container_width=True)
            with tab2_sink:
                st.plotly_chart(sink_vol_fig, use_container_width=True)


def get_energy_consumption_data(power_cons: npt.NDArray[np.float64], delta_t: float):
    energy_cons_cum = np.apply_along_axis(
        lambda power: power_to_energy(power, delta_t), 0, power_cons
    )
    total_energy = np.sum(energy_cons_cum)
    energy_cons_cum = np.cumsum(energy_cons_cum)
    return energy_cons_cum, total_energy


def get_in_out_energy_cons(
    flows: list[Flow], vessel_state: npt.NDArray[np.float64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    source_energy = np.zeros(flows[0].flow_temp.shape)
    sink_energy = np.zeros(source_energy.shape)
    for flow in flows:
        if flow.input_type == SimType.SOURCE:
            source_energy += calc_flow_energy(
                flow=flow, output_temp=vessel_state[-2, 1:]
            )
        else:
            sink_energy += calc_flow_energy(flow=flow, output_temp=vessel_state[1, 1:])
    return source_energy, sink_energy


def calc_flow_energy(
    flow: Flow, output_temp: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    flow_power = np.zeros(output_temp.shape)
    if flow.input_type == SimType.SOURCE:
        for timestep, temp in enumerate(output_temp):
            flow_power[timestep] = calc_mix_power(
                mass_flow=flow.mass_flow_kg_s[timestep],
                c_p_fluid=flow.medium.c_p,
                high_temp=flow.flow_temp[timestep],
                low_temp=temp,
            )
    else:
        for timestep, temp in enumerate(output_temp):
            flow_power[timestep] = calc_mix_power(
                mass_flow=flow.mass_flow_kg_s[timestep],
                c_p_fluid=flow.medium.c_p,
                high_temp=temp,
                low_temp=flow.flow_temp[timestep],
            )
    flow_energy = np.apply_along_axis(
        lambda power: power_to_energy(power=power, delta_t=300), 0, flow_power
    )
    return flow_energy


def main():
    st.set_page_config(
        page_title="Wärmespeicher Simulation",
        layout="wide",
        page_icon=":chart_with_downwards_trend:",
    )
    st.title(HEADER)
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
        st.header("Heizfreie Simulation")
        result_fig = plot_sim_results(base_result)
        st.plotly_chart(result_fig, use_container_width=True)
        st.header("Simulation mit Heizung")
        _, total_energy = get_energy_consumption_data(
            heater_pow, delta_t=int(time_delta)
        )
        st.metric("Energieverbrauch Spitzenlastheizung in kWh", "%.2f" % total_energy)
        source_energy, sink_energy = get_in_out_energy_cons(
            flows=flows, vessel_state=base_result
        )
        st.metric("Energieverbrauch Quellen in kWh", "%.2f" % source_energy.sum())
        st.metric("Energieverbrauch Senken in kWh", "%.2f" % sink_energy.sum())
        heater_result_fig = plot_sim_results(heater_result)
        st.plotly_chart(heater_result_fig, use_container_width=True)


if __name__ == "__main__":
    main()
