import numpy as np
import numpy.typing as npt
import pandas as pd


def df_to_np_temp_mass_array(
    df: pd.DataFrame,
) -> tuple[list[npt.NDArray[np.float64]], list[npt.NDArray[np.float64]]]:
    col_number = len(list(df.columns))
    temperatures = [
        df[f"Temperatur {i}"].to_numpy() for i in range(int(col_number / 2))
    ]
    masses = [df[f"Volumenstrom {i}"].to_numpy() for i in range(int(col_number / 2))]
    return temperatures, masses
