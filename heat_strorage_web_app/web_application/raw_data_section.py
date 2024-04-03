import re

import numpy as np
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from web_application.st_plot import plotly_raw_data


def display_raw_data_section():
    st.subheader("Rohdaten")
    source_df, sink_df = get_dfs(
        st.session_state.source_data_raw, st.session_state.sink_data_raw
    )
    display_raw_data(source_df=source_df, sink_df=sink_df)
    st.divider()


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
                    current_source_factor = (  # type: ignore
                        st.session_state.edited_source[header_to_edit].min()
                        / source_df[header_to_edit].min()  # type: ignore
                    )
                    st.number_input(
                        "Faktor",
                        0.1,
                        10.0,
                        current_source_factor,  # type: ignore
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
                    current_sink_factor = (  # type: ignore
                        st.session_state.edited_sink[header_to_edit_sink].min()
                        / sink_df[header_to_edit_sink].min()  # type: ignore
                    )
                    st.number_input(
                        "Faktor",
                        0.1,
                        10.0,
                        current_sink_factor,  # type: ignore
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


def raw_to_df(raw_data: UploadedFile) -> pd.DataFrame:
    df = pd.read_excel(raw_data, skiprows=1, header=None, dtype=np.float64)  # type: ignore
    header = [f"Temperatur {i}" for i in range(int(len(df.columns) / 2))]
    header.extend([f"Volumenstrom {i}" for i in range(int(len(df.columns) / 2))])
    rename_dict = {  # type: ignore
        list(df.columns)[i]: new_header for (i, new_header) in enumerate(header)
    }
    df.rename(columns=rename_dict, inplace=True)  # type: ignore
    return df


def manipulate_source(header: str, original_df: pd.DataFrame) -> None:
    st.session_state.edited_source[header] = original_df[header].apply(  # type: ignore
        lambda x: x * st.session_state.source_factor  # type: ignore
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
        lambda x: x * st.session_state.sink_factor  # type: ignore
    )
    if re.search("Temperatur", st.session_state.sink_select):
        st.session_state.edited_sink[header][
            st.session_state.edited_sink[header] > st.session_state.max_temp_sink
        ] = st.session_state.max_temp_sink
    else:
        st.session_state.edited_sink[header][
            st.session_state.edited_sink[header] > st.session_state.max_vol_sink
        ] = st.session_state.max_vol_sink
