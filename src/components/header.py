# src/components/header.py
# -*- coding: utf-8 -*-
"""
Componente de header de la aplicación
"""
import streamlit as st
from src.utils.ui import back_button


def header_bar():
    """Renderiza la barra de header simplificada con botón atrás"""
    left, mid, right = st.columns([2, 6, 4], vertical_alignment="center")
    
    with left:
        # Solo mostrar botón atrás si no estamos en home
        route = st.session_state.get("route", "home")
        if route != "home":
            back_button()
    
    with mid:
        st.markdown("<h2 style='text-align:center;margin:0'>🏀 Scouting Hub</h2>", unsafe_allow_html=True)
    
    with right:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Perfil", use_container_width=True):
                st.toast("Sección de perfil (futuro)")
        with col2:
            st.button("📚 Equipos", use_container_width=True, disabled=True)