# app.py
# -*- coding: utf-8 -*-
"""
Aplicación principal Scouting Hub - Versión modularizada con autenticación
"""
import streamlit as st

# Importar sistema de autenticación con Supabase
from src.auth.db_authenticator import DatabaseAuthenticator

# Importar módulos de la aplicación
from src.views import (
    view_home,
    view_team, 
    view_equipo_informe,
    view_jugador_informe,
    view_players,
    view_teams,
    show_loading_screen,
    is_app_ready
)
from src.views.admin import view_user_management
from src.views.videos import view_videos, view_log_videos
from src.utils import set_route
from src.data.drive_loader import auto_sync_on_load, debug_player_files, force_sync


def show_login_page():
    """Muestra la página de login"""
    st.set_page_config(page_title="🔐 Login - Scouting Hub", layout="centered")
    
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
        # Instanciar autenticador con Supabase
        auth = DatabaseAuthenticator()
        
        # Mostrar formulario de login personalizado
        with st.form("login_form"):
            username = st.text_input("👤 Usuario")
            password = st.text_input("🔒 Contraseña", type="password")
            submitted = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
            
            if submitted:
                if username and password:
                    # Mostrar mensaje de carga mientras se autentica
                    with st.spinner("🔍 Verificando credenciales..."):
                        success, user_data, error_reason = auth.authenticate(username, password)
                    
                    if success:
                        user_name = user_data.get('full_name', username) if user_data else username
                        st.success(f"✅ ¡Bienvenido {user_name}! Redirigiendo...")
                        st.rerun()
                    else:
                        # Mostrar mensaje de error específico basado en la razón
                        if error_reason == "user_not_found":
                            st.error("❌ **Usuario no encontrado**")
                            st.info("🔍 Verifica que hayas escrito correctamente tu nombre de usuario.")
                        elif error_reason == "invalid_password":
                            st.error("❌ **Contraseña incorrecta**")
                            st.info("🔑 Asegúrate de escribir tu contraseña correctamente.")
                        elif error_reason == "user_inactive":
                            st.error("❌ **Cuenta desactivada**")
                            st.warning("⚠️ Tu cuenta ha sido desactivada. Contacta al administrador para reactivarla.")
                        elif error_reason == "system_error":
                            st.error("❌ **Error del sistema**")
                            st.warning("⚠️ Problema técnico temporal. Intenta de nuevo en unos momentos.")
                        else:
                            st.error("❌ **Error de acceso**")
                            st.info("🔍 Verifica tus credenciales e intenta nuevamente.")
                        
                        # Mensaje adicional de ayuda
                        st.info("💡 **¿Necesitas ayuda?** Contacta al administrador del sistema.")
                else:
                    st.warning("⚠️ Por favor, completa todos los campos")
        
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


def main():
    """Función principal de la aplicación"""
    # Configurar página antes de cualquier cosa
    st.set_page_config(
        page_title="Scouting Hub", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Instanciar autenticador con Supabase
    auth = DatabaseAuthenticator()
    
    # Verificar autenticación
    if not auth.is_authenticated():
        show_login_page()
        return
    
    # Usuario autenticado - proceder con la aplicación normal
    
    # Mostrar información del usuario en sidebar (DESHABILITADO)
    # auth.show_user_info()
    
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
    
    # Sin logging automático de page views - solo login/logout, informes y descargas

    if route == "home":
        view_home()
    elif route == "teams":
        view_teams()
    elif route == "team":
        view_team()
    elif route == "equipo_informe":
        view_equipo_informe()
    elif route == "players":
        view_players()
    elif route == "jugador_informe":
        view_jugador_informe()
    elif route == "videos":
        view_videos()
    elif route == "log_videos" and auth.get_user_role() in ["admin", "coach"]:
        # Vista de log de videos para admins y coaches
        view_log_videos()
    elif route == "stats" and auth.get_user_role() == "admin":
        # Panel de estadísticas solo para admins
        from src.auth.stats import StatsManager
        stats_manager = StatsManager()
        stats_manager.show_dashboard()
    elif route == "user_management" and auth.get_user_role() == "admin":
        # Panel de gestión de usuarios solo para admins
        view_user_management()
    elif route == "debug":
        # Página temporal de debugging
        st.title("Archivos de Jugadores")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Forzar Sincronización"):
                auth.log_activity(auth.get_current_user(), "force_sync", "debug")
                force_sync()
                st.rerun()
        
        with col2:
            if st.button("📋 Mostrar Debug Info"):
                auth.log_activity(auth.get_current_user(), "debug_info", "debug")
                debug_player_files()
        
        st.markdown("---")
        st.markdown("Para acceder: Agrega `?route=debug` a la URL")
        
    else:
        set_route("home")


if __name__ == "__main__":
    main()
