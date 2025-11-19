# src/views/team.py
# -*- coding: utf-8 -*-
"""
Vista del equipo
"""
import streamlit as st
import base64
from ..components import header_bar
from ..utils import find_image_detailed, set_route
from ..auth.db_logger import DatabaseLogger
from ..config import TEAM_NAME_DISPLAY, TEAM_LOGO_DIR, TEAM_SLUG


def view_team():
    """Renderiza la vista del equipo simplificada"""
    # Registrar visualización de informe de equipo
    auth = DatabaseLogger()
    
    header_bar()
    
    # Obtener equipo seleccionado de session_state
    selected_team = st.session_state.get('selected_team')
    
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
        # Registrar que se está viendo el informe de este equipo (solo una vez por visita)
        team_view_key = f"team_overview_logged_{team_slug}"
        if not st.session_state.get(team_view_key, False):
            auth.log_report_view("team", team_name)
            st.session_state[team_view_key] = True
    else:
        team_name = TEAM_NAME_DISPLAY
        team_slug = TEAM_SLUG
        # Registrar informe de equipo por defecto (solo una vez por visita)
        default_team_view_key = f"default_team_overview_logged_{team_slug}"
        if not st.session_state.get(default_team_view_key, False):
            auth.log_report_view("team", team_name)
            st.session_state[default_team_view_key] = True

    # Header con título
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem; 
                color: white; text-align: center;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0; 
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{team_name}</h1>
    </div>
    """, unsafe_allow_html=True)

    # Layout de dos columnas
    col1, col2 = st.columns([1, 2])

    with col1:
        # Logo del equipo
        try:
            # Buscar el logo del equipo (find_image_detailed espera un Path sin extensión)
            logo_base_path = TEAM_LOGO_DIR / team_slug
            logo_path, tried_paths = find_image_detailed(logo_base_path)
            
            if logo_path and logo_path.exists():
                # Mostrar logo real del equipo
                with open(logo_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                
                # Detectar tipo MIME basado en la extensión
                ext = logo_path.suffix.lower()
                mime_type = "image/png"
                if ext == ".jpg" or ext == ".jpeg":
                    mime_type = "image/jpeg"
                elif ext == ".webp":
                    mime_type = "image/webp"
                
                logo_tag = f"""
                    <div style="text-align: center; margin-bottom: 1rem;">
                        <img src="data:{mime_type};base64,{img_data}" 
                             style="width: 200px; height: 200px; object-fit: contain; 
                                    border-radius: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.25);"
                             alt="Logo {team_name}">
                    </div>
                """
                st.markdown(logo_tag, unsafe_allow_html=True)
            else:
                # Fallback: emoji si no se encuentra el logo
                logo_tag = """
                    <div style="text-align: center; font-size: 4rem; opacity: 0.5; margin-bottom: 1rem;">🏀</div>
                """
                st.markdown(logo_tag, unsafe_allow_html=True)
                
        except Exception as e:
            # En caso de error, mostrar emoji genérico
            logo_tag = """
                <div style="text-align: center; font-size: 4rem; opacity: 0.5; margin-bottom: 1rem;">🏀</div>
            """
            st.markdown(logo_tag, unsafe_allow_html=True)

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VER INFORME
        if st.button("📄 VER INFORME", 
                    help="Análisis completo del equipo", 
                    width="stretch", 
                    type="primary"):
            # Registrar que se está viendo el informe del equipo
            auth.log_report_view("team", team_name)
            set_route("equipo_informe")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VER VIDEOS DEL EQUIPO
        from ..utils.video_manager import video_manager
        team_videos = video_manager.get_team_videos(team_name)
        has_team_videos = len(team_videos) > 0
        
        if st.button("🎥 VER VIDEOS DEL EQUIPO", 
                    help="Videos de análisis del equipo" if has_team_videos else "No hay videos disponibles", 
                    width="stretch",
                    disabled=not has_team_videos):
            if has_team_videos:
                # Configurar contexto para mostrar videos del equipo
                st.session_state['video_context'] = {
                    'type': 'team',
                    'team_name': team_name
                }
                set_route("videos")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VER JUGADORES
        if st.button("� VER JUGADORES", 
                    help="Ver jugadores del equipo", 
                    width="stretch"):
            # Registrar que se están viendo los jugadores del equipo
            auth.log_report_view("team", f"{team_name} - Jugadores")
            set_route("players")
        
        st.markdown("<br>", unsafe_allow_html=True)