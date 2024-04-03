from typing import Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd
import streamlit as st
from pde_calculations.sim_enums import InitialStateType, SimType
from web_application.param_enums import Params

from pde_calculations.analysis_calcs import (
    get_energy_consumption_data,
    get_in_out_energy_cons,
    get_outer_power_cons,
)
from pde_calculations.environment import Environment
from pde_calculations.flow import Flow
from pde_calculations.heat_pde import HeatTransferEquation
from pde_calculations.medium import Medium
from pde_calculations.simulations import (
    base_simulation,
    cooler_simulation,
    heater_simulation,
)
from pde_calculations.vessel import Vessel


def df_to_np_temp_mass_array(
    df: pd.DataFrame,
) -> tuple[list[npt.NDArray[np.float64]], list[npt.NDArray[np.float64]]]:
    col_number = len(list(df.columns))
    temperatures: list[npt.NDArray[np.float64]] = [
        df[f"Temperatur {i}"].to_numpy() for i in range(int(col_number / 2))  # type: ignore
    ]
    masses: list[npt.NDArray[np.float64]] = [
        df[f"Volumenstrom {i}"].to_numpy() for i in range(int(col_number / 2))  # type: ignore
    ]
    return temperatures, masses


def get_medium() -> Medium:
    return Medium(
        density=st.session_state[Params.DENSITY.value],
        alpha=st.session_state[Params.DIFFUSIVITY.value] * 10 ** (-7),
        c_p=st.session_state[Params.C_P.value],
    )


def get_vessel() -> Vessel:
    return Vessel(
        height=st.session_state[Params.HEIGHT.value],
        radius=st.session_state[Params.RADIUS.value],
        segmentation=st.session_state[Params.NUM_SEGS.value],
        initial_state=st.session_state[Params.INIT_STATE.value],
    )


def get_environment() -> Environment:
    return Environment(env_temp=st.session_state[Params.T_ENV.value])


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


def get_base_simulation_results() -> npt.NDArray[np.float64]:
    medium = get_medium()
    flows = get_flows(medium=medium)
    vessel = get_vessel()
    env = get_environment()
    pde = HeatTransferEquation(fluid=medium, vessel=vessel, env=env)
    return base_simulation(
        hte=pde, flows=flows, delta_t=st.session_state[Params.DELTA_T.value]
    )


def get_heater_simulation_results() -> (
    Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
):
    medium = get_medium()
    flows = get_flows(medium=medium)
    vessel = get_vessel()
    env = get_environment()
    pde = HeatTransferEquation(fluid=medium, vessel=vessel, env=env)
    heater_result, heater_power = heater_simulation(
        hte=pde,
        flows=flows,
        delta_t=st.session_state[Params.DELTA_T.value],
        vessel_section=st.session_state[Params.HEAT_PERC.value],
        critical_temp=st.session_state[Params.HEAT_CRIT_T.value],
        turn_off_temp=st.session_state[Params.HEAT_GOAL_T.value],
        heating_temp=st.session_state[Params.HEAT_T.value],
    )
    return heater_result, heater_power


def get_cooler_simulation_results(
    sim_result: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    medium = get_medium()
    flows = get_flows(medium=medium)
    return cooler_simulation(
        layer=sim_result[-2, 1:],
        desired_temp=st.session_state[Params.COOLER_GOAL_T.value],
        flows=flows,
        c_p_fluid=st.session_state[Params.C_P.value],
    )


def get_analysis_results(
    base_result: npt.NDArray[np.float64],
    heater_power: npt.NDArray[np.float64],
    cooler_power: npt.NDArray[np.float64],
) -> tuple[float, float, npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    medium = get_medium()
    flows = get_flows(medium=medium)
    _, total_energy = get_energy_consumption_data(
        heater_power, delta_t=st.session_state[Params.DELTA_T.value]
    )
    _, cooler_energy_total = get_energy_consumption_data(
        cooler_power, delta_t=st.session_state[Params.DELTA_T.value]
    )
    source_energy, sink_energy = get_in_out_energy_cons(
        flows=flows, vessel_state=base_result
    )
    return (total_energy, cooler_energy_total, source_energy, sink_energy)


def get_source_sink_power_consumption(simulation_result: npt.NDArray[np.float64]):
    medium = get_medium()
    flows = get_flows(medium=medium)
    source_power, sink_power = get_outer_power_cons(
        flows=flows, medium=medium, simulation_result=simulation_result
    )
    return source_power, sink_power


def get_parameter_data() -> dict[str, list[str | int | float]]:
    param_dict: dict[str, list[str | int | float]] = {}
    for param in Params:
        param_dict[param.value] = [st.session_state[param.value]]
    return param_dict


def get_init_state_idx(init_state: str) -> int:
    init_state_list = [state.value for state in InitialStateType]
    return init_state_list.index(init_state)


def set_parameter_data(param_dict: dict[str, list[str | int | float]]) -> None:
    for param in Params:
        if param.value == Params.INIT_STATE.value:
            st.session_state.init_state_idx = get_init_state_idx(
                str(param_dict[param.value][0])
            )
        else:
            st.session_state[param.value] = param_dict[param.value][0]
