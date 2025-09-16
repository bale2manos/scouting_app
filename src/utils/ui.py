# src/utils/ui.py
# -*- coding: utf-8 -*-
"""
Utilidades de interfaz de usuario para Streamlit
"""
import base64
from pathlib import Path
from typing import Optional, List, Tuple
import streamlit as st
import streamlit.components.v1 as components

from ..config import CSS, PDF_VIEWER_HEIGHT


def set_route(route: str, **kwargs):
    """Cambia de vista y fuerza rerun inmediato (evita 2 clics)."""
    # Guardar la ruta anterior en el historial
    current_route = st.session_state.get("route", "home")
    if "navigation_history" not in st.session_state:
        st.session_state["navigation_history"] = []
    
    # Solo agregar al historial si es una ruta diferente
    if current_route != route:
        st.session_state["navigation_history"].append(current_route)
        # Mantener solo las últimas 5 rutas para no sobrecargar
        if len(st.session_state["navigation_history"]) > 5:
            st.session_state["navigation_history"] = st.session_state["navigation_history"][-5:]
    
    st.session_state["route"] = route
    for k, v in kwargs.items():
        st.session_state[k] = v
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def go_back():
    """Navega a la ruta anterior en el historial."""
    history = st.session_state.get("navigation_history", [])
    if history:
        previous_route = history.pop()
        st.session_state["route"] = previous_route
    else:
        # Si no hay historial, ir a home
        st.session_state["route"] = "home"
    
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def back_button(label="← Atrás"):
    """Renderiza un botón para ir atrás."""
    if st.button(label):
        go_back()


def find_image_detailed(base_no_ext: Path) -> Tuple[Optional[Path], List[Path]]:
    """Busca imagen probando extensiones; devuelve (path_encontrado, rutas_intentadas)."""
    tried = []
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        cand = base_no_ext.with_suffix(ext)
        tried.append(cand)
        if cand.exists():
            return cand, tried
    return None, tried


