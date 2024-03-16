from typing import Tuple

import numpy as np
import numpy.typing as npt
from pde_calculations.flow import Flow
from pde_calculations.sim_enums import SimType
from pde_calculations.simulations import calc_mix_power, power_to_energy

from heat_strorage_web_app.pde_calculations.medium import Medium


def get_energy_consumption_data(
    power_cons: npt.NDArray[np.float64], delta_t: float
) -> Tuple[npt.NDArray[np.float64], float]:
    """
    Converts power of each timestep to consumed energy per timestep.

    Parameters
    ----------
    power_cons: npt.NDArray[np.float64]
        Array of shape (number_of_timesteps, 1) with used power of each timestep
    delta_t: float
        length of each timestep in seconds

    Returns
    -------
    Tuple[npt.NDArray[np.float64], float]
        array: containing the cumulated energy for each timestep
        float: total energy summed
    """

    energy_cons_cum = np.apply_along_axis(
        lambda power: power_to_energy(power, delta_t), 0, power_cons  # type: ignore
    )
    total_energy = np.sum(energy_cons_cum)  # type: ignore
    energy_cons_cum = np.cumsum(energy_cons_cum)
    return energy_cons_cum, total_energy


def get_in_out_energy_cons(
    flows: list[Flow], vessel_state: npt.NDArray[np.float64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Calculates the energy consumption of all input flows for the source and sink side.
    """

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
    """
    Calculates the energy consumed on either the source or sink side to achieve the temperature
    difference between the output (calculated) and input (given) of the vessel.

    The calculation is based on the mixed temperature formula, where the mass flow is given and
    the temperature difference is given by the difference of input (given) and output (calculated)
    temperatures.
    NOTE: For the source side we expect the input temperature to be higher than the calulated
    output temperature (sink side -> vice versa). If this condition is ever violated we simply
    set the consumed energy for that interval to 0.

    Parameters
    ----------
    flow: Flow
        Flow with the given input temperature and the mass flow.
    output_temp: npt.NDArray[np.float64]
        Temperature of the calcualted output flow.

    Returns
    -------
    npt.NDArray[np.float64]
        Array of the shape (number_of_sim_steps, 1) which gives the consumed energy for every
        timestep corresponding to the given flow.
    """

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
        lambda power: power_to_energy(power=power, delta_t=300), 0, flow_power  # type: ignore
    )
    return flow_energy


def get_outer_power_cons(
    flows: list[Flow], medium: Medium, simulation_result: npt.NDArray[np.float64]
) -> Tuple[list[npt.NDArray[np.float64]], list[npt.NDArray[np.float64]]]:
    source_power: list[npt.NDArray[np.float64]] = []
    sink_power: list[npt.NDArray[np.float64]] = []
    for flow in flows:
        if flow.input_type == SimType.SOURCE:
            source_power.append(
                get_source_power(
                    high_temp=flow.flow_temp,
                    low_temp=simulation_result[-2, :],
                    mass_flow=flow.mass_flow_kg_s,
                    c_p=medium.c_p,
                ).reshape((len(flow.flow_temp), 1))
            )
        else:
            sink_power.append(
                get_source_power(
                    high_temp=simulation_result[1, :],
                    low_temp=flow.flow_temp,
                    mass_flow=flow.mass_flow_kg_s,
                    c_p=medium.c_p,
                ).reshape((len(flow.flow_temp), 1))
            )
    return source_power, sink_power


def get_source_power(
    high_temp: npt.NDArray[np.float64],
    low_temp: npt.NDArray[np.float64],
    mass_flow: npt.NDArray[np.float64],
    c_p: float,
) -> npt.NDArray[np.float64]:
    return np.array(
        [
            calc_mix_power(
                mass_flow=inp[0], high_temp=inp[1], low_temp=inp[2], c_p_fluid=c_p
            )
            for inp in list(zip(mass_flow, high_temp, low_temp))
        ]
    )
