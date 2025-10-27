# src/utils/player_classification.py
# -*- coding: utf-8 -*-
"""
Sistema de clasificación de jugadores (Interiores/Exteriores)
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Ruta del archivo de clasificación
CLASSIFICATION_FILE = Path("data/players_classification.json")

# Tipos de clasificación válidos
CLASSIFICATION_TYPES = {
    "exterior": "🔵 EXTERIOR",
    "interior": "🔴 INTERIOR",
    None: "⚪ SIN CLASIFICAR"
}


class PlayerClassificationManager:
    """Gestor de clasificaciones de jugadores"""
    
    def __init__(self):
        self.classification_file = CLASSIFICATION_FILE
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Carga el archivo de clasificación o crea uno vacío"""
        if self.classification_file.exists():
            try:
                with open(self.classification_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando clasificación: {e}")
                return {}
        else:
            # Crear estructura inicial
            return {}
    
    def _save_data(self) -> bool:
        """Guarda el archivo de clasificación"""
        try:
            # Asegurar que existe el directorio
            self.classification_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.classification_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error guardando clasificación: {e}")
            return False
    
    def get_classification(self, team_slug: str, player_slug: str) -> Optional[str]:
        """
        Obtiene la clasificación de un jugador
        
        Args:
            team_slug: Identificador del equipo
            player_slug: Identificador del jugador
            
        Returns:
            'exterior', 'interior' o None (sin clasificar)
        """
        if team_slug not in self.data:
            return None
        return self.data[team_slug].get(player_slug)
    
    def set_classification(self, team_slug: str, player_slug: str, 
                          classification: Optional[str]) -> bool:
        """
        Establece la clasificación de un jugador
        
        Args:
            team_slug: Identificador del equipo
            player_slug: Identificador del jugador
            classification: 'exterior', 'interior' o None (para quitar clasificación)
            
        Returns:
            True si se guardó correctamente
        """
        # Validar clasificación
        if classification not in ['exterior', 'interior', None]:
            logger.error(f"Clasificación inválida: {classification}")
            return False
        
        # Crear entrada del equipo si no existe
        if team_slug not in self.data:
            self.data[team_slug] = {}
        
        # Establecer o eliminar clasificación
        if classification is None:
            # Eliminar clasificación
            if player_slug in self.data[team_slug]:
                del self.data[team_slug][player_slug]
        else:
            # Establecer clasificación
            self.data[team_slug][player_slug] = classification
        
        return self._save_data()
    
    def set_multiple_classifications(self, team_slug: str, 
                                    classifications: Dict[str, Optional[str]]) -> bool:
        """
        Establece múltiples clasificaciones de una vez
        
        Args:
            team_slug: Identificador del equipo
            classifications: Diccionario {player_slug: classification}
            
        Returns:
            True si se guardó correctamente
        """
        # Crear entrada del equipo si no existe
        if team_slug not in self.data:
            self.data[team_slug] = {}
        
        # Actualizar clasificaciones
        for player_slug, classification in classifications.items():
            if classification in ['exterior', 'interior']:
                self.data[team_slug][player_slug] = classification
            elif classification is None:
                # Eliminar clasificación
                if player_slug in self.data[team_slug]:
                    del self.data[team_slug][player_slug]
        
        return self._save_data()
    
    def get_team_classifications(self, team_slug: str) -> Dict[str, Optional[str]]:
        """
        Obtiene todas las clasificaciones de un equipo
        
        Args:
            team_slug: Identificador del equipo
            
        Returns:
            Diccionario {player_slug: classification}
        """
        return self.data.get(team_slug, {})
    
    def classify_players_list(self, team_slug: str, players: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Clasifica una lista de jugadores en grupos
        
        Args:
            team_slug: Identificador del equipo
            players: Lista de diccionarios de jugadores (con 'slug')
            
        Returns:
            Diccionario con claves 'exterior', 'interior', 'unclassified'
        """
        result = {
            'exterior': [],
            'interior': [],
            'unclassified': []
        }
        
        for player in players:
            player_slug = player.get('slug')
            if not player_slug:
                result['unclassified'].append(player)
                continue
            
            classification = self.get_classification(team_slug, player_slug)
            
            if classification == 'exterior':
                result['exterior'].append(player)
            elif classification == 'interior':
                result['interior'].append(player)
            else:
                result['unclassified'].append(player)
        
        return result


def can_classify_players(user: Optional[Dict]) -> bool:
    """
    Verifica si un usuario puede clasificar jugadores
    
    Args:
        user: Diccionario con datos del usuario (debe tener 'role' y 'username')
        
    Returns:
        True si el usuario puede clasificar (admin o coach)
    """
    if not user:
        return False
    
    # Verificar si es admin
    if user.get('role') == 'admin':
        return True
    
    # Verificar si tiene 'coach' en el username (para usuarios con rol 'user')
    username = user.get('username', '').lower()
    if 'coach' in username or 'entrenador' in username:
        return True
    
    return False
