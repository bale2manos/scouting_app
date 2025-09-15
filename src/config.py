# config.py
# -*- coding: utf-8 -*-
"""
Configuración global de la aplicación Scouting Hub
"""
from pathlib import Path

# ==============================
# ======= CONFIG BÁSICA ========
# ==============================

TEAM_NAME_DISPLAY = "LUJISA GUADALAJARA BASKET"   # texto visible
TEAM_SLUG = "lujisa_guadalajara_basket"           # para rutas (minúsculas + _)

# ==============================
# ========== RUTAS =============
# ==============================

# Rutas de datos
DATA_DIR = Path("./data")
TEAM_LOGO_DIR = DATA_DIR / "club_images"
EXCEL_FILE = DATA_DIR / "jugadores.xlsx"

# Rutas específicas del equipo
TEAM_REPORT = DATA_DIR / "informe" / TEAM_SLUG / f"{TEAM_SLUG}.pdf"
PLAYER_REPORTS_DIR = DATA_DIR / "informe" / TEAM_SLUG / "jugadores"
PLAYER_PHOTOS_DIR = DATA_DIR / "informe" / TEAM_SLUG / "jugadores"

# Imagen genérica de fallback
GENERIC_USER_IMAGE = DATA_DIR / "generic_user.png"

# ==============================
# ===== GOOGLE DRIVE ==========
# ==============================

# Configuración de Google Drive
GOOGLE_DRIVE_ROOT_FOLDER_ID = "1y_UpkzuqR7rMVrN4oCc59HRahPaCfXTQ"  # EBA Pintobasket 25/26
GOOGLE_DRIVE_CREDENTIALS_PATH = "credentials/google_drive_credentials.json"

# Cache local para archivos descargados
CACHE_DIR = DATA_DIR / "cache"
DRIVE_CACHE_DIR = CACHE_DIR / "drive"

# Configuración de cache
CACHE_EXPIRY_HOURS = 24  # Renovar cache cada 24 horas
USE_DRIVE_FIRST = True   # True: Priorizar Google Drive, False: Priorizar archivos locales

# ==============================
# ===== CONFIG UI/UX ==========
# ==============================

# Configuración de la grilla de jugadores
PLAYERS_PER_ROW = 6

# Dimensiones de imágenes
PLAYER_IMAGE_WIDTH = 120
TEAM_LOGO_WIDTH_HOME = 160
TEAM_LOGO_WIDTH_TEAM = 140
PDF_VIEWER_HEIGHT = 600

# ==============================
# ===== INFORMACIÓN DEL PARTIDO ====
# ==============================

# Variables configurables para la página de inicio
NEXT_MATCH_DATE = "04/10/2024"  # Fecha del próximo partido (formato DD/MM/YYYY)
LEAGUE_POSITION = "3º"          # Posición en la liga
WINS_LOSSES = "15-10"           # Victorias-Derrotas

# ==============================
# ===== MAPEO DE JUGADORES ====
# ==============================

# Mapeo manual más preciso basado en los datos reales
PLAYER_NAME_MAPPING = {
    "ALMENARA_SANABRIAS_ALVARO": ("ALMENARA SANABRIAS, ALVARO", 1),
    "ALMENARA_SANABRIAS_D": ("D. ALMENARA SANABRIAS", 55),
    "DIAZ_ZARZUELA_FRANCISCO_JAVIER": ("DIAZ ZARZUELA, FRANCISCO JAVIER", 8),
    "VALERA_VILLEGAS_L": ("L. VALERA VILLEGAS", 9),
    # Para los que no están en Excel, usaremos números secuenciales
    "ARMSTRONG_ADRIAN_SOLOMON": ("ARMSTRONG, ADRIAN SOLOMON", 13),
    "CALVO_SALVE_ESHETE_GABRIEL": ("CALVO SALVE, ESHETE GABRIEL", 14),
    "DIALLO_MOUHAMED_MASSAYA": ("DIALLO, MOUHAMED MASSAYA", 15),
}

# Datos de fallback en caso de error
FALLBACK_PLAYERS = [
    {"number": 1,  "name": "Álvaro", "surnames": "ALMENARA SANABRIAS",  "slug": "ALMENARA_SANABRIAS_ALVARO"},
    {"number": 55, "name": "D.", "surnames": "ALMENARA SANABRIAS", "slug": "ALMENARA_SANABRIAS_D"},
]

# ==============================
# ========= ESTILOS CSS ========
# ==============================

CSS = """
<style>
.stButton > button {
  border-radius: 10px;
  padding: 0.5rem 0.9rem;
  font-weight: 600;
}

/* tarjetas */
.card {
  border: 1px solid rgba(140,140,160,0.25);
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}
.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

/* Modal superpuesto */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.5);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-content {
  background: white;
  border-radius: 12px;
  padding: 20px;
  max-width: 90%;
  max-height: 90%;
  overflow-y: auto;
}

/* breadcrumb estilo píldoras */
.bc-line {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}
.bc-sep {
  opacity: 0.65;
}
.bc-inline .stButton > button {
  background: transparent !important;
  border: none !important;
  padding: 0 2px !important;
  margin: 0 !important;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}
.bc-current {
  font-weight: 800;
}
</style>
"""