# src/data/loader.py
# -*- coding: utf-8 -*-
"""
Módulo para carga dinámica de datos de jugadores
"""
from typing import Dict, Any, List
import streamlit as st
import pandas as pd

from ..config import (
    EXCEL_FILE, 
    TEAM_NAME_DISPLAY, 
    PLAYER_PHOTOS_DIR, 
    PLAYER_NAME_MAPPING,
    FALLBACK_PLAYERS
)


def _validate_image_url(url):
    """Valida si una URL de imagen es válida y confiable"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url.startswith('http'):
        return False
    
    # Filtrar URLs problemáticas conocidas
    problematic_domains = [
        'imagenes.feb.es',  # URLs dinámicas que no siempre funcionan
        'Foto.aspx',        # Archivos ASP.NET que pueden fallar
    ]
    
    for domain in problematic_domains:
        if domain in url:
            return False
    
    # Solo permitir URLs de imágenes estáticas confiables
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    if not any(url.lower().endswith(ext) for ext in valid_extensions):
        return False
    
    return True


@st.cache_data
def load_players_dynamically() -> List[Dict[str, Any]]:
    """Carga jugadores dinámicamente desde PNG y Excel con lógica mejorada"""
    players = []
    
    try:
        # Leer Excel
        if not EXCEL_FILE.exists():
            st.error(f"No se encontró el archivo Excel: {EXCEL_FILE}")
            return FALLBACK_PLAYERS
        
        df = pd.read_excel(EXCEL_FILE)
        team_df = df[df['EQUIPO'].str.contains(TEAM_NAME_DISPLAY, case=False, na=False)]
        
        # Obtener archivos PNG disponibles
        png_files = []
        if PLAYER_PHOTOS_DIR.exists():
            png_files = [f.stem for f in PLAYER_PHOTOS_DIR.glob("*.png")]
        
        # Para cada PNG, intentar encontrar el jugador correspondiente en Excel
        for png_file in png_files:
            player_found = False
            
            # Primero intentar con mapping manual (casos exactos conocidos)
            if png_file in PLAYER_NAME_MAPPING:
                expected_name, fallback_number = PLAYER_NAME_MAPPING[png_file]
                
                # Buscar coincidencia exacta
                exact_match = team_df[team_df['JUGADOR'] == expected_name]
                if not exact_match.empty:
                    row = exact_match.iloc[0]
                    player = _create_player_from_excel_row(row, png_file)
                    players.append(player)
                    player_found = True
            
            # Si no se encontró con mapping, buscar por similitud de nombres
            if not player_found:
                # Extraer componentes del nombre del archivo PNG
                name_parts = png_file.replace('_', ' ').split()
                
                # Buscar jugadores que contengan estas partes del nombre
                best_match = None
                best_score = 0
                
                for idx, row in team_df.iterrows():
                    excel_name = row['JUGADOR'].upper()
                    score = 0
                    
                    # Contar cuántas partes del nombre coinciden
                    for part in name_parts:
                        if part.upper() in excel_name:
                            score += 1
                    
                    # Si coinciden suficientes partes, es un buen candidato
                    if score >= 2 and score > best_score:  # Al menos 2 partes coinciden
                        best_match = row
                        best_score = score
                
                if best_match is not None:
                    player = _create_player_from_excel_row(best_match, png_file)
                    players.append(player)
                    player_found = True
            
            # Si aún no se encontró, crear jugador básico
            if not player_found:
                # Usar número del mapping o generar uno
                fallback_number = PLAYER_NAME_MAPPING.get(png_file, (png_file, 99))[1]
                
                player = {
                    "number": fallback_number,
                    "name": png_file.split('_')[0].title(),
                    "surnames": " ".join(png_file.split('_')[1:]).title(),
                    "slug": png_file,
                    "image_url": None
                }
                players.append(player)
        
        # Ordenar por número
        players.sort(key=lambda x: x['number'])
        
    except Exception as e:
        st.error(f"Error cargando jugadores: {str(e)}")
        return FALLBACK_PLAYERS
    
    return players


def _create_player_from_excel_row(row, png_file):
    """Crea un objeto jugador a partir de una fila del Excel"""
    full_name = row['JUGADOR']
    player_number = int(row['DORSAL']) if pd.notna(row['DORSAL']) else 99
    
    # Asignar URL de imagen con validación básica
    raw_image_url = row['IMAGEN'] if pd.notna(row['IMAGEN']) else None
    image_url = raw_image_url if _validate_image_url(raw_image_url) else None
    
    # Separar nombre y apellidos
    if ',' in full_name:
        surnames, name = full_name.split(',', 1)
        surnames = surnames.strip()
        name = name.strip()
    else:
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            name = name_parts[0]
            surnames = ' '.join(name_parts[1:])
        else:
            name = full_name
            surnames = ""
    
    return {
        "number": player_number,
        "name": name,
        "surnames": surnames,
        "slug": png_file,
        "image_url": image_url
    }


def get_team_players() -> List[Dict[str, Any]]:
    """Obtiene la lista de jugadores del equipo"""
    return load_players_dynamically()


def find_player_by_slug(slug: str) -> Dict[str, Any]:
    """Busca un jugador por su slug"""
    players = get_team_players()
    return next((p for p in players if p["slug"] == slug), None)