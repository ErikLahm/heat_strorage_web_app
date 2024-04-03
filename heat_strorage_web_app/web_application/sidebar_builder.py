import streamlit as st
from web_application.backend_connection import (
    get_parameter_data,
    set_parameter_data,
)
from web_application.data_base_handle import ParamDataBase
from pde_calculations.sim_enums import InitialStateType
from web_application.param_enums import ParamDefaultChoices, Params


def build_sidebar():
    display_sidebar_head()
    get_raw_data()
    display_parameter_load_section()
    display_data_features()
    display_vessel_widgets()
    display_medium_widgets()
    display_environment()
    display_heater()
    display_cooler_settings()
    display_simulation()


def display_sidebar_head():
    st.sidebar.image("heat_strorage_web_app/resources/emv_logo.png")
    st.sidebar.header("Datensatz Import")


def display_parameter_load_section():
    param_db = ParamDataBase()
    options = [option.value for option in ParamDefaultChoices]
    set_names = param_db.get_set_names()
    options.extend(set_names)
    st.sidebar.selectbox(
        label="Parametersatz Auswahl",
        options=options,
        key="parameter_choice",
    )

    def apply_param_set() -> None:
        param_dict = param_db.get_param_set(set_name=st.session_state.parameter_choice)
        set_parameter_data(param_dict=param_dict)

    if st.session_state.parameter_choice in set_names:
        st.sidebar.button(label="Anwenden", on_click=apply_param_set)
        st.sidebar.button(
            label="Entfernen",
            on_click=param_db.remove_set,
            args=(st.session_state.parameter_choice,),
        )

    def save_set_to_db() -> None:
        set_name = st.session_state.name_param_choice
        param_dict = get_parameter_data()
        param_db.append_set(set_name, param_dict)

    if st.session_state.parameter_choice == ParamDefaultChoices.NEW_SET.value:
        st.sidebar.text_input(
            label="Name des neuen Parametersatzes", key="name_param_choice"
        )
        st.sidebar.button(label="Speichern", on_click=save_set_to_db)


def display_data_features():
    st.sidebar.number_input(
        "Zeitdifferenz zw. Messwerten [s]",
        min_value=1,
        value=st.session_state.get(Params.DELTA_T.value, 300),
        step=60,
        help="Was ist die Zeitdifferenz zwischen je zwei Messwerten im Datensatz.",
        key=Params.DELTA_T.value,
    )
    st.sidebar.number_input(
        "Anzahl der Messtage",
        min_value=1,
        value=st.session_state.get(Params.DAYS.value, 7),
        step=1,
        key=Params.DAYS.value,
    )


def get_raw_data():
    source_data_raw = st.sidebar.file_uploader(
        "Quellen laden", type=["xlsx"], help="Datensatz wählen", key="source_data_raw"
    )
    sink_data_raw = st.sidebar.file_uploader(
        "Senken laden", type=["xlsx"], help="Senken laden", key="sink_data_raw"
    )
    if not (source_data_raw or sink_data_raw):
        st.error("Bitte mindestens einen Datensatz hochladen.")


