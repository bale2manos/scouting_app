# src/views/admin.py
# -*- coding: utf-8 -*-
"""
Vista de administración para Google Drive y gestión de usuarios
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Usuarios", "👤 Historial Individual", "🎥 Videos", "➕ Gestión"
    ])
    
    with tab1:
        _show_users_list()
    
    with tab2:
        _show_user_history()
    
    with tab3:
        _show_video_stats()
    
    with tab4:
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


def _show_video_stats():
    """Muestra estadísticas de visualización de videos"""
    st.markdown("### 🎥 Estadísticas de Videos")
    
    with st.spinner("Cargando datos de videos..."):
        try:
            from ..auth.db_logger import DatabaseLogger
            logger = DatabaseLogger()
            
            # Obtener actividad de videos de todos los jugadores
            players_activity = logger.get_all_players_with_video_activity()
            
            # Separar jugadores con y sin actividad
            players_with_videos = {k: v for k, v in players_activity.items() if v['has_watched']}
            players_without_videos = {k: v for k, v in players_activity.items() if not v['has_watched']}
            
            # Crear pestañas para diferentes vistas
            tab_general, tab_detailed = st.tabs(["📊 Resumen", "📋 Detallado"])
            
            with tab_general:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "� Total Jugadores", 
                        len(players_activity),
                        help="Total de jugadores activos en el sistema"
                    )
                
                with col2:
                    st.metric(
                        "✅ Han visto videos", 
                        len(players_with_videos),
                        help="Jugadores que han visto al menos un video"
                    )
                
                with col3:
                    st.metric(
                        "🔴 No han visto videos", 
                        len(players_without_videos),
                        help="Jugadores que nunca han visto videos"
                    )
                
                # Mostrar progreso
                if players_activity:
                    progress = len(players_with_videos) / len(players_activity)
                    st.progress(progress, text=f"Progreso de visualización: {progress:.1%}")
                
                # Mostrar jugadores sin actividad
                if players_without_videos:
                    st.warning("⚠️ **Jugadores que no han visto videos:**")
                    
                    # Mostrar en formato de tabla
                    video_data = []
                    for username, data in players_without_videos.items():
                        video_data.append({
                            "👤 Jugador": data['full_name'],
                            "🏷️ Username": username,
                            "📊 Estado": "🔴 Sin actividad"
                        })
                    
                    if video_data:
                        df_videos = pd.DataFrame(video_data)
                        st.dataframe(
                            df_videos,
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.success("🎉 ¡Todos los jugadores han visto videos!")
                
                # Mostrar top jugadores más activos
                if players_with_videos:
                    st.markdown("#### 🏆 Jugadores Más Activos")
                    
                    # Ordenar por número de visualizaciones
                    sorted_players = sorted(
                        players_with_videos.items(), 
                        key=lambda x: x[1]['view_count'], 
                        reverse=True
                    )[:5]  # Top 5
                    
                    for i, (username, data) in enumerate(sorted_players, 1):
                        col_rank, col_info = st.columns([1, 4])
                        with col_rank:
                            st.markdown(f"**#{i}**")
                        with col_info:
                            last_view = data['last_view'].strftime("%d/%m/%Y") if data['last_view'] else "Nunca"
                            st.markdown(f"**{data['full_name']}** - {data['view_count']} visualizaciones - Último: {last_view}")
            
            with tab_detailed:
                st.markdown("#### 📈 Actividad Detallada por Usuario")
                
                if players_activity:
                    # Crear tabla completa
                    detailed_data = []
                    for username, data in players_activity.items():
                        last_view_str = data['last_view'].strftime("%d/%m/%Y %H:%M") if data['last_view'] else "Nunca"
                        status = "✅ Activo" if data['has_watched'] else "🔴 Sin actividad"
                        
                        detailed_data.append({
                            "👤 Jugador": data['full_name'],
                            "�️ Username": username,
                            "📊 Estado": status,
                            "🎬 Total Visualizaciones": data['view_count'],
                            "📂 Videos Únicos": data['unique_videos'],
                            "🕒 Última Visualización": last_view_str
                        })
                    
                    df_detailed = pd.DataFrame(detailed_data)
                    
                    # Filtros
                    col_filter1, col_filter2 = st.columns(2)
                    with col_filter1:
                        filter_status = st.selectbox(
                            "Filtrar por estado:",
                            ["Todos", "Solo activos", "Solo sin actividad"]
                        )
                    
                    with col_filter2:
                        sort_by = st.selectbox(
                            "Ordenar por:",
                            ["Nombre", "Visualizaciones", "Última actividad"]
                        )
                    
                    # Aplicar filtros
                    filtered_df = df_detailed.copy()
                    
                    if filter_status == "Solo activos":
                        filtered_df = filtered_df[filtered_df["📊 Estado"] == "✅ Activo"]
                    elif filter_status == "Solo sin actividad":
                        filtered_df = filtered_df[filtered_df["📊 Estado"] == "🔴 Sin actividad"]
                    
                    # Aplicar ordenamiento
                    if sort_by == "Visualizaciones":
                        filtered_df = filtered_df.sort_values("🎬 Total Visualizaciones", ascending=False)
                    elif sort_by == "Última actividad":
                        filtered_df = filtered_df.sort_values("🕒 Última Visualización", ascending=False)
                    else:
                        filtered_df = filtered_df.sort_values("👤 Jugador")
                    
                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "👤 Jugador": st.column_config.TextColumn("👤 Jugador", width="medium"),
                            "🏷️ Username": st.column_config.TextColumn("🏷️ Username", width="small"),
                            "📊 Estado": st.column_config.TextColumn("📊 Estado", width="small"),
                            "🎬 Total Visualizaciones": st.column_config.NumberColumn("🎬 Visualizaciones", width="small"),
                            "📂 Videos Únicos": st.column_config.NumberColumn("📂 Videos Únicos", width="small"),
                            "🕒 Última Visualización": st.column_config.TextColumn("🕒 Última Visualización", width="medium")
                        }
                    )
                    
                    # Selector para ver detalles específicos
                    st.markdown("---")
                    st.markdown("#### 🔍 Detalles de Jugador Específico")
                    
                    player_options = {data['full_name']: username for username, data in players_activity.items()}
                    selected_player_name = st.selectbox("Seleccionar jugador:", list(player_options.keys()))
                    selected_username = player_options[selected_player_name]
                    
                    if selected_username:
                        _show_player_video_details_db_only(selected_username, players_activity[selected_username])
                
        except Exception as e:
            st.error(f"❌ Error cargando estadísticas de videos: {e}")
            import traceback
            st.code(traceback.format_exc())


def _show_player_video_details_db_only(username: str, player_data: Dict):
    """Muestra detalles de videos de un jugador usando solo datos de la base de datos"""
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Ha visto videos" if player_data['has_watched'] else "🔴 No ha visto videos"
            st.markdown(f"**Estado:** {status}")
        
        with col2:
            st.markdown(f"**Total Visualizaciones:** {player_data['view_count']}")
        
        with col3:
            st.markdown(f"**Videos Únicos:** {player_data['unique_videos']}")
        
        if player_data['last_view']:
            last_view_str = player_data['last_view'].strftime("%d/%m/%Y %H:%M")
            st.markdown(f"**Última Visualización:** {last_view_str}")
        
        # Mostrar videos vistos
        if player_data['video_names']:
            st.markdown("**📂 Videos Vistos:**")
            for video_name in player_data['video_names']:
                st.markdown(f"- 🎬 {video_name}")
        
        # Mostrar historial detallado
        st.markdown("**📊 Historial Completo:**")
        try:
            from ..auth.database import db_manager
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT additional_data->>'video_name' as video_name,
                           created_at,
                           additional_data->>'video_id' as video_id
                    FROM activity_logs 
                    WHERE username = %s 
                    AND action = 'video_view' 
                    AND log_type = 'video'
                    AND additional_data->>'video_type' = 'user'
                    ORDER BY created_at DESC
                    LIMIT 20
                """, (username,))
                
                views = cursor.fetchall()
                
                if views:
                    for i, view in enumerate(views, 1):
                        video_name = view[0] or "Video sin nombre"
                        view_date = view[1].strftime("%d/%m/%Y %H:%M") if view[1] else "Fecha desconocida"
                        st.markdown(f"{i}. 🎬 **{video_name}** - {view_date}")
                else:
                    st.markdown("- *No hay visualizaciones registradas*")
                    
        except Exception as e:
            st.error(f"Error cargando historial detallado: {e}")
            
    except Exception as e:
        st.error(f"Error mostrando detalles del jugador: {e}")


