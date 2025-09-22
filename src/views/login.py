# src/views/login.py
# -*- coding: utf-8 -*-
"""
Vista de login para el sistema de autenticación
"""
import streamlit as st
from src.auth import Authenticator


def view_login():
    """Vista principal de login"""
    st.set_page_config(page_title="🔐 Login - Scouting Hub", layout="centered")
    
    # Instanciar autenticador
    auth = Authenticator()
    
    # Si ya está autenticado, redirigir
    if auth.is_authenticated():
        st.success("✅ Ya estás autenticado")
        if st.button("🏠 Ir a la aplicación"):
            st.switch_page("app.py")
        return
    
    # Layout principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1>🏀 Scouting Hub</h1>
        <h3>Sistema de Análisis de Baloncesto</h3>
        <hr style='margin: 2rem 0;'>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor centrado para el login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Mostrar formulario de login
        auth.show_login_form()
        
        # Información adicional
        with st.expander("ℹ️ Información del Sistema"):
            st.markdown("""
            **Scouting Hub** es un sistema profesional de análisis de baloncesto que te permite:
            
            - 📊 **Análisis de Equipos**: Visualiza estadísticas detalladas
            - 👥 **Perfiles de Jugadores**: Información completa de cada jugador
            - 📈 **Reportes Avanzados**: Genera informes profesionales
            - 🎯 **Scouting Inteligente**: Herramientas de análisis avanzado
            
            ---
            **¿Necesitas acceso?** Contacta con el administrador del sistema.
            """)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 3rem; color: #666;'>
            <small>© 2025 Scouting Hub - Sistema de Análisis de Baloncesto</small>
        </div>
        """, unsafe_allow_html=True)


def show_login_required():
    """Muestra mensaje cuando se requiere login"""
    st.error("🔒 **Acceso Restringido**")
    st.markdown("""
    Para acceder al contenido de **Scouting Hub**, necesitas iniciar sesión.
    
    **¿Qué puedes hacer?**
    - 🔐 Inicia sesión con tu cuenta existente
    - 📞 Contacta al administrador si necesitas una cuenta
    """)
    
    if st.button("🔐 Ir al Login", use_container_width=True):
        st.switch_page("src/views/login.py")


if __name__ == "__main__":
    view_login()