def display_vessel_widgets():
    st.sidebar.divider()
    st.sidebar.header("Behältermaße")
    st.sidebar.number_input(
        "Höhe in $\\text{m}$",
        min_value=0.0,
        max_value=40.0,
        value=st.session_state.get(Params.HEIGHT.value, 8.0),
        step=1.0,
        key=Params.HEIGHT.value,
    )
    st.sidebar.number_input(
        "Radius in $\\text{m}$",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.get(Params.RADIUS.value, 2.0),
        step=0.5,
        key=Params.RADIUS.value,
    )
    st.sidebar.number_input(
        "Segmentierung",
        min_value=2,
        max_value=20,
        value=st.session_state.get(Params.NUM_SEGS.value, 7),
        step=1,
        key=Params.NUM_SEGS.value,
    )
    intial_states_list = [state.value for state in InitialStateType]
    init_state = st.sidebar.selectbox(
        "Anfangszustand",
        intial_states_list,
        key=Params.INIT_STATE.value,
        index=st.session_state.get("init_state_idx", 0),
    )
    st.sidebar.number_input(
        "initiale Höchsttemperatur in $\degree \\text{C}$",  # type: ignore
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.INIT_MAX_T.value, 70.0),
        step=1.0,
        key=Params.INIT_MAX_T.value,
    )
    st.sidebar.number_input(
        "initiale Niedertemperatur in $\degree \\text{C}$",  # type: ignore
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.INIT_MIN_T.value, 20.0),
        step=1.0,
        key=Params.INIT_MIN_T.value,
    )
    st.session_state.init_state_idx = intial_states_list.index(str(init_state))


def display_medium_widgets():
    st.sidebar.header("Medium")
    st.sidebar.number_input(
        "Dichte $\\varrho$ in $\\frac{\\text{kg}}{\\text{m}^3}$",
        min_value=0.0,
        value=st.session_state.get(Params.DENSITY.value, 1000.0),
        key=Params.DENSITY.value,
    )
    st.sidebar.number_input(
        "Spezifische Wärmekapazität $c_p$ in $\\frac{\\text{J}}{\\text{kg} \\text{K}}$",
        min_value=0.0,
        value=st.session_state.get(Params.C_P.value, 4184.0),
        key=Params.C_P.value,
    )
    st.sidebar.number_input(
        "Fluid Diffusivity $\\alpha$ in $\\frac{\\text{m}^2}{\\text{s}}(10^{-7})$",
        min_value=0.0,
        value=st.session_state.get(Params.DIFFUSIVITY.value, 1.43),
        key=Params.DIFFUSIVITY.value,
    )


def display_environment():
    st.sidebar.header("Umgebungsvariablen")
    st.sidebar.number_input(
        "Umgebungstemperatur $T_{\\text{ext}}$ in $\degree \\text{C}$",  # type:ignore
        value=st.session_state.get(Params.T_ENV.value, 20.0),
        key=Params.T_ENV.value,
    )


def display_heater():
    st.sidebar.header("Heizung")
    st.sidebar.number_input(
        "kritische Kesselschicht",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.get(Params.HEAT_PERC.value, 0.2),
        step=0.1,
        help="Schichtdicke des Kessels, anhand derer die Referenztemperatur gemessen wird.",
        key=Params.HEAT_PERC.value,
    )
    st.sidebar.number_input(
        "kritische Temperatur",
        min_value=0.0,
        max_value=99.0,
        value=st.session_state.get(Params.HEAT_CRIT_T.value, 60.0),
        step=0.5,
        help="Ab welcher Temperatur soll die Heizung anspringen.",
        key=Params.HEAT_CRIT_T.value,
    )
    st.sidebar.number_input(
        "Zieltemperatur",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.HEAT_GOAL_T.value, 80.0),
        step=0.5,
        help="Ab welcher Temperatur schaltet die Heizung ab.",
        key=Params.HEAT_GOAL_T.value,
    )
    st.sidebar.number_input(
        "Heiztemperatur",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.HEAT_T.value, 85.0),
        step=0.5,
        help="Auf welche Temperatur werden die Ströme aufgeheizt.",
        key=Params.HEAT_T.value,
    )


def display_cooler_settings():
    st.sidebar.header("Notkühler")
    st.sidebar.number_input(
        "Zieltemperatur",
        min_value=1.0,
        value=st.session_state.get(Params.COOLER_GOAL_T.value, 30.0),
        step=1.0,
        help="Auf welche Temperatur soll der Zulauf zu den Erzeugern abgekühlt werden.",
        key=Params.COOLER_GOAL_T.value,
    )


def display_simulation():
    st.sidebar.button("Simulieren", key="sim_button")
