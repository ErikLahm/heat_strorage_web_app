import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from heat_strorage_web_app.web_application.param_enums import Params


DTYPEMAP = {
    Params.DELTA_T.value: "int",
    Params.DAYS.value: "int",
    Params.HEIGHT.value: "float",
    Params.RADIUS.value: "float",
    Params.NUM_SEGS.value: "int",
    Params.INIT_STATE.value: "str",
    Params.INIT_MAX_T.value: "float",
    Params.INIT_MIN_T.value: "float",
    Params.DENSITY.value: "float",
    Params.C_P.value: "float",
    Params.DIFFUSIVITY.value: "float",
    Params.T_ENV.value: "float",
    Params.HEAT_PERC.value: "float",
    Params.HEAT_CRIT_T.value: "float",
    Params.HEAT_GOAL_T.value: "float",
    Params.HEAT_T.value: "float",
    Params.COOLER_GOAL_T.value: "float",
}


class ParamDataBase:
    def __init__(self) -> None:
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        self.database_df = self.read_database()

    def df(self) -> pd.DataFrame:
        return self.database_df

    def read_database(self) -> pd.DataFrame:
        df = self.conn.read(
            usecols=list(range(len(Params) + 1)),
            ttl=0,
        ).dropna(how="all")
        df = df.astype(DTYPEMAP)
        return df

    def update_database(self) -> None:
        self.conn.update(worksheet="simulation_parameter", data=self.database_df)

    def set_name_exists(self, set_name: str) -> bool:
        set_list = self.get_set_names()
        if set_name in set_list:
            return True
        return False

    def append_set(
        self, set_name: str, param_set: dict[str, list[str | float | int]]
    ) -> None:
        """
        Method to append another dataset of parameters. It is only appended if
        the given name is unique or in other words if there is no other dataset
        yet in the database with the same name.

        """
        if not self.set_name_exists(set_name=set_name):
            param_set["name"] = [set_name]
            self.database_df = pd.concat(
                [self.database_df, pd.DataFrame(param_set)], axis=0
            )
            self.update_database()

    def remove_set(self, set_name: str) -> None:
        if self.set_name_exists(set_name=set_name):
            self.database_df = self.database_df[self.database_df["name"] != set_name]
            self.update_database()

    def get_set_names(self) -> list[str]:
        names: list[str] = self.database_df["name"].tolist()
        return names

    def get_param_set(self, set_name: str) -> dict[str, list[str | float | int]]:
        """
        Method returns a dataset based on the given set name.

        The returned data set is given as dictionary of list, where the keys are the
        column names and the lists contain the corresponding values.
        We choose to return list as values to stay consistend with the input needed
        for the pd.concat() function. (see append_set())

        """
        # NOTE: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_dict.html
        param_set = self.database_df.loc[self.database_df["name"] == set_name]
        # return param_set.to_dict()
        return param_set.to_dict("list")
