# src/views/videos.py
# -*- coding: utf-8 -*-
"""
Vista para reproducción de videos de scouting
(Embed de Google Drive responsivo con aspect-ratio 16:9, sin altura fija)
"""
import re
from typing import Dict, Optional

import streamlit as st
import pandas as pd

from ..components import header_bar
from ..utils import set_route
from ..utils.video_manager import video_manager
from ..auth.db_logger import DatabaseLogger
from ..auth.db_authenticator import DatabaseAuthenticator


# ====================== Helpers (Google Drive) ======================

# Patrones para extraer el ID de Google Drive desde distintas formas de enlace
_DRIVE_RE_FILE = re.compile(r"/file/d/([a-zA-Z0-9_-]{20,})")
_DRIVE_RE_ID = re.compile(r"(?:id=|/d/)([a-zA-Z0-9_-]{20,})")
_DRIVE_RE_SHARE = re.compile(
    r"https?://drive\.google\.com/(?:open\?id=|file/d/|uc\?export=download&id=)([a-zA-Z0-9_-]{20,})"
)

def _drive_embed_url(url_or_id: str) -> Optional[str]:
    """
    Devuelve la URL de preview embebible de Google Drive para iframes:
        https://drive.google.com/file/d/<ID>/preview

    Acepta:
      - ID de archivo
      - Cualquier URL compartida de Drive (open, file/d, uc?export, etc.)
    """
    if not url_or_id:
        return None

    s = str(url_or_id).strip()

    # Si ya es /file/d/<id>/preview, devolver tal cual
    if "drive.google.com" in s and "/file/d/" in s and "/preview" in s:
        return s

    # Intentar extraer ID con distintos patrones
    for regex in (_DRIVE_RE_FILE, _DRIVE_RE_SHARE, _DRIVE_RE_ID):
        m = regex.search(s)
        if m:
            file_id = m.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"

    # Si parece un ID "crudo" (solo el identificador)
    if re.fullmatch(r"[a-zA-Z0-9_-]{20,}", s):
        return f"https://drive.google.com/file/d/{s}/preview"

    return None


def _escape_attr(text: str) -> str:
    return (text or "video").replace('"', "").replace("<", "").replace(">", "")


def _embed_drive_iframe(embed_url: str, title: str = ""):
    """
    Renderiza el iframe de Drive de forma **responsiva** (sin altura fija),
    usando aspect-ratio 16/9 para que ocupe el ancho del contenedor.
    """
    if not embed_url:
        st.error("No hay URL de vídeo")
        return

    html = f"""
    <div style="
        width:100%;
        aspect-ratio:16/9;        /* Altura dinámica en función del ancho */
        background: rgba(0,0,0,.15);
        border-radius: 12px;
        overflow: hidden;
        ">
      <iframe
        src="{embed_url}"
        title="{_escape_attr(title)}"
        style="width:100%; height:100%; border:0; display:block;"
        allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
        allowfullscreen
        loading="lazy"
        referrerpolicy="no-referrer"
      ></iframe>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# =========================== Vistas ===========================

def view_videos():
    """Vista principal de videos de scouting"""
    header_bar()

    # Obtener datos del contexto
    video_context = st.session_state.get('video_context')
    if not video_context:
        st.error("❌ No se especificó qué videos mostrar")
        st.button("← Volver", on_click=lambda: set_route("home"))
        return

    video_type = video_context.get('type')

    if video_type == 'team':
        _show_team_videos(video_context)
    elif video_type == 'team_player':
        _show_team_player_video(video_context)
    elif video_type == 'user':
        _show_user_videos(video_context)
    else:
        st.error("❌ Tipo de video no válido")
        st.button("← Volver", on_click=lambda: set_route("home"))


def _show_team_videos(context: Dict):
    """Muestra videos del equipo rival"""
    team_name = context.get('team_name')
    if not team_name:
        st.error("❌ No se especificó el equipo")
        return

    # Título
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
                color: white; text-align: center;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3);">🎥 Videos - {team_name}</h1>
        <p style="font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.9;">Análisis del equipo rival</p>
    </div>
    """, unsafe_allow_html=True)

    # Botón volver
    if st.button("← Volver al equipo", key="back_to_team"):
        set_route("team")
        st.rerun()

    # Cargar videos del equipo
    with st.spinner("🔍 Cargando videos del equipo..."):
        team_videos = video_manager.get_team_videos(team_name)

    if not team_videos:
        st.info("📽️ No hay videos disponibles para este equipo")
        return

    # Mostrar videos
    st.markdown(f"### 📹 Videos del equipo ({len(team_videos)} videos)")
    for video in team_videos:
        _display_video_card(video)


