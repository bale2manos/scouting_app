# src/views/loading.py
# -*- coding: utf-8 -*-
"""
Vista de carga profesional y minimalista
"""
import streamlit as st


def show_loading_screen():
    """Pantalla de carga profesional y minimalista"""
    
    # Versión simplificada y robusta
    st.markdown("# 🏀 SCOUTING HUB")
    st.markdown("---")
    
    # Contenedor centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="
                width: 60px;
                height: 60px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #1f77b4;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 2rem auto;
            "></div>
            <h3 style="color: #1f77b4;">Preparando tu experiencia de scouting</h3>
            <p style="color: #666;">Cargando datos desde Google Drive...</p>
        </div>
        
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Barra de progreso visual (más rápida)
    progress_bar = st.progress(0)
    import time
    for i in range(20):  # Reducido de 100 a 20 para ser más rápido
        time.sleep(0.02)  # 0.4 segundos total
        progress_bar.progress((i + 1) * 5)


def show_loading_screen_advanced():
    """Pantalla de carga avanzada (solo si el HTML funciona bien)"""
    
    # Crear contenedor principal centrado
    st.markdown("""
    <style>
    .loading-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .loading-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 3rem;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    .loading-title {
        font-size: 3rem;
        margin-bottom: 1rem;
        font-weight: 300;
        letter-spacing: 2px;
        margin-top: 0;
    }
    
    .loading-spinner {
        width: 60px;
        height: 60px;
        border: 3px solid rgba(255,255,255,0.3);
        border-top: 3px solid #ffffff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
    }
    
    .loading-text {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
        font-weight: 300;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Ocultar elementos de Streamlit */
    .stApp > header {visibility: hidden;}
    .stApp > .main > div > div > div > section > div {padding-top: 0rem;}
    </style>
    """, unsafe_allow_html=True)
    
    # Mostrar la pantalla de carga
    st.markdown("""
    <div class="loading-container">
        <div class="loading-card">
            <h1 class="loading-title">🏀 SCOUTING HUB</h1>
            <div class="loading-spinner"></div>
            <p class="loading-text">Preparando tu experiencia de scouting</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def is_app_ready():
    """Verifica si la app está lista para mostrar contenido"""
    return st.session_state.get('drive_synced', False)