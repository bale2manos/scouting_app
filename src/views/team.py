# src/views/team.py
# -*- coding: utf-8 -*-
"""
Vista del equipo
"""
import streamlit as st
import base64
from ..components import header_bar
from ..utils import find_image_detailed, set_route
from ..config import TEAM_NAME_DISPLAY, TEAM_LOGO_DIR, TEAM_SLUG


def view_team():
    """Renderiza la vista del equipo simplificada"""
    header_bar()
    
    # Obtener equipo seleccionado de session_state
    selected_team = st.session_state.get('selected_team')
    
    if selected_team:
        team_name = selected_team['name']
        team_slug = selected_team['slug']
    else:
        team_name = TEAM_NAME_DISPLAY
        team_slug = TEAM_SLUG
    
    # Header con título
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem; 
                color: white; text-align: center;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0; 
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{team_name}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Logo como imagen embebida
    logo_tag = """
        <div style="font-size: 4rem; opacity: 0.5;">🏀</div>
        <div style="margin-top: 1rem; opacity: 0.7;">Escudo del equipo</div>
    """
    logo_path, tried = find_image_detailed(TEAM_LOGO_DIR / team_slug)
    if logo_path:
        try:
            mime = "image/png" if logo_path.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            logo_tag = f"<img src='data:{mime};base64,{b64}' alt='logo' style='width: 250px; height: auto; border-radius: 12px;'>"
        except Exception:
            pass
    
    # Layout con columnas
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            {logo_tag}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VER INFORME
        if st.button("📄 VER INFORME", 
                    help="Análisis completo del equipo", 
                    use_container_width=True, 
                    type="primary"):
            set_route("equipo_informe")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VER JUGADORES
        if st.button("👥 VER JUGADORES", 
                    help="Ver jugadores del equipo", 
                    use_container_width=True):
            set_route("players")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón VOLVER A EQUIPOS
        if st.button("🔙 VOLVER A EQUIPOS", 
                    help="Regresar a la lista de equipos", 
                    use_container_width=True):
            set_route("teams")