def _show_team_player_video(context: Dict):
    """Muestra video específico de un jugador rival"""
    team_name = context.get('team_name')
    player_name = context.get('player_name')

    if not team_name or not player_name:
        st.error("❌ No se especificó el equipo o jugador")
        return

    # Título
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
                color: white; text-align: center;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3);">🎥 VIDEO</h1>
        <p style="font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.9;">{team_name}</p>
    </div>
    """, unsafe_allow_html=True)

    # Botón volver
    if st.button("← Volver a jugadores", key="back_to_players"):
        set_route("players")
        st.rerun()

    # Normalizar el player_name recibido
    lookup_name = player_name
    if '.' not in str(player_name):
        parts = str(player_name).replace('-', ' ').split()
        lookup_name = '_'.join(parts).upper()

    # Cargar video del jugador
    with st.spinner("🔍 Cargando video del jugador..."):
        player_video = video_manager.get_player_video(team_name, lookup_name)

    if not player_video:
        st.info(f"📽️ No hay video disponible para {player_name}")
        return

    _display_video_card(player_video)


def _show_user_videos(context: Dict):
    """Muestra videos del usuario actual (PINTOBASKET)"""
    username = context.get('username')
    if not username:
        st.error("❌ No se pudo identificar el usuario")
        return

    # Título
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
                color: white; text-align: center;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0;
                   text-shadow: 0 2px 4px rgba(0,0,0,0.3);">🎥 Mis Videos</h1>
        <p style="font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.9;">Análisis personal - PINTOBASKET</p>
    </div>
    """, unsafe_allow_html=True)

    # Botón volver
    if st.button("← Volver al inicio", key="back_to_home"):
        set_route("home")
        st.rerun()

    # Cargar videos del usuario
    with st.spinner("🔍 Cargando mis videos..."):
        user_videos = video_manager.get_user_videos(username)

    if not user_videos:
        st.info("📽️ No tienes videos disponibles aún")
        st.markdown(f"""
        ### 💡 ¿Cómo conseguir mis videos?

        Los videos de análisis personal se suben en la carpeta **PINTOBASKET** de Google Drive.

        - Contacta con tu entrenador para solicitar videos de tus jugadas  
        - Los videos deben nombrarse como: `{username}.mp4` o `{username}.mov`  
        - Una vez subidos, aparecerán automáticamente aquí
        """)
        return

    # Separar personales y compartidos
    personal_videos = [v for v in user_videos if not v.get('shared')]
    shared_videos = [v for v in user_videos if v.get('shared')]

    if personal_videos:
        st.markdown(f"### 📹 Mis videos de análisis ({len(personal_videos)} videos)")
        for video in personal_videos:
            _display_video_card(video)

    if shared_videos:
        st.markdown(f"### 📢 Videos del equipo ({len(shared_videos)} vídeo(s))")
        for video in shared_videos:
            _display_video_card(video)

    if not personal_videos and not shared_videos:
        st.info("📽️ No tienes videos disponibles aún")


def _display_video_card(video: Dict):
    """Muestra una tarjeta con el video (Drive -> iframe responsivo)"""
    title = video.get('pretty_name') or video.get('name') or "Vídeo"
    raw_url = video.get('embed_url') or video.get('url') or video.get('id')
    embed_url = _drive_embed_url(raw_url)

    # Título del video
    st.markdown(f"#### 🎬 {title}")

    # Mostrar el video embebido
    if embed_url:
        _embed_drive_iframe(embed_url, title=title)
    else:
        # Fallback: si no es Drive o no se pudo normalizar, usar HTML5 video si es directo
        url = (raw_url or "").strip()
        if url.lower().endswith((".mp4", ".webm", ".m3u8")):
            st.video(url)
        else:
            st.warning("No se pudo embeber el vídeo. Abre el enlace externo:")
            if video.get('url'):
                st.markdown(f"- 🔗 [Abrir en Google Drive]({video['url']})")
            elif raw_url:
                st.markdown(f"- 🔗 [Abrir enlace]({raw_url})")

    # Separador
    st.markdown("---")


# =================== Permisos y vistas de Log ===================

def _user_can_view_video(video: Dict, current_user: Dict) -> bool:
    """Verifica si el usuario actual puede ver el video"""
    user_role = current_user.get('role', 'player')
    username = current_user.get('username', '')

    # Admins y coaches pueden ver todo
    if user_role in ['admin', 'coach']:
        return True

    # Players pueden ver:
    # 1. Sus propios videos de PINTOBASKET
    # 2. Videos de equipos rivales
    # 3. Videos de jugadores rivales
    video_type = video.get('type')

    if video_type == 'user':
        return video.get('username') == username
    elif video_type in ['team', 'team_player']:
        return True

    return False