def _show_player_video_details(username: str, logger):
    """Muestra detalles de videos de un jugador específico"""
    try:
        # Verificar si tiene videos disponibles
        has_videos = logger.user_has_videos_available(username)
        has_watched = logger.has_user_watched_videos(username)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if has_videos:
                st.success("✅ Tiene videos disponibles")
            else:
                st.info("ℹ️ No tiene videos en PINTOBASKET")
        
        with col2:
            if has_watched:
                st.success("✅ Ha visto videos")
            else:
                st.warning("⚠️ No ha visto videos")
        
        if has_videos:
            # Mostrar videos disponibles
            st.markdown("**📂 Videos Disponibles:**")
            try:
                from ..utils.video_manager import video_manager
                user_videos = video_manager.get_user_videos(username)
                
                if user_videos:
                    for video in user_videos:
                        st.markdown(f"- 🎬 {video.get('name', 'Sin nombre')}")
                else:
                    st.markdown("- *No se encontraron videos*")
            except Exception as e:
                st.error(f"Error cargando videos: {e}")
        
        # Mostrar historial de visualizaciones
        st.markdown("**📊 Historial de Visualizaciones:**")
        try:
            from ..auth.database import db_manager
            conn = db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT additional_data->>'video_name' as video_name,
                           created_at,
                           additional_data->>'video_id' as video_id
                    FROM activity_logs 
                    WHERE username = %s 
                    AND action = 'video_view' 
                    AND log_type = 'video'
                    AND additional_data->>'video_type' = 'user'
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (username,))
                
                views = cursor.fetchall()
                
                if views:
                    for view in views:
                        video_name = view[0] or "Video sin nombre"
                        view_date = view[1].strftime("%d/%m/%Y %H:%M") if view[1] else "Fecha desconocida"
                        st.markdown(f"- 🎬 **{video_name}** - {view_date}")
                else:
                    st.markdown("- *No hay visualizaciones registradas*")
                    
        except Exception as e:
            st.error(f"Error cargando historial: {e}")
            
    except Exception as e:
        st.error(f"Error mostrando detalles del jugador: {e}")