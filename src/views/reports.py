# src/views/reports.py
# -*- coding: utf-8 -*-
"""
Vistas de informes (equipo y jugador)
"""
import streamlit as st
import time
from ..components import header_bar
from ..utils import embed_pdf_local, download_button_for_pdf, player_label, set_route
from ..auth.db_logger import DatabaseLogger
from ..config import TEAM_SLUG, PLAYER_REPORTS_DIR, GENERIC_USER_IMAGE, TEAM_NAME_DISPLAY
from ..data.drive_loader import load_players, get_team_report_path


def view_equipo_informe():
    """Renderiza la vista del informe del equipo desde Google Drive"""
    from ..data.drive_loader import get_team_report_path_by_drive_id
    
    # Inicializar logger para logging
    auth = DatabaseLogger()
    
    header_bar()
    
    # Obtener equipo seleccionado de session_state
    selected_team = st.session_state.get('selected_team')
    
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
        drive_id = selected_team['drive_id']
        
        # Registrar visualización del informe de equipo cada vez que se accede
        auth.log_report_view("team", team_name)
        
        st.info(f"📄 Viendo informe de: **{team_name}**")
        
        # Verificar si es el equipo principal configurado
        if (team_name.upper() == TEAM_NAME_DISPLAY.upper() or 
            team_slug == TEAM_SLUG or 
            drive_id is None):
            # Es el equipo principal, usar la función existente
            team_report_path = get_team_report_path()
        else:
            # Es otro equipo, usar la nueva función dinámica
            with st.spinner(f"🔍 Buscando informe de {team_name} en Google Drive..."):
                team_report_path = get_team_report_path_by_drive_id(team_name, team_slug, drive_id)
            
        if team_report_path:
            # Sistema simplificado de detección de descarga
            team_download_session_key = f"team_download_session_{team_slug}"
            
            # Botón de descarga
            download_clicked = download_button_for_pdf(
                team_report_path, 
                "⬇️ Descargar informe del equipo", 
                f"{team_slug}.pdf",
                f"download_team_{team_slug}"
            )
            
            # Registrar descarga cuando se hace clic
            if download_clicked:
                auth.log_report_download("team", team_name)
            
            # Mostrar PDF
            embed_pdf_local(team_report_path)
        else:
            st.warning(f"📄 **No se encontró informe** para **{team_name}**")
            st.info("💡 El sistema buscó archivos PDF en la carpeta del equipo en Google Drive.")
            
            # Botones de navegación
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👥 Ver jugadores del equipo", use_container_width=True, type="primary"):
                    set_route("players")
            with col2:
                if st.button("🔙 Volver a equipos", use_container_width=True):
                    set_route("teams")
                
    else:
        # Sin equipo seleccionado, usar configuración por defecto
        team_slug = TEAM_SLUG
        team_report_path = get_team_report_path()
        
        if not team_report_path:
            st.error("📄 Informe del equipo no disponible")
            
            if st.button("👥 Ver jugadores disponibles", use_container_width=True):
                set_route("players")
            
            return
        
        # Mostrar el informe por defecto
        # Registrar visualización del informe de equipo (equipo por defecto, solo una vez)
        default_view_key = f"default_team_view_logged_{TEAM_SLUG}"
        # Registrar visualización del informe del equipo principal cada vez
        auth.log_report_view("team", TEAM_NAME_DISPLAY)
        
        # Botón de descarga
        download_clicked = download_button_for_pdf(
            team_report_path, 
            "⬇️ Descargar informe del equipo", 
            f"{team_slug}.pdf",
            f"download_default_team_{team_slug}"
        )
        
        # Registrar descarga cuando se hace clic
        if download_clicked:
            auth.log_report_download("team", TEAM_NAME_DISPLAY)
        
        # Mostrar PDF
        embed_pdf_local(team_report_path)