def view_log_videos():
    """Vista de log de videos para administradores y entrenadores"""
    header_bar()

    st.markdown("# 📊 Log de Videos - Estado de Jugadores")

    # Verificar permisos
    auth = DatabaseAuthenticator()
    current_user = auth.get_current_user()
    if not current_user or current_user.get('role') not in ['admin', 'coach']:
        st.error("❌ No tienes permisos para acceder a esta vista")
        if st.button("← Volver", width="stretch"):
            set_route("home")
        return

    with st.spinner("Cargando estado de videos de jugadores..."):
        try:
            # Obtener actividad de videos de todos los jugadores
            logger = DatabaseLogger()
            players_activity = logger.get_all_players_with_video_activity()

            if not players_activity:
                st.warning("No se encontraron jugadores en el sistema")
                if st.button("← Volver", width="stretch"):
                    set_route("home")
                return

            # Separar jugadores por estado
            players_with_videos = {k: v for k, v in players_activity.items() if v['has_watched']}
            players_without_videos = {k: v for k, v in players_activity.items() if not v['has_watched']}

            # Mostrar métricas principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("👥 Total Jugadores", len(players_activity))

            with col2:
                st.metric("✅ Han visto videos", len(players_with_videos))

            with col3:
                st.metric("🔴 No han visto", len(players_without_videos))

            with col4:
                if players_activity:
                    percentage = (len(players_with_videos) / len(players_activity)) * 100
                    st.metric("📈 % Completado", f"{percentage:.0f}%")

            # Pestañas para diferentes vistas
            tab1, tab2, tab3 = st.tabs(["🔴 Sin Videos", "✅ Con Videos", "📋 Vista Completa"])

            # --------- Tab 1: Sin videos ----------
            with tab1:
                st.markdown("### 🔴 Jugadores que NO han visto videos")

                if players_without_videos:
                    for username, data in players_without_videos.items():
                        with st.container():
                            col_player, col_action = st.columns([3, 1])

                            with col_player:
                                st.markdown(f"**👤 {data['full_name']}** (`{username}`)")
                                st.markdown("📊 Estado: 🔴 Sin actividad de videos")

                            with col_action:
                                if st.button("👁️ Ver", key=f"check_{username}", help="Ver qué videos tiene disponibles"):
                                    _show_player_video_availability(username, data['full_name'])

                            st.markdown("---")
                else:
                    st.success("🎉 ¡Todos los jugadores han visto videos!")

            # --------- Tab 2: Con videos ----------
            with tab2:
                st.markdown("### ✅ Jugadores que SÍ han visto videos")

                if players_with_videos:
                    # Ordenar por número de visualizaciones
                    sorted_players = sorted(
                        players_with_videos.items(),
                        key=lambda x: x[1]['view_count'],
                        reverse=True
                    )

                    for username, data in sorted_players:
                        with st.container():
                            col_player, col_stats, col_action = st.columns([2, 2, 1])

                            with col_player:
                                st.markdown(f"**👤 {data['full_name']}** (`{username}`)")
                                if data['last_view']:
                                    last_view_str = data['last_view'].strftime("%d/%m/%Y %H:%M")
                                    st.markdown(f"🕒 Última visualización: {last_view_str}")

                            with col_stats:
                                st.markdown(f"🎬 **{data['view_count']}** visualizaciones")
                                st.markdown(f"📂 **{data['unique_videos']}** videos únicos")
                                if data['video_names']:
                                    videos_text = ", ".join(data['video_names'][:2])
                                    if len(data['video_names']) > 2:
                                        videos_text += f" +{len(data['video_names']) - 2} más"
                                    st.markdown(f"📋 Videos: {videos_text}")

                            with col_action:
                                if st.button("📊 Detalles", key=f"details_{username}", help="Ver historial completo"):
                                    _show_player_video_history(username, data)

                            st.markdown("---")
                else:
                    st.info("Ningún jugador ha visto videos aún")

            # --------- Tab 3: Vista completa ----------
            with tab3:
                st.markdown("### 📋 Vista Completa de Todos los Jugadores")

                # Crear tabla completa
                table_data = []
                for username, data in players_activity.items():
                    status_emoji = "✅" if data['has_watched'] else "🔴"
                    status_text = "Ha visto videos" if data['has_watched'] else "No ha visto"
                    last_view_str = data['last_view'].strftime("%d/%m/%Y") if data['last_view'] else "Nunca"

                    table_data.append({
                        "👤 Jugador": data['full_name'],
                        "🏷️ Username": username,
                        "📊 Estado": f"{status_emoji} {status_text}",
                        "🎬 Visualizaciones": data['view_count'],
                        "📂 Videos Únicos": data['unique_videos'],
                        "🕒 Última Vista": last_view_str
                    })

                df = pd.DataFrame(table_data)

                # Filtros
                col_filter1, col_filter2 = st.columns(2)
                with col_filter1:
                    filter_option = st.selectbox(
                        "Filtrar por estado:",
                        ["Todos", "Solo sin videos", "Solo con videos"]
                    )

                with col_filter2:
                    sort_option = st.selectbox(
                        "Ordenar por:",
                        ["Nombre", "Estado", "Visualizaciones", "Última vista"]
                    )

                # Aplicar filtros
                filtered_df = df.copy()

                if filter_option == "Solo sin videos":
                    filtered_df = filtered_df[filtered_df["📊 Estado"].str.contains("🔴")]
                elif filter_option == "Solo con videos":
                    filtered_df = filtered_df[filtered_df["📊 Estado"].str.contains("✅")]

                # Aplicar ordenamiento
                if sort_option == "Estado":
                    filtered_df = filtered_df.sort_values("📊 Estado")
                elif sort_option == "Visualizaciones":
                    filtered_df = filtered_df.sort_values("🎬 Visualizaciones", ascending=False)
                elif sort_option == "Última vista":
                    # Como es texto dd/mm/yyyy, el orden será lexicográfico; para exactitud habría que parsear.
                    filtered_df = filtered_df.sort_values("🕒 Última Vista", ascending=False)
                else:
                    filtered_df = filtered_df.sort_values("👤 Jugador")

                # Mostrar tabla
                st.dataframe(
                    filtered_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "👤 Jugador": st.column_config.TextColumn("👤 Jugador", width="medium"),
                        "🏷️ Username": st.column_config.TextColumn("🏷️ Username", width="small"),
                        "📊 Estado": st.column_config.TextColumn("📊 Estado", width="medium"),
                        "🎬 Visualizaciones": st.column_config.NumberColumn("🎬 Vistas", width="small"),
                        "📂 Videos Únicos": st.column_config.NumberColumn("📂 Únicos", width="small"),
                        "🕒 Última Vista": st.column_config.TextColumn("🕒 Última Vista", width="medium"),
                    }
                )

            # Botón de volver
            st.markdown("---")
            if st.button("← Volver al Inicio", width="stretch"):
                set_route("home")

        except Exception as e:
            st.error(f"❌ Error cargando datos de videos: {e}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
            if st.button("← Volver", width="stretch"):
                set_route("home")


# ========== Auxiliares para disponibilidad e historial ==========
def _show_player_video_availability(username: str, full_name: str):
    """Muestra información sobre videos disponibles para un jugador"""
    with st.expander(f"📂 Videos disponibles para {full_name}"):
        try:
            videos = video_manager.get_user_videos(username)

            if not videos:
                st.info("🎥 No hay videos disponibles para este jugador.")
                return

            for i, video in enumerate(videos):
                title = video.get('pretty_name') or video.get('name') or f"Vídeo {i+1}"
                st.markdown(f"**{title}**")

                embed_url = _drive_embed_url(video.get('embed_url') or video.get('url') or video.get('id'))
                if embed_url:
                    _embed_drive_iframe(embed_url, title=title)
                else:
                    url = (video.get('url') or "").strip()
                    if url.lower().endswith((".mp4", ".webm", ".m3u8")):
                        st.video(url)
                    elif url:
                        st.markdown(f"- 🔗 [Abrir enlace]({url})")

        except Exception as e:
            st.error(f"❌ Error cargando videos: {e}")


def _show_player_video_history(username: str, player_data: Dict):
    """Muestra el historial detallado de visualizaciones de un jugador"""
    with st.expander(f"📊 Historial completo de {player_data['full_name']}"):
        try:
            # Obtener historial detallado de la base de datos
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
                """, (username,))

                views = cursor.fetchall()

                if views:
                    st.markdown(f"**Total de visualizaciones: {len(views)}**")

                    for i, view in enumerate(views, 1):
                        video_name = view[0] or "Video sin nombre"
                        view_date = view[1].strftime("%d/%m/%Y %H:%M") if view[1] else "Fecha desconocida"
                        st.markdown(f"{i}. 🎬 **{video_name}** — {view_date}")
                else:
                    st.warning("No se encontraron visualizaciones registradas")

        except Exception as e:
            st.error(f"Error cargando historial: {e}")