def embed_pdf_local(path: Path, height: int = 600, start_page: int = 1, show_download: bool = False):
    """
    Visor PDF accesible para móvil con:
      - Paginación por botones e input.
      - Swipe/drag izquierda/derecha para cambiar de página (táctil y ratón).
      - Reajuste automático tras rotación/cambio de tamaño (usa visualViewport).
    """
    if not path.exists() or path.stat().st_size == 0:
        st.error(f"❌ PDF no encontrado o vacío: {path}")
        return

    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")

    html = f"""
    <style>
      .pdf-container {{
        max-width: 1000px;
        margin: 0 auto;
        border-radius: 8px;
        position: relative;
      }}
      .pdf-toolbar {{
        display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
        padding: 8px 12px; border: 1px solid #2a2a2a; border-radius: 8px 8px 0 0;
        background: #0f1115; color: #e6e6e6; font: 600 14px system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial;
      }}
      .pdf-toolbar button, .pdf-toolbar input {{
        background: #1b1e26; color: #e6e6e6; border: 1px solid #2a2a2a; border-radius: 8px;
        padding: 8px 12px; font-weight: 700; min-height: 40px; min-width: 44px;
      }}
      .pdf-toolbar button:disabled {{ opacity: .5; cursor: not-allowed; }}
      .pdf-page-input {{ width: 64px; text-align: center; }}
      .pdf-viewer {{
        width: 100%;
        height: {height}px; /* valor inicial; JS lo recalcula para móvil/rotación */
        overflow: hidden; border: 1px solid #2a2a2a; border-top: 0;
        border-radius: 0 0 8px 8px; background: #111; padding: 6px;
        display: flex; align-items: center; justify-content: center; position: relative;
        touch-action: pan-y pinch-zoom; /* permite scroll vertical y pinch; el swipe horizontal lo gestionamos a mano */
        box-sizing: border-box;
      }}
      #the-canvas {{
        max-width: 100%; max-height: 100%; display: block; margin: 0 auto;
        cursor: grab; image-rendering: auto;
        touch-action: pan-y pinch-zoom; /* evita que el navegador coma el gesto horizontal */
      }}
      #the-canvas:active {{ cursor: grabbing; }}
      .swipe-indicator {{
        position: absolute; top: 50%; transform: translateY(-50%);
        background: rgba(255,255,255,0.08); color: #fff; padding: 16px;
        border-radius: 50%; opacity: 0; transition: opacity .25s ease; pointer-events: none;
        font-size: 22px;
      }}
      .swipe-indicator.left {{ left: 16px; }}
      .swipe-indicator.right {{ right: 16px; }}
      .swipe-indicator.show {{ opacity: 1; }}

      @media (max-width: 768px) {{
        .pdf-toolbar {{ border-radius: 0; }}
        .pdf-container {{ border-radius: 0; }}
        .pdf-viewer {{ border-radius: 0; }}
      }}
    </style>

    <div class="pdf-container">
      <div class="pdf-toolbar">
        <button id="btnPrev" title="Página anterior">⟨</button>
        <div>Página&nbsp;<input id="pageNum" class="pdf-page-input" type="number" min="1" value="{max(1,int(start_page))}"> / <span id="pageCount">?</span></div>
        <button id="btnNext" title="Página siguiente">⟩</button>
        <span id="status" style="margin-left:auto;opacity:.75;"></span>
      </div>
      <div id="pdfjs_container" class="pdf-viewer">
        <canvas id="the-canvas"></canvas>
        <div class="swipe-indicator left" id="swipeLeft">⟨</div>
        <div class="swipe-indicator right" id="swipeRight">⟩</div>
      </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
      (function(){{
        const pdfDataB64 = "{b64}";
        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

        const $ = s => document.querySelector(s);
        const statusEl = $("#status");
        const canvas = $("#the-canvas");
        const ctx = canvas.getContext('2d', {{ alpha: false }});
        const container = $("#pdfjs_container");
        const pageInput = $("#pageNum");
        const pageCountEl = $("#pageCount");
        const btnPrev = $("#btnPrev");
        const btnNext = $("#btnNext");
        const swipeLeft = $("#swipeLeft");
        const swipeRight = $("#swipeRight");

        let pdf = null;
        let currentPage = Math.max(1, parseInt(pageInput.value || "1"));
        let rendering = false;

        const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

        function setStatus(msg) {{ if (statusEl) statusEl.textContent = msg || ""; }}
        function clamp(v, a, b) {{ return Math.min(b, Math.max(a, v)); }}
        function u8FromB64(b64) {{
          const bin = atob(b64), arr = new Uint8Array(bin.length);
          for (let i=0;i<bin.length;i++) arr[i] = bin.charCodeAt(i);
          return arr;
        }}
        function updateButtons(){{
          btnPrev.disabled = (currentPage <= 1);
          btnNext.disabled = (pdf && currentPage >= pdf.numPages);
        }}

        // Alto dinámico para móvil: usa visualViewport cuando exista
        function updateViewerHeight(){{
          const vv = window.visualViewport || {{ height: window.innerHeight }};
          // margen aproximado para toolbar y paddings; deja hueco para UI móvil
          const offset = 180;
          const minH = 360;
          const h = Math.max(minH, Math.floor(vv.height - offset));
          container.style.height = h + "px";
        }}

        function fitScale(page){{
          const viewport = page.getViewport({{ scale: 1 }});
          const rect = container.getBoundingClientRect();
          const aw = Math.max(100, rect.width - 12);
          const ah = Math.max(100, rect.height - 12);
          const scaleX = aw / viewport.width;
          const scaleY = ah / viewport.height;
          return Math.min(scaleX, scaleY);
        }}

        async function renderPage(num){{
          if (!pdf || rendering) return;
          rendering = true; setStatus("Renderizando...");
          try {{
            const page = await pdf.getPage(num);
            const scale = fitScale(page);
            const v = page.getViewport({{ scale }});

            // DPI correcto sin acumulación
            const dpr = Math.max(1, window.devicePixelRatio || 1);
            canvas.width = Math.floor(v.width * dpr);
            canvas.height = Math.floor(v.height * dpr);
            canvas.style.width = Math.floor(v.width) + "px";
            canvas.style.height = Math.floor(v.height) + "px";

            // reset transform en cada render para evitar acumulación
            ctx.setTransform(1,0,0,1,0,0);
            ctx.imageSmoothingEnabled = true;
            ctx.scale(dpr, dpr);

            await page.render({{ canvasContext: ctx, viewport: v, background: 'white' }}).promise;
            setStatus(`Página ${{num}} / ${{pdf.numPages}}`);
          }} catch(e) {{
            console.error(e); setStatus("Error al renderizar");
          }} finally {{
            rendering = false;
          }}
        }}

        async function goTo(num){{
          if (!pdf) return;
          currentPage = clamp(num, 1, pdf.numPages);
          pageInput.value = currentPage;
          updateButtons();
          await renderPage(currentPage);
        }}

        // Carga del PDF
        pdfjsLib.getDocument({{ data: u8FromB64(pdfDataB64) }}).promise.then(p => {{
          pdf = p; pageCountEl.textContent = pdf.numPages;
          updateViewerHeight();
          updateButtons();
          goTo(currentPage);
        }}).catch(err => {{ console.error(err); setStatus("No se pudo abrir el PDF"); }});

        // Controles
        btnPrev.addEventListener("click", () => goTo(currentPage - 1));
        btnNext.addEventListener("click", () => goTo(currentPage + 1));
        pageInput.addEventListener("change", () => goTo(parseInt(pageInput.value || "1")));
        pageInput.addEventListener("keydown", (e) => {{ if (e.key === "Enter") goTo(parseInt(pageInput.value||"1")); }});

        // Swipe/drag con Pointer Events (funciona con ratón y táctil)
        let dragStartX = 0, dragStartY = 0, dragging = false;
        let lastMoveX = 0, lastMoveY = 0;

        function showSwipe(dir){{
          (dir==='left' ? swipeLeft : swipeRight).classList.add('show');
          setTimeout(()=> (dir==='left' ? swipeLeft : swipeRight).classList.remove('show'), 220);
        }}

        const onPointerDown = (e) => {{
          dragging = true;
          dragStartX = e.clientX; dragStartY = e.clientY;
          lastMoveX = dragStartX; lastMoveY = dragStartY;
          // Capturamos el puntero para seguir recibiendo eventos
          canvas.setPointerCapture && canvas.setPointerCapture(e.pointerId);
        }};
        const onPointerMove = (e) => {{
          if (!dragging) return;
          lastMoveX = e.clientX; lastMoveY = e.clientY;
          const dx = lastMoveX - dragStartX;
          const dy = lastMoveY - dragStartY;
          // si el gesto es claramente horizontal, evita el scroll
          if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) e.preventDefault();
        }};
        const onPointerUp = (e) => {{
          if (!dragging) return;
          dragging = false;
          const dx = lastMoveX - dragStartX;
          const dy = lastMoveY - dragStartY;
          const minSwipe = 50; // umbral
          if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > minSwipe) {{
            if (dx > 0) {{
              if (currentPage > 1) {{ showSwipe('left'); goTo(currentPage - 1); }}
            }} else {{
              if (pdf && currentPage < pdf.numPages) {{ showSwipe('right'); goTo(currentPage + 1); }}
            }}
          }}
        }};

        // Registrar pointer events en canvas y contenedor (más área útil)
        [canvas, container].forEach(el => {{
          el.addEventListener('pointerdown', onPointerDown, {{ passive: false }});
          el.addEventListener('pointermove', onPointerMove, {{ passive: false }});
          el.addEventListener('pointerup', onPointerUp, {{ passive: false }});
          el.addEventListener('pointercancel', onPointerUp, {{ passive: false }});
          el.addEventListener('pointerleave', onPointerUp, {{ passive: false }});
        }});

        // Redibujo y ajuste tras rotación / resize
        function handleResize(){{
          updateViewerHeight();
          renderPage(currentPage);
        }}
        let roTimer = null;
        const scheduleResize = () => {{
          if (roTimer) cancelAnimationFrame(roTimer);
          roTimer = requestAnimationFrame(handleResize);
        }};

        new ResizeObserver(scheduleResize).observe(container);
        new ResizeObserver(scheduleResize).observe(document.body);
        window.addEventListener('resize', scheduleResize);
        window.addEventListener('orientationchange', () => setTimeout(scheduleResize, 250));

        // Atajos de teclado (desktop)
        if (!isTouch) {{
          window.addEventListener('keydown', (e) => {{
            if (!pdf) return;
            if (e.key === 'ArrowLeft') {{ e.preventDefault(); goTo(currentPage - 1); }}
            if (e.key === 'ArrowRight') {{ e.preventDefault(); goTo(currentPage + 1); }}
          }});
        }}
      }})();
    </script>
    """
    components.html(html, height=height + 50, scrolling=False)

    if show_download:
        st.download_button(
            "⬇️ Descargar PDF",
            data=base64.b64decode(b64),
            file_name=path.name,
            mime="application/pdf",
            use_container_width=True
        )



