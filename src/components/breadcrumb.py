# src/components/breadcrumb.py
# -*- coding: utf-8 -*-
"""
Componente de navegación breadcrumb
"""
import streamlit as st
from ..utils import set_route, apply_styles


def breadcrumb():
    """Renderiza el breadcrumb de navegación"""
    apply_styles()

    route = st.session_state.get("route", "home")

    if route in ("home", "team", "equipo_informe"):
        trail = ["Inicio", "Equipo"]
        last_label = "Equipo"
    elif route in ("players", "jugador_modal", "jugador_informe"):
        trail = ["Inicio", "Equipo", "Jugadores"]
        last_label = "Jugadores"
    else:
        trail = ["Inicio"]
        last_label = "Inicio"

    st.markdown("<div class='bc-line bc-inline'>", unsafe_allow_html=True)
    cols = st.columns(len(trail) * 2 - 1, gap="small")
    col_i = 0
    for i, label in enumerate(trail):
        with cols[col_i]:
            if label == last_label:
                st.markdown(f"<span class='bc-current'>{label}</span>", unsafe_allow_html=True)
            else:
                if st.button(label, key=f"bc_{i}", use_container_width=False):
                    if label == "Inicio":
                        set_route("home")
                    elif label == "Equipo":
                        set_route("team")
                    elif label == "Jugadores":
                        set_route("players")
        col_i += 1
        if i < len(trail) - 1:
            with cols[col_i]:
                st.markdown("<span class='bc-sep'>&gt;</span>", unsafe_allow_html=True)
            col_i += 1
    st.markdown("</div>", unsafe_allow_html=True)