# src/views/teams.py
# -*- coding: utf-8 -*-
"""
Vista de lista de equipos (tarjetas HTML estables: fondo blanco, altura uniforme)
"""
import base64
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import streamlit.components.v1 as components

from ..components import header_bar
from ..utils import find_image_detailed, set_route
from ..utils.google_drive import get_drive_client
from ..config import (
    TEAM_NAME_DISPLAY,
    TEAM_LOGO_DIR,
    GOOGLE_DRIVE_ROOT_FOLDER_ID,
    NEXT_MATCH_DATE,
    LEAGUE_POSITION,
    WINS_LOSSES,
)


# ---------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------
def get_all_teams() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de todos los equipos disponibles desde Google Drive.
    Returns: lista de diccionarios con información de equipos
    """
    try:
        drive_client = get_drive_client()
        if not drive_client or not drive_client.is_authenticated():
            return []

        folders = drive_client.list_folders_in_folder(GOOGLE_DRIVE_ROOT_FOLDER_ID)
        teams: List[Dict[str, Any]] = []
        for folder in folders:
            team_name = folder["name"]
            team_slug = team_name.lower().replace(" ", "_")
            teams.append({"name": team_name, "slug": team_slug, "drive_id": folder["id"]})

        teams.sort(key=lambda x: x["name"])
        return teams
    except Exception as e:
        st.error(f"Error al cargar equipos: {e}")
        return []


def _logo_b64(team_slug: str) -> str:
    """
    Devuelve un <img> con el logo en base64 (tamaño fijo), o fallback de igual tamaño.
    """
    logo_path, _ = find_image_detailed(TEAM_LOGO_DIR / team_slug)
    if logo_path and Path(logo_path).exists():
        try:
            mime = "image/png" if logo_path.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(Path(logo_path).read_bytes()).decode("utf-8")
            return f'<img class="team-card__logo" src="data:{mime};base64,{b64}" alt="logo" />'
        except Exception:
            pass
    # Fallback con mismo “caja” que la imagen para no romper alturas
    return (
        '<div class="team-card__logo-fallback" aria-label="logo">'
        '🏀'
        "</div>"
    )


def _render_team_card_html(team: Dict[str, Any], is_next_rival: bool = False) -> str:
    """
    HTML de la tarjeta sin botones - los botones irán debajo usando Streamlit.
    """
    logo_html = _logo_b64(team["slug"])
    badge_html = (
        '<div class="team-card__badge">📅 Próximo Rival</div>' if is_next_rival else ""
    )
    title = team["name"]
    title_html = f'<h4 class="team-card__title">{"🏆 " + title if is_next_rival else title}</h4>'

    meta_html = ""
    if is_next_rival:
        meta_html = (
            f'<div class="team-card__meta">📅 {NEXT_MATCH_DATE}</div>'
            f'<div class="team-card__meta">📊 {LEAGUE_POSITION} &nbsp;|&nbsp; 🏆 {WINS_LOSSES}</div>'
        )

    return f"""
    <article class="team-card">
        {badge_html}
        <div class="team-card__main">
            {logo_html}
            {title_html}
            {meta_html}
        </div>
    </article>
    """


def _build_grid_html(teams: List[Dict[str, Any]], cards_per_row: int = 3) -> str:
    """
    Construye el bloque HTML completo (grid + tarjetas) para inyectar en components.html.
    """
    cards = []
    for team in teams:
        is_next_rival = (team["name"].upper() == TEAM_NAME_DISPLAY.upper())
        cards.append(_render_team_card_html(team, is_next_rival))

    # --- Estilos aislados en un scope para evitar interferencias ---
    # Altura fija (no min-height), flex centrado, logos con caja fija.
    # Grid responsivo sin reflows.
    style = """
    <style>
      /* Scope para evitar que otros estilos del app afecten */
      #teams-scope {
        --card-height: 200px;
        --gap: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      }

      /* Asegurar que todos los elementos hereden la fuente */
      #teams-scope * {
        font-family: inherit;
      }

      #teams-scope .teams-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--gap);
      }

      @media (max-width: 1100px) {
        #teams-scope .teams-grid { grid-template-columns: repeat(2, 1fr); }
      }
      @media (max-width: 700px) {
        #teams-scope .teams-grid { grid-template-columns: 1fr; }
      }

      /* Tarjeta base */
      #teams-scope .team-card {
        background: #ffffff;              /* FONDO BLANCO SIEMPRE */
        border: 1px solid #e5e7eb;       /* gris suave */
        border-radius: 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,.08);
        padding: 16px;
        height: var(--card-height);      /* ALTURA UNIFORME y FIJA */
        display: flex;
        flex-direction: column;
        justify-content: center;         /* centrar contenido */
        overflow: hidden;                /* por si hubiera textos largos */
      }

      /* Badge Próximo Rival */
      #teams-scope .team-card__badge {
        align-self: flex-start;
        background: #ef4444;
        color: #fff;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 6px;
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.35);
      }

      /* Zona central (logo + textos) centrada */
      #teams-scope .team-card__main {
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 6px;
        padding: 4px 0;
      }

      /* Logo: caja fija, no cambia alturas cuando carga */
      #teams-scope .team-card__logo,
      #teams-scope .team-card__logo-fallback {
        width: 56px;
        height: 56px;
        display: block;
      }
      #teams-scope .team-card__logo {
        object-fit: contain;
      }
      #teams-scope .team-card__logo-fallback {
        font-size: 44px;                 /* ajustado para encajar en 56x56 */
        line-height: 56px;
      }

      /* Título SIEMPRE NEGRO */
      #teams-scope .team-card__title {
        color: #111111;
        margin: 8px 0 2px;
        font-size: 1rem;
        font-weight: 700;
      }

      /* Metadatos en gris */
      #teams-scope .team-card__meta {
        color: #6b7280;
        font-size: 0.9rem;
      }
    </style>
    """

    grid = f"""
    <div id="teams-scope">
      <div class="teams-grid">
        {''.join(cards)}
      </div>
    </div>
    """
    return style + grid


# ---------------------------------------------------------------------
# Vista principal
# ---------------------------------------------------------------------
def view_teams():
    """
    Renderiza la vista de lista de equipos con tarjetas HTML pequeñas y botones debajo de cada una.
    """
    # 1) Header
    header_bar()

    # 2) Cargar equipos
    teams = get_all_teams()
    if not teams:
        st.warning("No se pudieron cargar los equipos. Verifica la conexión con Google Drive.")
        return

    # 3) Crear estructura de tarjetas + botones en cuadrícula
    cols_per_row = 3
    for i in range(0, len(teams), cols_per_row):
        row_teams = teams[i:i + cols_per_row]
        cols = st.columns(len(row_teams))
        
        for j, team in enumerate(row_teams):
            with cols[j]:
                # Renderizar tarjeta HTML individual
                is_next_rival = (team["name"].upper() == TEAM_NAME_DISPLAY.upper())
                card_html = _render_team_card_html(team, is_next_rival)
                
                # Estilos solo para esta tarjeta
                card_style = """
                <style>
                  .single-card-scope {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                  }
                  .single-card-scope .team-card {
                    background: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 16px;
                    box-shadow: 0 6px 16px rgba(0,0,0,.08);
                    padding: 16px;
                    height: 200px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    overflow: hidden;
                    margin-bottom: 10px;
                  }
                  .single-card-scope .team-card__badge {
                    align-self: flex-start;
                    background: #ef4444;
                    color: #fff;
                    padding: 4px 12px;
                    border-radius: 14px;
                    font-size: 11px;
                    font-weight: 700;
                    margin-bottom: 6px;
                    box-shadow: 0 2px 6px rgba(239, 68, 68, 0.35);
                  }
                  .single-card-scope .team-card__main {
                    flex: 1 1 auto;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    gap: 6px;
                    padding: 4px 0;
                  }
                  .single-card-scope .team-card__logo,
                  .single-card-scope .team-card__logo-fallback {
                    width: 56px;
                    height: 56px;
                    display: block;
                  }
                  .single-card-scope .team-card__logo {
                    object-fit: contain;
                  }
                  .single-card-scope .team-card__logo-fallback {
                    font-size: 44px;
                    line-height: 56px;
                  }
                  .single-card-scope .team-card__title {
                    color: #111111;
                    margin: 8px 0 2px;
                    font-size: 1rem;
                    font-weight: 700;
                  }
                  .single-card-scope .team-card__meta {
                    color: #6b7280;
                    font-size: 0.8rem;
                  }
                </style>
                """
                
                # Mostrar tarjeta individual
                full_card_html = card_style + f'<div class="single-card-scope">{card_html}</div>'
                st.components.v1.html(full_card_html, height=220)
                
                # Botones inmediatamente debajo de esta tarjeta
                col_informe, col_jugadores = st.columns(2)
                with col_informe:
                    if st.button("📄 Informe", key=f"informe_{team['slug']}", use_container_width=True, type="primary"):
                        st.session_state["selected_team"] = team
                        set_route("team")
                        st.rerun()
                
                with col_jugadores:
                    if st.button("👥 Jugadores", key=f"jugadores_{team['slug']}", use_container_width=True):
                        st.session_state["selected_team"] = team
                        set_route("players")
                        st.rerun()

    # 4) Pie
    st.markdown("---")
    st.markdown(f"**Total de equipos:** {len(teams)}")
