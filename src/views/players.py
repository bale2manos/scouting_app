# src/views/players.py
# -*- coding: utf-8 -*-
"""
Vista de jugadores
"""
import streamlit as st
from pathlib import Path
from ..components import header_bar
from ..utils import player_label, set_route
from ..config import (
    TEAM_NAME_DISPLAY, 
    PLAYERS_PER_ROW, 
    PLAYER_IMAGE_WIDTH,
    PLAYER_REPORTS_DIR,
    GENERIC_USER_IMAGE
)
from ..data.drive_loader import load_players, get_player_image_path


def view_players():
    """Renderiza la vista de jugadores desde Google Drive"""
    header_bar()
    
    # Encabezado
    st.markdown(f"## {TEAM_NAME_DISPLAY}")
    
    # Cargar jugadores desde Google Drive
    players = load_players()
    
    if not players:
        st.info("No se encontraron jugadores para este equipo.")
        return

    cols_per_row = PLAYERS_PER_ROW
    rows = (len(players) + cols_per_row - 1) // cols_per_row

    idx = 0
    for _ in range(rows):
        cols = st.columns(cols_per_row)
        for c in cols:
            if idx >= len(players):
                break
            p = players[idx]; idx += 1
            with c:
                # Crear contenido visual del jugador
                with st.container():
                    # Prioridad de imágenes:
                    # 1. Imagen de URL del Excel
                    # 2. Imagen genérica local
                    
                    image_displayed = False
                    
                    # 1. Intentar imagen URL del Excel
                    if p.get('image_url'):
                        try:
                            st.image(p['image_url'], use_container_width=True)
                            image_displayed = True
                        except:
                            pass  # Si falla la URL, continuar al fallback
                    
                    # 2. Fallback a imagen genérica local
                    if not image_displayed:
                        if GENERIC_USER_IMAGE.exists():
                            st.image(str(GENERIC_USER_IMAGE), use_container_width=True)
                        else:
                            st.markdown("🏀", help="Imagen no disponible")
                    
                    # Botón con el nombre del jugador
                    player_name = _create_player_button_content(p)
                    if st.button(
                        label=player_name,
                        key=f"player_btn_{p.get('slug', idx)}",
                        help=f"Ver informe de {player_name}",
                        use_container_width=True
                    ):
                        set_route("jugador_informe", selected_player=p.get("slug", str(idx)))


def _create_player_button_content(player):
    """Crea el contenido de texto simple para el botón del jugador"""
    # Ahora los datos ya vienen en la estructura correcta
    number = player.get('number', 0)
    name = player.get('name', 'N')
    surnames = player.get('surnames', 'APELLIDOS')
    
    return player_label(number, name, surnames)