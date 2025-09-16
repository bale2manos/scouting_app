# app.py
# -*- coding: utf-8 -*-
"""
Aplicación principal Scouting Hub - Versión modularizada
"""
import streamlit as st

# Importar módulos de la aplicación
from src.views import (
    view_home,
    view_team, 
    view_equipo_informe,
    view_jugador_informe,
    view_players,
    show_loading_screen,
    is_app_ready
)
from src.utils import set_route
from src.data.drive_loader import auto_sync_on_load, debug_player_files, force_sync


def main():
    """Función principal de la aplicación"""
    st.set_page_config(page_title="Scouting Hub", layout="wide")
    
    # Verificar si la app está lista
    if not is_app_ready():
        # Mostrar pantalla de carga profesional
        show_loading_screen()
        
        # Sincronización automática silenciosa en background
        auto_sync_on_load()
        
        # Recargar para mostrar contenido
        st.rerun()
        return
    
    # App lista - mostrar contenido normal
    # Router principal
    route = st.session_state.get("route", "home")

    if route == "home":
        view_home()
    elif route == "team":
        view_team()
    elif route == "equipo_informe":
        view_equipo_informe()
    elif route == "players":
        view_players()
    elif route == "jugador_informe":
        view_jugador_informe()
    elif route == "debug":
        # Página temporal de debugging
        st.title("Archivos de Jugadores")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Forzar Sincronización"):
                force_sync()
                st.rerun()
        
        with col2:
            if st.button("📋 Mostrar Debug Info"):
                debug_player_files()
        
        st.markdown("---")
        st.markdown("Para acceder: Agrega `?route=debug` a la URL")
        
    else:
        set_route("home")


if __name__ == "__main__":
    main()
