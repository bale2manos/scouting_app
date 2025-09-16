# src/views/admin.py
# -*- coding: utf-8 -*-
"""
Vista de administración para Google Drive
"""
import streamlit as st
from ..components import header_bar
from ..data import get_drive_status, sync_from_drive, clear_drive_cache
from ..utils import set_route


def view_admin():
    """Vista de administración para Google Drive"""
    header_bar()
    
    st.markdown("## ⚙️ Administración")
    
    # Estado de Google Drive
    st.markdown("### ☁️ Estado de Google Drive")
    
    drive_status = get_drive_status()
    
    # Indicadores de estado
    col1, col2, col3 = st.columns(3)
    
    with col1:
        auth_color = "🟢" if drive_status['authenticated'] else "🔴"
        st.metric(
            "Autenticación", 
            f"{auth_color} {'Conectado' if drive_status['authenticated'] else 'Desconectado'}"
        )
    
    with col2:
        report_color = "🟢" if drive_status['team_report_cached'] else "🟡"
        st.metric(
            "Informe Equipo",
            f"{report_color} {'Descargado' if drive_status['team_report_cached'] else 'No disponible'}"
        )
    
    with col3:
        st.metric(
            "Imágenes Jugadores",
            f"📸 {drive_status['player_images_cached']} descargadas"
        )
    
    # Mostrar errores importantes si los hay
    if drive_status['errors']:
        with st.expander("⚠️ Información adicional"):
            st.warning("Se encontraron algunos problemas menores:")
            for error in drive_status['errors']:
                st.write(f"• {error}")
    
    st.markdown("---")
    
    # Acciones de sincronización
    st.markdown("### 🔄 Sincronización")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Sincronizar datos", use_container_width=True, help="Descargar archivos desde Google Drive"):
            if not drive_status['authenticated']:
                st.error("❌ Google Drive no está autenticado")
            else:
                with st.spinner("Sincronizando desde Google Drive..."):
                    result = sync_from_drive(force_refresh=False)
                    
                    if result['success']:
                        st.success("✅ Sincronización completada")
                    else:
                        st.error("❌ Error en la sincronización")
    
    with col2:
        if st.button("🔄 Forzar actualización", use_container_width=True, help="Forzar descarga completa"):
            if not drive_status['authenticated']:
                st.error("❌ Google Drive no está autenticado")
            else:
                with st.spinner("Descargando todo desde Google Drive..."):
                    result = sync_from_drive(force_refresh=True)
                    
                    if result['success']:
                        st.success("✅ Actualización forzada completada")
                        st.balloons()
                    else:
                        st.error("❌ Error en la actualización")
    
    st.markdown("---")
    
    # Gestión de cache
    st.markdown("### 🗑️ Gestión de Cache")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Cache local:** Archivos descargados desde Google Drive se guardan localmente para acceso rápido.")
    
    with col2:
        if st.button("🗑️ Limpiar cache", use_container_width=True, help="Eliminar archivos descargados"):
            if st.button("✅ Confirmar limpieza", use_container_width=True):
                if clear_drive_cache():
                    st.success("✅ Cache limpiado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al limpiar cache")
    
    st.markdown("---")
    
    # Configuración
    st.markdown("### ⚙️ Configuración")
    
    st.info("La aplicación está configurada para sincronizar automáticamente con Google Drive.")
    
    # Navegación
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 Ver jugadores", use_container_width=True):
            set_route("players")
    
    with col2:
        if st.button("📄 Ver informe equipo", use_container_width=True):
            set_route("equipo_informe")