def download_button_for_pdf(path: Path, label: str, file_name: str):
    """Crea un botón de descarga para archivos PDF."""
    if not path.exists():
        st.warning(f"📄 Archivo no disponible para descarga: {path.name}")
        st.button(label, disabled=True, use_container_width=True, help="Archivo no encontrado")
        return
    
    try:
        # Verificar que el archivo no esté vacío
        if path.stat().st_size == 0:
            st.warning(f"📄 El archivo está vacío: {path.name}")
            st.button(label, disabled=True, use_container_width=True, help="Archivo vacío")
            return
            
        st.download_button(
            label, 
            data=path.read_bytes(), 
            file_name=file_name,
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"❌ Error al preparar descarga: {str(e)}")
        st.button(label, disabled=True, use_container_width=True, help=f"Error: {str(e)}")


def player_label(n: int, name: str, surnames: str) -> str:
    """Genera etiqueta consistente para jugadores: DORSAL - INICIAL. APELLIDOS"""
    # Obtener la inicial del nombre (primer carácter en mayúscula)
    initial = name.strip()[0].upper() if name.strip() else "?"
    
    # Formatear apellidos en mayúsculas
    surnames_upper = surnames.strip().upper() if surnames.strip() else "APELLIDOS"
    
    return f"{n} - {initial}. {surnames_upper}"


