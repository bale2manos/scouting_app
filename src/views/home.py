# src/views/home.py
# -*- coding: utf-8 -*-
"""
Vista principal/home de la aplicación
"""
import streamlit as st
import base64
from ..components import header_bar
from ..utils import find_image_detailed, set_route
from ..config import (
    TEAM_NAME_DISPLAY, 
    TEAM_LOGO_DIR, 
    TEAM_SLUG,
    NEXT_MATCH_DATE,
    LEAGUE_POSITION,
    WINS_LOSSES
)


def view_home():
    """Renderiza la vista principal con TODO dentro de la caja azul."""
    header_bar()

    # --- redirección por query param (?go=team / ?go=players) ---
    go = st.query_params.get("go")
    if isinstance(go, list):
        go = go[0] if go else None
    if go in ("team", "players"):
        # Limpieza rápida visual: cambiamos la ruta y rerun
        set_route(go)
        return

    # ------- estilos -------
    st.markdown("""
    <style>
      .hero-section {
        text-align:center; padding: 2rem 1rem 1.5rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 16px; margin: 1rem 0 2rem; color: #fff;
      }
      .hero-title { font-size: 2.2rem; font-weight: 800; margin: .25rem 0 1rem; text-shadow: 0 2px 4px rgba(0,0,0,.25); }
      .hero-sub   { font-size: 1.05rem; opacity:.9; }
      .match-info {
        background: rgba(255,255,255,.12); padding: .9rem 1rem; border-radius: 12px;
        margin: 1rem auto 1.25rem; max-width: 460px; backdrop-filter: blur(8px);
      }
      .match-date { font-size: 1.6rem; font-weight: 700; margin-bottom: .35rem; }
      .team-stats { display:flex; gap:1.4rem; justify-content:center; opacity:.9; font-size:.95rem; }

      /* grid interior: logo a la izq, info a la dcha */
      .hero-grid {
        display:grid; grid-template-columns: 280px 1fr; gap: 25px; align-items:center;
        max-width: 1050px; margin: 0 auto;
      }
      .hero-logo { display:flex; align-items:center; justify-content:center; }
      .hero-logo img { width: 250px; height:auto; display:block; filter: drop-shadow(0 6px 14px rgba(0,0,0,.25)); }
      .hero-actions { 
        display:grid; grid-template-columns: 1fr 1fr; gap:15px; 
        max-width: 800px; margin: 0 auto; 
      }
      .cta {
        display:block; text-align:center; padding: 1rem 1.2rem; border-radius: 10px;
        font-weight: 700; border: 1px solid rgba(255,255,255,.25);
        text-decoration:none; color:#000; backdrop-filter: blur(4px);
      }
      .cta.primary   { background:#ef4444; color:#fff; }          /* rojo informe con texto blanco */
      .cta.secondary { background:rgba(255,255,255,.9); color:#000; }  /* fondo blanco con texto negro */
      .cta:hover { filter: brightness(1.05); transform: translateY(-1px); transition:.15s; }

      @media (max-width: 820px) {
        .hero-grid { grid-template-columns: 1fr; gap: 16px; }
        .hero-logo img { width: 200px; }
        .hero-actions { grid-template-columns: 1fr; }
      }
    </style>
    """, unsafe_allow_html=True)

    # ------- logo como <img> embebido dentro de la caja -------
    logo_tag = """
      <div style="font-size:120px;line-height:1">🏀</div>
      <div style="opacity:.85;font-size:1rem;margin-top:.5rem">Escudo del equipo</div>
    """
    logo_path, _ = find_image_detailed(TEAM_LOGO_DIR / TEAM_SLUG)
    if logo_path:
        try:
            mime = "image/png" if logo_path.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            logo_tag = f"<img src='data:{mime};base64,{b64}' alt='logo'>"
        except Exception:
            pass

    # ------- caja azul completa reorganizada según el diseño -------
    st.markdown(f"""
    <div class="hero-section">
      <div class="hero-grid">
        <div class="hero-logo">{logo_tag}</div>
        <div style="text-align: center;">
          <div class="hero-sub">Próximo rival</div>
          <div class="hero-title">{TEAM_NAME_DISPLAY}</div>
          <div class="match-info">
            <div class="match-date">📅 {NEXT_MATCH_DATE}</div>
            <div class="team-stats">
              <span>📊 Posición: {LEAGUE_POSITION}</span>
              <span>🏆 Balance: {WINS_LOSSES}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="hero-actions" style="margin-top: 1.5rem;">
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones de navegación usando Streamlit pero estilizados para que parezcan parte de la caja
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.25);
        backdrop-filter: blur(4px);
        transition: all 0.15s;
        height: 3rem;
        font-size: 1rem;
    }
    .stButton > button:hover {
        filter: brightness(1.05);
        transform: translateY(-1px);
    }
    .nav-buttons {
        margin-top: -1rem;
        padding: 0 1rem 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor para los botones que simule estar dentro de la caja azul
    st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Ver Informe del Equipo", use_container_width=True, type="primary"):
            set_route("team")
    
    with col2:
        if st.button("👥 Ver Jugadores", use_container_width=True):
            set_route("players")
    
    st.markdown('</div>', unsafe_allow_html=True)