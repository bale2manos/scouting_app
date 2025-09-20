# src/components/header.py
# -*- coding: utf-8 -*-
"""
Componente de header de la aplicación
"""
import streamlit as st
from src.utils.ui import back_button, set_route


def header_bar():
    """Renderiza la barra de header simplificada con botón home y atrás"""
    left, mid, right = st.columns([3, 6, 3], vertical_alignment="center")
    
    with left:
        # Crear dos columnas en la izquierda para Home y Atrás
        home_col, back_col = st.columns([1, 1])
        
        with home_col:
            if st.button("🏠 Home", use_container_width=True, key="header_home"):
                set_route("home")
        
        with back_col:
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
                pass  # Funcionalidad futura
        with col2:
            if st.button("📚 Equipos", use_container_width=True):
                set_route("teams")