def big_card(title: str, height: int = 220):
    """Crea una tarjeta grande con título centrado."""
    st.markdown(
        f"<div class='card' style='height:{height}px;display:flex;align-items:center;justify-content:center;"
        f"font-size:26px;font-weight:700;'>"
        f"{title}</div>",
        unsafe_allow_html=True
    )


def safe_image(image_url: str = None, fallback_path: Path = None, placeholder: str = "🏀", **kwargs):
    """
    Muestra una imagen con fallback automático en caso de error
    
    Args:
        image_url: URL de la imagen a mostrar
        fallback_path: Path a imagen local de respaldo
        placeholder: Emoji o texto si todo falla
        **kwargs: Argumentos adicionales para st.image()
    """
    image_shown = False
    
    # 1. Intentar URL externa (solo si es válida)
    if image_url and _is_reliable_image_url(image_url):
        try:
            st.image(image_url, **kwargs)
            image_shown = True
        except:
            pass  # Continuar al fallback
    
    # 2. Fallback a imagen local
    if not image_shown and fallback_path and fallback_path.exists():
        try:
            st.image(str(fallback_path), **kwargs)
            image_shown = True
        except:
            pass  # Continuar al placeholder
    
    # 3. Placeholder final
    if not image_shown:
        st.markdown(f'<div style="text-align: center; font-size: 3rem;">{placeholder}</div>', unsafe_allow_html=True)


def _is_reliable_image_url(url: str) -> bool:
    """Verifica si una URL de imagen es confiable"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url.startswith('http'):
        return False
    
    # Lista de dominios/patrones problemáticos
    unreliable_patterns = [
        'imagenes.feb.es',
        'Foto.aspx',
        '.aspx?',
        'dynamic-image',
        'temp-image'
    ]
    
    for pattern in unreliable_patterns:
        if pattern in url:
            return False
    
    # Verificar que termine en extensión de imagen
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']
    return any(url.lower().endswith(ext) for ext in valid_extensions)


def apply_styles():
    """Aplica los estilos CSS globales."""
    st.markdown(CSS, unsafe_allow_html=True)