# src/views/players.py
# -*- coding: utf-8 -*-
"""
Vista de jugadores
"""
import streamlit as st
from pathlib import Path
from ..components import header_bar
from ..utils import player_label, set_route, PlayerClassificationManager, can_classify_players
from ..config import (
    TEAM_NAME_DISPLAY, 
    TEAM_SLUG,
    PLAYERS_PER_ROW, 
    PLAYER_IMAGE_WIDTH,
    PLAYER_REPORTS_DIR,
    GENERIC_USER_IMAGE
)
from ..data.drive_loader import load_players, get_player_image_path


def view_players():
    """Renderiza la vista de jugadores desde Google Drive"""
    from ..data.drive_loader import load_players_by_drive_id
    
    header_bar()
    
    # Obtener equipo seleccionado de session_state
    selected_team = st.session_state.get('selected_team')
    
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
        drive_id = selected_team['drive_id']
        
        # Encabezado
        st.markdown(f"## {team_name}")
        
        # Verificar si es el equipo principal configurado
        if (team_name.upper() == TEAM_NAME_DISPLAY.upper() or 
            team_slug == TEAM_SLUG or 
            drive_id is None):
            # Es el equipo principal, usar la función existente
            players = load_players()
        else:
            # Es otro equipo, usar la nueva función dinámica
            with st.spinner(f"Cargando jugadores de {team_name} desde Google Drive..."):
                players = load_players_by_drive_id(team_name, team_slug, drive_id)
                
    else:
        # Sin equipo seleccionado, usar configuración por defecto
        team_name = TEAM_NAME_DISPLAY
        team_slug = TEAM_SLUG
        st.markdown(f"## {team_name}")
        players = load_players()
    
    if not players:
        st.info("No se encontraron jugadores para este equipo.")
        return

    # ===== BOTÓN DE CLASIFICACIÓN (solo para admin/coach) =====
    current_user = st.session_state.get('user')
    
    # Si no hay user en session_state pero sí está autenticado, obtenerlo
    if not current_user and st.session_state.get('authenticated', False):
        from ..auth.db_authenticator import DatabaseAuthenticator
        auth = DatabaseAuthenticator()
        current_user = auth.get_current_user()
        if current_user:
            st.session_state['user'] = current_user
    
    if can_classify_players(current_user):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"👥 Mostrando jugadores de: **{team_name}**")
        with col2:
            if st.button("📋 Clasificar Jugadores", use_container_width=True):
                st.session_state['show_classification_dialog'] = True
        
        # Mostrar diálogo de clasificación
        if st.session_state.get('show_classification_dialog', False):
            _show_classification_dialog(team_slug, players)
    else:
        st.info(f"👥 Mostrando jugadores de: **{team_name}**")
    
    # ===== RENDERIZAR JUGADORES CLASIFICADOS =====
    _render_classified_players(team_slug, players)


def _create_player_button_content(player):
    """Crea el contenido de texto simple para el botón del jugador"""
    # Ahora los datos ya vienen en la estructura correcta
    number = player.get('number', 0)
    name = player.get('name', 'N')
    surnames = player.get('surnames', 'APELLIDOS')
    
    return player_label(number, name, surnames)


def _render_classified_players(team_slug: str, players: list):
    """Renderiza jugadores organizados por clasificación"""
    # Inicializar gestor de clasificaciones
    classification_manager = PlayerClassificationManager()
    
    # Clasificar jugadores
    classified = classification_manager.classify_players_list(team_slug, players)
    
    cols_per_row = PLAYERS_PER_ROW
    
    # Renderizar EXTERIORES
    if classified['exterior']:
        st.markdown("### 🔵 EXTERIORES")
        st.markdown(f"*{len(classified['exterior'])} jugador(es)*")
        _render_player_grid(classified['exterior'], cols_per_row, "ext")
        st.markdown("---")
    
    # Renderizar INTERIORES
    if classified['interior']:
        st.markdown("### 🔴 INTERIORES")
        st.markdown(f"*{len(classified['interior'])} jugador(es)*")
        _render_player_grid(classified['interior'], cols_per_row, "int")
        st.markdown("---")
    
    # Renderizar SIN CLASIFICAR
    if classified['unclassified']:
        st.markdown("### ⚪ SIN CLASIFICAR")
        st.markdown(f"*{len(classified['unclassified'])} jugador(es)*")
        _render_player_grid(classified['unclassified'], cols_per_row, "unc")


