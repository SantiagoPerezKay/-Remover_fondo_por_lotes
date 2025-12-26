# Removedor de Fondos en Lote (Python)

Script en **Python** para remover el fondo de imágenes de forma **masiva**, automática y local usando **rembg (U²-Net)**.  
Convierte las imágenes a **WebP con transparencia**, ideal para e-commerce, catálogos y marketplaces.

Funciona tanto como **script Python** como **.exe compilado con PyInstaller**.

---

## 🚀 Qué hace

- Procesa **todas las imágenes de una carpeta**
- Remueve el fondo usando **IA (U²-Net)**
- Guarda las imágenes:
  - Con **transparencia**
  - En formato **WebP sin pérdida**
- Procesamiento **multiproceso** (más rápido)
- Manejo de errores y fallback secuencial
- Compatible con **Windows (.exe)**

---

## 🖼️ Formatos soportados

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.bmp`
- `.tiff`

---

## 📦 Salida

Las imágenes procesadas se guardan automáticamente en:

