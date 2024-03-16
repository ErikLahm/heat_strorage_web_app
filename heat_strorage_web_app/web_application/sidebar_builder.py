import streamlit as st
from pde_calculations.sim_enums import InitialStateType
from web_application.param_enums import Params


def build_sidebar():
    display_sidebar_head()
    get_raw_data()
    display_data_features()
    st.sidebar.divider()
    display_vessel_widgets()
    display_medium_widgets()
    display_environment()
    display_heater()
    display_cooler_settings()
    display_simulation()


def display_sidebar_head():
    st.sidebar.image("heat_strorage_web_app/resources/emv_logo.png")
    st.sidebar.header("Datensatz Import")


def display_data_features():
    delta_t = st.sidebar.number_input(
        "Zeitdifferenz zw. Messwerten [s]",
        min_value=1,
        value=st.session_state.get(Params.DELTA_T.value, 300),
        step=60,
        help="Was ist die Zeitdifferenz zwischen je zwei Messwerten im Datensatz.",
    )
    days = st.sidebar.number_input(
        "Anzahl der Messtage",
        min_value=1,
        value=st.session_state.get(Params.DAYS.value, 7),
        step=1,
    )
    st.session_state[Params.DELTA_T.value] = delta_t
    st.session_state[Params.DAYS.value] = days


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
    st.sidebar.header("Behältermaße")
    height = st.sidebar.number_input(
        "Höhe in $\\text{m}$",
        min_value=0.0,
        max_value=40.0,
        value=st.session_state.get(Params.HEIGHT.value, 8.0),
        step=1.0,
    )
    radius = st.sidebar.number_input(
        "Radius in $\\text{m}$",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.get(Params.RADIUS.value, 2.0),
        step=0.5,
    )
    num_segs = st.sidebar.number_input(
        "Segmentierung",
        min_value=2,
        max_value=20,
        value=st.session_state.get(Params.NUM_SEGS.value, 7),
        step=1,
    )
    st.sidebar.selectbox(
        "Anfangszustand",
        [value.value for value in InitialStateType],
        key=Params.INIT_STATE.value,
    )
    init_max_t = st.sidebar.number_input(
        "initiale Höchsttemperatur in $\degree \\text{C}$",  # type: ignore
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.INIT_MAX_T.value, 70.0),
        step=1.0,
    )
    init_min_t = st.sidebar.number_input(
        "initiale Niedertemperatur in $\degree \\text{C}$",  # type: ignore
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.INIT_MIN_T.value, 20.0),
        step=1.0,
    )
    st.session_state[Params.HEIGHT.value] = height
    st.session_state[Params.RADIUS.value] = radius
    st.session_state[Params.NUM_SEGS.value] = num_segs
    st.session_state[Params.INIT_MAX_T.value] = init_max_t
    st.session_state[Params.INIT_MIN_T.value] = init_min_t


def display_medium_widgets():
    st.sidebar.header("Medium")
    density = st.sidebar.number_input(
        "Dichte $\\varrho$ in $\\frac{\\text{kg}}{\\text{m}^3}$",
        min_value=0.0,
        value=st.session_state.get(Params.DENSITY.value, 1000.0),
    )
    c_p = st.sidebar.number_input(
        "Spezifische Wärmekapazität $c_p$ in $\\frac{\\text{J}}{\\text{kg} \\text{K}}$",
        min_value=0.0,
        value=st.session_state.get(Params.C_P.value, 4184.0),
    )
    alpha = st.sidebar.number_input(
        "Fluid Diffusivity $\\alpha$ in $\\frac{\\text{m}^2}{\\text{s}}(10^{-7})$",
        min_value=0.0,
        value=st.session_state.get(Params.DIFFUSIVITY.value, 1.43),
    )
    st.session_state[Params.DENSITY.value] = density
    st.session_state[Params.C_P.value] = c_p
    st.session_state[Params.DIFFUSIVITY.value] = alpha


def display_environment():
    st.sidebar.header("Umgebungsvariablen")
    t_env = st.sidebar.number_input(
        "Umgebungstemperatur $T_{\\text{ext}}$ in $\degree \\text{C}$",  # type:ignore
        value=st.session_state.get(Params.T_ENV.value, 20.0),
    )
    st.session_state[Params.T_ENV.value] = t_env


def display_heater():
    st.sidebar.header("Heizung")
    heat_percentage = st.sidebar.number_input(
        "kritische Kesselschicht",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.get(Params.HEAT_PERC.value, 0.2),
        step=0.1,
        help="Schichtdicke des Kessels, anhand derer die Referenztemperatur gemessen wird.",
    )
    heat_crit = st.sidebar.number_input(
        "kritische Temperatur",
        min_value=0.0,
        max_value=99.0,
        value=st.session_state.get(Params.HEAT_CRIT_T.value, 60.0),
        step=0.5,
        help="Ab welcher Temperatur soll die Heizung anspringen.",
    )
    heat_goal = st.sidebar.number_input(
        "Zieltemperatur",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.HEAT_GOAL_T.value, 80.0),
        step=0.5,
        help="Ab welcher Temperatur schaltet die Heizung ab.",
    )
    heat_t = st.sidebar.number_input(
        "Heiztemperatur",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get(Params.HEAT_T.value, 85.0),
        step=0.5,
        help="Auf welche Temperatur werden die Ströme aufgeheizt.",
    )
    st.session_state[Params.HEAT_PERC.value] = heat_percentage
    st.session_state[Params.HEAT_CRIT_T.value] = heat_crit
    st.session_state[Params.HEAT_GOAL_T.value] = heat_goal
    st.session_state[Params.HEAT_T.value] = heat_t


def display_cooler_settings():
    st.sidebar.header("Notkühler")
    cooler_goal = st.sidebar.number_input(
        "Zieltemperatur",
        min_value=1.0,
        value=st.session_state.get(Params.COOLER_GOAL_T.value, 30.0),
        step=1.0,
        help="Auf welche Temperatur soll der Zulauf zu den Erzeugern abgekühlt werden.",
    )
    st.session_state[Params.COOLER_GOAL_T.value] = cooler_goal


def display_simulation():
    st.sidebar.button("Simulieren", key="sim_button")
