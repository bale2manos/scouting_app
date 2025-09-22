# src/views/admin.py
# -*- coding: utf-8 -*-
"""
Vista de administración para Google Drive y gestión de usuarios
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from ..components import header_bar
from ..data.hybrid_loader import get_drive_status, sync_from_drive, clear_drive_cache
from ..utils import set_route
from ..auth import Authenticator, UserManager, ActivityLogger


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


def view_user_management():
    """Vista de gestión de usuarios para administradores"""
    # Verificar que sea admin
    auth = Authenticator()
    if not auth.require_admin():
        return
    
    # Header con navegación
    _show_admin_header()
    
    st.markdown("# 👥 Gestión de Usuarios")
    
    # Tabs para diferentes funciones
    tab1, tab2, tab3 = st.tabs([
        "📋 Lista de Usuarios", "👤 Historial Individual", "➕ Gestión"
    ])
    
    with tab1:
        _show_users_list()
    
    with tab2:
        _show_user_history()
    
    with tab3:
        _show_user_management()


def _show_admin_header():
    """Muestra el header del panel de administración"""
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        if st.button("🏠 Volver a Home", use_container_width=True):
            set_route("home")
            st.rerun()
    
    with col2:
        st.markdown("<h3 style='text-align:center;margin:0'>👥 Panel de Usuarios</h3>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    st.markdown("---")


def _show_users_list():
    """Muestra la lista completa de usuarios"""
    user_manager = UserManager()
    activity_logger = ActivityLogger()
    
    users = user_manager.list_users()
    
    if not users:
        st.info("👥 No hay usuarios registrados en el sistema.")
        return
    
    # Preparar datos para la tabla
    user_data = []
    for user in users:
        username = user["username"]
        activity = activity_logger.get_user_activity(username)
        user_stats = activity["stats"]
        
        # Calcular última actividad
        last_activity = user_stats.get("last_activity")
        if last_activity:
            try:
                last_activity_date = datetime.fromisoformat(last_activity)
                last_activity_str = last_activity_date.strftime("%Y-%m-%d %H:%M")
            except:
                last_activity_str = "Error en fecha"
        else:
            last_activity_str = "Nunca"
        
        user_data.append({
            "👤 Usuario": user["full_name"],
            "🏷️ Username": username,
            "📝 Rol": user["role"].title(),
            "✅ Estado": "🟢 Activo" if user["is_active"] else "🔴 Inactivo",
            "🔐 Total Sesiones": user_stats.get("total_sessions", 0),
            "📄 Páginas Vistas": sum(user_stats.get("page_views", {}).values()),
            "🎯 Total Acciones": sum(user_stats.get("actions", {}).values()),
            "🕒 Última Actividad": last_activity_str,
            "📅 Último Login": user.get("last_login", "Nunca")[:16] if user.get("last_login") else "Nunca"
        })
    
    df_users = pd.DataFrame(user_data)
    
    # Mostrar tabla con configuración
    st.dataframe(
        df_users,
        use_container_width=True,
        hide_index=True,
        column_config={
            "👤 Usuario": st.column_config.TextColumn("👤 Usuario", width="medium"),
            "🏷️ Username": st.column_config.TextColumn("🏷️ Username", width="small"),
            "📝 Rol": st.column_config.TextColumn("📝 Rol", width="small"),
            "✅ Estado": st.column_config.TextColumn("✅ Estado", width="small"),
            "🔐 Total Sesiones": st.column_config.NumberColumn("🔐 Sesiones", width="small"),
            "📄 Páginas Vistas": st.column_config.NumberColumn("📄 Páginas", width="small"),
            "🎯 Total Acciones": st.column_config.NumberColumn("🎯 Acciones", width="small"),
            "🕒 Última Actividad": st.column_config.TextColumn("🕒 Última Actividad", width="medium"),
            "📅 Último Login": st.column_config.TextColumn("📅 Último Login", width="medium")
        }
    )
    
    # Estadísticas resumen
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(users)
        st.metric("👥 Total Usuarios", total_users)
    
    with col2:
        active_users = sum(1 for u in users if u["is_active"])
        st.metric("🟢 Activos", active_users)
    
    with col3:
        admin_users = sum(1 for u in users if u["role"] == "admin")
        st.metric("👨‍💼 Admins", admin_users)
    
    with col4:
        with_activity = sum(1 for data in user_data if data["🕒 Última Actividad"] != "Nunca")
        st.metric("📊 Con Actividad", with_activity)


def _show_user_history():
    """Muestra el historial detallado de un usuario específico"""
    user_manager = UserManager()
    activity_logger = ActivityLogger()
    
    # Selector de usuario
    users = user_manager.list_users()
    if not users:
        st.info("👥 No hay usuarios para analizar.")
        return
    
    usernames = [user["username"] for user in users]
    selected_user = st.selectbox(
        "👤 Seleccionar usuario para ver historial completo:",
        usernames,
        format_func=lambda x: f"{x} ({next(u['full_name'] for u in users if u['username'] == x)})"
    )
    
    if not selected_user:
        return
    
    # Obtener datos del usuario
    user_data = user_manager.get_user(selected_user)
    activity = activity_logger.get_user_activity(selected_user)
    user_stats = activity["stats"]
    
    if not user_data:
        st.error(f"❌ Usuario '{selected_user}' no encontrado.")
        return
    
    # Información básica del usuario
    st.markdown(f"### 👤 Perfil de {user_data['full_name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏷️ Username", 
            user_data["username"],
            delta=f"Rol: {user_data['role']}"
        )
    
    with col2:
        st.metric(
            "🔐 Total Sesiones", 
            user_stats.get("total_sessions", 0),
            delta=f"Logins: {user_data.get('login_count', 0)}"
        )
    
    with col3:
        total_page_views = sum(user_stats.get("page_views", {}).values())
        st.metric("📄 Páginas Vistas", total_page_views)
    
    with col4:
        total_actions = sum(user_stats.get("actions", {}).values())
        st.metric("🎯 Total Acciones", total_actions)
    
    # Información de fechas
    st.markdown("#### 📅 Información Temporal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        created_at = user_data.get("created_at")
        if created_at:
            created_date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
            st.info(f"📅 **Creado:** {created_date}")
    
    with col2:
        last_login = user_data.get("last_login")
        if last_login:
            login_date = datetime.fromisoformat(last_login).strftime("%Y-%m-%d %H:%M")
            st.info(f"🔐 **Último Login:** {login_date}")
        else:
            st.info("🔐 **Último Login:** Nunca")
    
    with col3:
        last_activity = user_stats.get("last_activity")
        if last_activity:
            activity_date = datetime.fromisoformat(last_activity).strftime("%Y-%m-%d %H:%M")
            st.info(f"📊 **Última Actividad:** {activity_date}")
        else:
            st.info("📊 **Última Actividad:** Nunca")
    
    # Actividad detallada
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Páginas Visitadas")
        page_views = user_stats.get("page_views", {})
        if page_views:
            for page, count in sorted(page_views.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{page}**: {count} visitas")
        else:
            st.info("Sin páginas visitadas")
    
    with col2:
        st.markdown("#### 🎯 Acciones Realizadas")
        actions = user_stats.get("actions", {})
        if actions:
            for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{action}**: {count} veces")
        else:
            st.info("Sin acciones registradas")
    
    # Logs de acceso recientes
    st.markdown("#### 🕒 Historial de Accesos (Últimos 20)")
    recent_logs = activity["recent_access_logs"]
    
    if recent_logs:
        # Preparar datos para mostrar
        logs_data = []
        for log in recent_logs[:20]:
            # Obtener descripción específica si existe
            additional_data = log.get("additional_data", {})
            description = additional_data.get("description", "")
            
            # Usar descripción específica o acción genérica, mejorar presentación
            if description:
                action_display = description
            else:
                # Mejorar la presentación de acciones genéricas
                action = log["action"]
                if action == "view_report":
                    report_name = additional_data.get("report_name", "")
                    report_type = additional_data.get("report_type", "")
                    if report_name and report_type:
                        if report_type == "team_report":
                            action_display = f"Visualizó informe del equipo: {report_name}"
                        elif report_type == "player_report":
                            action_display = f"Visualizó informe del jugador: {report_name}"
                        else:
                            action_display = f"Visualizó {report_type}: {report_name}"
                    else:
                        action_display = "Visualizó informe"
                elif action == "download_report":
                    report_name = additional_data.get("report_name", "")
                    report_type = additional_data.get("report_type", "")
                    if report_name and report_type:
                        if report_type == "team_report":
                            action_display = f"Descargó informe del equipo: {report_name}"
                        elif report_type == "player_report":
                            action_display = f"Descargó informe del jugador: {report_name}"
                        else:
                            action_display = f"Descargó {report_type}: {report_name}"
                    else:
                        action_display = "Descargó informe"
                elif action == "login":
                    action_display = "Inició sesión"
                elif action == "logout":
                    action_display = "Cerró sesión"
                else:
                    action_display = action
            
            # Manejar diferentes formatos de fecha
            try:
                if "T" in log["timestamp"]:
                    timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = log["timestamp"]
            except Exception:
                timestamp = log["timestamp"]
            
            logs_data.append({
                "🕒 Fecha/Hora": timestamp,
                "🎯 Acción": action_display,
                "✅ Éxito": "✅" if log["success"] else "❌",
                "🌐 IP": log.get("ip_address", "N/A"),
                "🖥️ User Agent": log.get("user_agent", "N/A")[:50] + "..." if len(log.get("user_agent", "")) > 50 else log.get("user_agent", "N/A")
            })
        
        df_logs = pd.DataFrame(logs_data)
        st.dataframe(
            df_logs,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📝 No hay logs de acceso para este usuario.")


def _show_user_management():
    """Muestra herramientas de gestión de usuarios"""
    st.markdown("#### 🛠️ Herramientas de Gestión")
    
    user_manager = UserManager()
    
    # Selector de acción
    action = st.selectbox(
        "🎯 Seleccionar acción:",
        ["Seleccionar...", "Desactivar Usuario", "Activar Usuario", "Resetear Contraseña", "Crear Usuario"],
        key="admin_action"
    )
    
    if action == "Seleccionar...":
        st.info("👆 Selecciona una acción para gestionar usuarios.")
        return
    
    users = user_manager.list_users()
    
    if action in ["Desactivar Usuario", "Activar Usuario", "Resetear Contraseña"]:
        if not users:
            st.error("❌ No hay usuarios en el sistema.")
            return
        
        # Filtrar usuarios según la acción
        if action == "Desactivar Usuario":
            available_users = [u for u in users if u["is_active"]]
            if not available_users:
                st.info("ℹ️ No hay usuarios activos para desactivar.")
                return
        elif action == "Activar Usuario":
            available_users = [u for u in users if not u["is_active"]]
            if not available_users:
                st.info("ℹ️ No hay usuarios inactivos para activar.")
                return
        else:
            available_users = users
        
        usernames = [user["username"] for user in available_users]
        selected_user = st.selectbox(
            "👤 Seleccionar usuario:",
            usernames,
            format_func=lambda x: f"{x} ({next(u['full_name'] for u in available_users if u['username'] == x)})"
        )
        
        if selected_user and st.button(f"🎯 {action}", type="primary"):
            if action == "Desactivar Usuario":
                success, message = user_manager.deactivate_user(selected_user)
            elif action == "Activar Usuario":
                success, message = user_manager.activate_user(selected_user)
            elif action == "Resetear Contraseña":
                success, message, new_password = user_manager.reset_password(selected_user)
                if success:
                    st.success(f"✅ {message}")
                    st.code(f"Nueva contraseña: {new_password}", language="text")
                    return
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    elif action == "Crear Usuario":
        with st.form("create_user_form"):
            st.markdown("##### ➕ Crear Nuevo Usuario")
            
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("👤 Username:")
                full_name = st.text_input("📝 Nombre completo:")
            
            with col2:
                email = st.text_input("📧 Email (opcional):")
                role = st.selectbox("🏷️ Rol:", ["user", "admin"])
            
            # Opción de contraseña
            auto_password = st.checkbox("🔐 Generar contraseña automática", value=True)
            manual_password = ""
            
            if not auto_password:
                manual_password = st.text_input("🔑 Contraseña manual:", type="password")
            
            if st.form_submit_button("➕ Crear Usuario", type="primary"):
                if not username or not full_name:
                    st.error("❌ Username y nombre completo son obligatorios.")
                elif not auto_password and len(manual_password) < 6:
                    st.error("❌ La contraseña manual debe tener al menos 6 caracteres.")
                else:
                    if auto_password:
                        password = user_manager.generate_random_password()
                    else:
                        password = manual_password
                    
                    success, message = user_manager.create_user(
                        username=username,
                        password=password,
                        role=role,
                        full_name=full_name,
                        email=email
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        if auto_password:
                            st.code(f"Contraseña generada: {password}", language="text")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")