def _render_player_grid(players: list, cols_per_row: int, prefix: str):
    """Renderiza una cuadrícula de jugadores"""
    rows = (len(players) + cols_per_row - 1) // cols_per_row
    
    idx = 0
    for row_num in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx, c in enumerate(cols):
            if idx >= len(players):
                break
            p = players[idx]
            idx += 1
            
            with c:
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
                    player_slug = p.get('slug', f"{prefix}_{idx}")
                    if st.button(
                        label=player_name,
                        key=f"player_btn_{prefix}_{player_slug}_{row_num}_{col_idx}",
                        help=f"Ver informe de {player_name}",
                        use_container_width=True
                    ):
                        set_route("jugador_informe", selected_player=player_slug)


def _show_classification_dialog(team_slug: str, players: list):
    """Muestra el diálogo modal para clasificar jugadores"""
    
    @st.dialog("📋 Clasificar Jugadores", width="large")
    def classification_dialog():
        st.markdown("""
        **Clasifica a los jugadores en dos categorías:**
        - 🔵 **EXTERIOR**: Bases, escoltas, aleros
        - 🔴 **INTERIOR**: Ala-pívots, pívots
        """)
        
        # Inicializar gestor
        classification_manager = PlayerClassificationManager()
        
        # Obtener clasificaciones actuales
        current_classifications = classification_manager.get_team_classifications(team_slug)
        
        # Inicializar estado temporal si no existe
        if 'temp_classifications' not in st.session_state:
            st.session_state.temp_classifications = {}
            for player in players:
                slug = player.get('slug')
                if slug:
                    st.session_state.temp_classifications[slug] = current_classifications.get(slug)
        
        st.markdown("---")
        
        # Mostrar jugadores con opciones de clasificación
        for i, player in enumerate(players):
            player_slug = player.get('slug')
            if not player_slug:
                continue
            
            player_name = _create_player_button_content(player)
            
            # Obtener clasificación actual
            current_class = st.session_state.temp_classifications.get(player_slug)
            
            # Determinar índice para radio button
            if current_class == 'exterior':
                default_idx = 0
            elif current_class == 'interior':
                default_idx = 1
            else:
                default_idx = 2
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.markdown(f"**{player_name}**")
            
            with col2:
                selection = st.radio(
                    "Clasificación",
                    options=["🔵 Exterior", "🔴 Interior", "⚪ Sin clasificar"],
                    index=default_idx,
                    key=f"class_radio_{player_slug}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                # Actualizar clasificación temporal
                if selection == "🔵 Exterior":
                    st.session_state.temp_classifications[player_slug] = 'exterior'
                elif selection == "🔴 Interior":
                    st.session_state.temp_classifications[player_slug] = 'interior'
                else:
                    st.session_state.temp_classifications[player_slug] = None
        
        st.markdown("---")
        
        # Botones de acción
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("✅ Guardar cambios", type="primary", use_container_width=True):
                # Guardar clasificaciones
                success = classification_manager.set_multiple_classifications(
                    team_slug,
                    st.session_state.temp_classifications
                )
                
                if success:
                    st.success("✅ Clasificaciones guardadas correctamente")
                    # Limpiar estado temporal
                    del st.session_state.temp_classifications
                    st.session_state.show_classification_dialog = False
                    st.rerun()
                else:
                    st.error("❌ Error al guardar las clasificaciones")
        
        with col2:
            if st.button("🔄 Restaurar", use_container_width=True):
                # Restaurar a valores guardados
                st.session_state.temp_classifications = {}
                for player in players:
                    slug = player.get('slug')
                    if slug:
                        st.session_state.temp_classifications[slug] = current_classifications.get(slug)
                st.rerun()
        
        with col3:
            if st.button("❌ Cancelar", use_container_width=True):
                # Limpiar estado temporal y cerrar
                if 'temp_classifications' in st.session_state:
                    del st.session_state.temp_classifications
                st.session_state.show_classification_dialog = False
                st.rerun()
    
    # Mostrar el diálogo
    classification_dialog()
