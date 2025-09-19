# src/views/reports.py
# -*- coding: utf-8 -*-
"""
Vistas de informes (equipo y jugador)
"""
import streamlit as st
from ..components import header_bar
from ..utils import embed_pdf_local, download_button_for_pdf, player_label, set_route
from ..config import TEAM_SLUG, PLAYER_REPORTS_DIR, GENERIC_USER_IMAGE
from ..data.drive_loader import load_players, get_team_report_path


def view_equipo_informe():
    """Renderiza la vista del informe del equipo desde Google Drive"""
    header_bar()
    
    # Obtener equipo seleccionado de session_state
    selected_team = st.session_state.get('selected_team')
    
    # Si no hay equipo seleccionado, usar el por defecto
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
        # Para equipos seleccionados específicos, mostrar advertencia
        if team_name != st.session_state.get('default_team_name', ''):
            st.info(f"📄 Viendo informe de: **{team_name}**")
            st.warning("Funcionalidad de informes dinámicos en desarrollo.")
            if st.button("👥 Ver jugadores disponibles", use_container_width=True):
                set_route("players")
            return
    else:
        team_slug = TEAM_SLUG
    
    # Obtener ruta del informe desde Google Drive (usa configuración por defecto)
    team_report_path = get_team_report_path()
    
    if not team_report_path:
        st.error("📄 Informe del equipo no disponible")
        
        if st.button("👥 Ver jugadores disponibles", use_container_width=True):
            set_route("players")
        
        return
    
    # Si el archivo existe, mostrarlo
    
    # Botón de descarga
    download_button_for_pdf(team_report_path, "⬇️ Descargar informe del equipo", f"{team_slug}.pdf")
    
    # Mostrar PDF
    embed_pdf_local(team_report_path)


def view_jugador_informe():
    """Renderiza la vista del informe de un jugador específico"""
    header_bar()
    
    selected_player = st.session_state.get("selected_player")
    if not selected_player:
        st.error("No se ha seleccionado ningún jugador")
        return
    
    # Cargar datos del jugador
    players = load_players()
    player = next((p for p in players if p.get("slug") == selected_player), None)
    
    if not player:
        st.error("Jugador no encontrado")
        return
    
    st.markdown(f"## 🏀 {player_label(player.get('number', 0), player.get('name', 'Nombre'), player.get('surnames', 'Apellidos'))}")
    
    # Mostrar imagen PNG del informe desde Google Drive
    player_slug = player.get('slug', 'unknown')
    image_filename = f"{player_slug}.png"
    
    # Intentar obtener la imagen desde Google Drive
    from ..data.drive_loader import get_player_image_path
    
    informe_png_path = get_player_image_path(image_filename)
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
    
    # Botones debajo del informe
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Botón descargar imagen del informe
        if image_to_download and image_to_download.exists():
            st.download_button(
                "📄 Descargar informe visual",
                data=image_to_download.read_bytes(),
                file_name=f"informe_{player.get('slug', 'unknown')}.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.button("📄 Descargar informe visual", use_container_width=True, disabled=True)
            st.caption("Imagen no disponible")
    
    with col2:
        st.button("🎬 Ver vídeos de scouting (próximamente)", use_container_width=True, disabled=True)


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