def view_jugador_informe():
    """Renderiza la vista del informe de un jugador específico"""
    # Inicializar logger para logging
    auth = DatabaseLogger()
    
    header_bar()
    
    selected_player = st.session_state.get("selected_player")
    if not selected_player:
        st.error("No se ha seleccionado ningún jugador")
        return
    
    # Cargar datos del jugador del equipo correspondiente
    selected_team = st.session_state.get('selected_team')
    
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
        drive_id = selected_team['drive_id']
        
        # Verificar si es el equipo principal configurado
        if (team_name.upper() == TEAM_NAME_DISPLAY.upper() or 
            team_slug == TEAM_SLUG or 
            drive_id is None):
            # Es el equipo principal, usar la función existente
            players = load_players()
        else:
            # Es otro equipo, usar la nueva función dinámica
            from ..data.drive_loader import load_players_by_drive_id
            players = load_players_by_drive_id(team_name, team_slug, drive_id)
    else:
        # Sin equipo seleccionado, usar configuración por defecto
        players = load_players()
    
    player = next((p for p in players if p.get("slug") == selected_player), None)
    
    if not player:
        st.error("Jugador no encontrado")
        return
    
    player_name = player_label(player.get('number', 0), player.get('name', 'Nombre'), player.get('surnames', 'Apellidos'))
    
    # Registrar visualización del informe de jugador cada vez
    auth.log_report_view("player", player_name)
    
    st.markdown(f"## 🏀 {player_name}")
    
    # Obtener información de la imagen del informe
    player_slug = player.get('slug', 'unknown')
    image_filename = f"{player_slug}.png"
    
    # Intentar obtener la imagen desde Google Drive
    from ..data.drive_loader import get_player_image_path, get_player_image_path_by_drive_id
    
    # Determinar qué función usar para obtener la imagen
    if selected_team and (team_name.upper() != TEAM_NAME_DISPLAY.upper() and 
                         team_slug != TEAM_SLUG and 
                         drive_id is not None):
        # Es otro equipo, usar la función específica para ese equipo
        informe_png_path = get_player_image_path_by_drive_id(image_filename, team_name, team_slug, drive_id)
    else:
        # Es el equipo principal, usar la función estándar
        informe_png_path = get_player_image_path(image_filename)
    
    # Botones por encima del informe
    col1, col2 = st.columns(2)
    
    with col1:
        # Botón descargar imagen del informe
        if informe_png_path and informe_png_path.exists():
            # Sistema simplificado de detección de descarga
            player_slug = player.get('slug', 'unknown')
            download_session_key = f"player_download_session_{player_slug}"
            
            # Botón de descarga con key estable
            clicked = st.download_button(
                "📄 Descargar informe",
                data=informe_png_path.read_bytes(),
                file_name=f"informe_{player_slug}.png",
                mime="image/png",
                use_container_width=True,
                type="primary",
                key=f"download_player_{player_slug}"
            )
            
            # Registrar descarga cuando se hace clic
            if clicked:
                auth.log_report_download("player", player_name)
                    
        else:
            st.button("📄 Descargar informe", use_container_width=True, disabled=True, help="Informe no disponible")
    
    with col2:
        st.button("🎬 Ver vídeos", use_container_width=True, disabled=True, help="Funcionalidad próximamente disponible")
    
    st.markdown("---")
    
    image_to_download = None
    
    # Intentar cargar la imagen del informe
    if informe_png_path and informe_png_path.exists():
        try:
            st.image(str(informe_png_path), use_container_width=True)
            image_to_download = informe_png_path
        except Exception as e:
            # Usar imagen genérica como fallback
            _show_generic_image()
            image_to_download = _get_generic_image_path()
    else:
        st.info("Imagen del informe no disponible")
        
        # Intentar forzar descarga
        from ..data.drive_loader import force_sync
        if st.button("🔄 Reintentar descarga", key="retry_download"):
            force_sync()
            st.rerun()
        
        # Usar imagen genérica como fallback
        _show_generic_image()
        image_to_download = _get_generic_image_path()


def _show_generic_image():
    """Muestra la imagen genérica de usuario con manejo robusto de errores"""
    if GENERIC_USER_IMAGE.exists():
        try:
            st.image(str(GENERIC_USER_IMAGE), use_container_width=True)
            return True
        except Exception as e:
            st.info("El informe visual no está disponible en este momento.")
            return False
    else:
        st.info("El informe visual no está disponible en este momento.")
        return False


def _get_generic_image_path():
    """Retorna el path de la imagen genérica si existe"""
    return GENERIC_USER_IMAGE if GENERIC_USER_IMAGE.exists() else None