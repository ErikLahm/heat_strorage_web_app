import numpy as np
import numpy.typing as npt
import pandas as pd
import plotly.express as px
import streamlit as st


def plotly_raw_data(raw_data: pd.DataFrame):
    num_cols = len(raw_data.columns)
    temperatures = raw_data[
        [header for header in raw_data.columns[: int(num_cols / 2)]]
    ]
    volumes = raw_data[[header for header in raw_data.columns[int(num_cols / 2) :]]]
    fig_temps = px.line(
        temperatures,
        labels=dict(
            index="Zeit in Zeitschritten",
            value="Temperatur",
        ),
    )
    fig_volumes = px.line(
        volumes,
        labels=dict(
            index="Zeit in Zeitschritten",
            value="Volumenströme in m^3/h",
        ),
    )
    return fig_temps, fig_volumes


def plot_sim_results(results: npt.NDArray[np.float64]):
    column_header = [f"Schicht {i}" for i in range(results.shape[0])]
    df = pd.DataFrame(results.T, columns=column_header)
    df.drop(columns=[df.columns[0], df.columns[-1]], inplace=True)
    fig = px.line(df, labels=dict(index="Zeit in Zeitschritten", value="Temperatur"))
    return fig


def plot_power(powers: list[npt.NDArray[np.float64]], name: list[str]):
    power_df = pd.DataFrame(np.concatenate(powers, axis=1), columns=name)
    fig = px.line(
        power_df,
        labels=dict(index="Zeit in Zeitschritten", value="Thermische Leistung in kW"),
    )
    return fig


def plot_heatmap(base_solution: npt.NDArray[np.float64]):
    base_solution = base_solution[1:-1, :]
    base_solution = np.flipud(base_solution)
    base_solution_3d = base_solution.reshape(
        (base_solution.shape[0], 1, base_solution.shape[1])
    )
    fig = px.imshow(
        img=base_solution_3d,
        zmin=np.min(base_solution),
        zmax=np.max(base_solution),
        color_continuous_scale="RdBu_r",
        origin="lower",
        animation_frame=2,
        aspect="auto",
    )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 10
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 5
    fig.update_layout(
        title_text="Wärmespeicher Animation",
        xaxis=dict(visible=False, showticklabels=False),
    )
    return fig
