import numpy as np
import numpy.typing as npt
import pandas as pd
import plotly.express as px


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
            value="Volumenströme",
        ),
    )
    return fig_temps, fig_volumes


def plot_sim_results(results: npt.NDArray[np.float64]):
    column_header = [f"Schicht {i}" for i in range(results.shape[0])]
    df = pd.DataFrame(results.T, columns=column_header)
    df.drop(columns=[df.columns[0], df.columns[-1]], inplace=True)
    fig = px.line(
        df, labels=dict(index="Zeit in Zeitschritten", value="Speicherschichten")
    )
    return fig
