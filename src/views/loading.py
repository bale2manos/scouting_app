# src/views/loading.py
# -*- coding: utf-8 -*-
"""
Vista de carga genérica para mostrar mientras se cargan los datos
"""
import streamlit as st
import time


def view_loading():
    """Vista de carga genérica para mostrar durante la sincronización"""
    st.markdown("""
    <style>
    .loading-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 70vh;
        text-align: center;
    }
    .loading-title {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .loading-subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .loading-spinner {
        width: 60px;
        height: 60px;
        border: 6px solid #f3f3f3;
        border-top: 6px solid #1f77b4;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 2rem auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-dots::after {
        content: '';
        animation: dots 1.5s steps(5, end) infinite;
    }
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="loading-container">
        <div class="loading-title">🏀 Scouting Hub</div>
        <div class="loading-subtitle">Preparando tu experiencia de scouting</div>
        <div class="loading-spinner"></div>
        <div class="loading-subtitle">
            <span class="loading-dots">Cargando datos</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Placeholder para información adicional
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center;">
        <h4>🔄 Sincronizando con Google Drive</h4>
        <p style="margin: 0; color: #666;">
        Descargando informes y datos de jugadores...
        </p>
        </div>
        """, unsafe_allow_html=True)


def view_loading_with_progress(message: str = "Cargando...", show_spinner: bool = True):
    """
    Vista de carga con mensaje personalizable
    
    Args:
        message: Mensaje a mostrar durante la carga
        show_spinner: Si mostrar el spinner de Streamlit
    """
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh;">
        <h2 style="color: #1f77b4; margin-bottom: 2rem;">🏀 Scouting Hub</h2>
        <div style="font-size: 1.2rem; color: #666; margin-bottom: 1rem;">""" + message + """</div>
    </div>
    """, unsafe_allow_html=True)
    
    if show_spinner:
        with st.spinner(""):
            time.sleep(0.1)  # Pequeña pausa para mostrar el spinner


def view_error_loading(error_message: str = "Error al cargar los datos"):
    """
    Vista de error durante la carga
    
    Args:
        error_message: Mensaje de error a mostrar
    """
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; text-align: center;">
        <h2 style="color: #1f77b4; margin-bottom: 2rem;">🏀 Scouting Hub</h2>
        <div style="font-size: 1.5rem; color: #e74c3c; margin-bottom: 1rem;">⚠️ """ + error_message + """</div>
        <div style="color: #666; margin-bottom: 2rem;">
            Por favor, verifica tu conexión e intenta nuevamente.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Reintentar", use_container_width=True):
            st.rerun()