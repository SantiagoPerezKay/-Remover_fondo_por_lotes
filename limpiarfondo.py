import os
import io
import sys
import traceback
import tempfile
import shutil
from pathlib import Path
from rembg import remove
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import freeze_support

# Extensiones válidas de imágenes
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")

def get_resource_path():
    """Obtiene la ruta correcta para recursos, tanto en desarrollo como en exe"""
    if getattr(sys, 'frozen', False):
        # Si está compilado con PyInstaller
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(sys.executable)
    else:
        # Si está ejecutándose como script
        return os.path.dirname(os.path.abspath(__file__))

def setup_u2net_path():
    """Configura la ruta de los modelos U2NET"""
    base_path = get_resource_path()
    u2net_path = os.path.join(base_path, "u2net")
    
    # Crear directorio si no existe
    os.makedirs(u2net_path, exist_ok=True)
    
    # Configurar variable de entorno
    os.environ["U2NET_HOME"] = u2net_path
    
    print(f"📁 Ruta de modelos U2NET: {u2net_path}")
    return u2net_path

def verificar_permisos(folder_path):
    """Verifica si se tienen permisos de escritura en la carpeta"""
    try:
        test_file = os.path.join(folder_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception as e:
        print(f"⚠️ Sin permisos de escritura en {folder_path}: {e}")
        return False

def procesar_imagen(args):
    """Procesa una sola imagen removiendo el fondo"""
    input_folder, output_folder, filename = args
    input_path = os.path.join(input_folder, filename)
    
    try:
        print(f"🔄 Procesando: {filename}")
        
        # Verificar que el archivo existe
        if not os.path.exists(input_path):
            return f"❌ Archivo no encontrado: {filename}"
        
        # Leer bytes de la imagen
        with open(input_path, "rb") as f:
            in_bytes = f.read()
        
        # Verificar que se leyeron datos
        if not in_bytes:
            return f"❌ No se pudieron leer datos de: {filename}"
        
        print(f"📖 Leyendo {len(in_bytes)} bytes de {filename}")
        
        # Procesar con rembg → devuelve bytes
        print(f"🤖 Removiendo fondo de {filename}...")
        out_bytes = remove(in_bytes)

        # Asegurar que hay salida
        if not out_bytes:
            return f"❌ Error con {filename}: rembg no devolvió datos"

        print(f"✨ Fondo removido de {filename}, {len(out_bytes)} bytes generados")
        
        # Convertir a imagen con transparencia
        output_img = Image.open(io.BytesIO(out_bytes)).convert("RGBA")

        # Generar nombre de salida
        name = Path(filename).stem
        output_filename = f"{name}_sin_fondo.webp"
        output_path = os.path.join(output_folder, output_filename)

        # Guardar imagen en formato WebP sin pérdida
        print(f"💾 Guardando en: {output_path}")
        output_img.save(output_path, "WEBP", lossless=True, quality=100)
        
        # Verificar que el archivo se guardó correctamente
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return f"✅ Procesado exitosamente: {filename} → {output_filename}"
        else:
            return f"❌ Error al guardar: {filename}"

    except Exception as e:
        tb = traceback.format_exc()
        return f"❌ Error con {filename}: {str(e)}\n{tb}"

def main():
    print("🎨 Removedor de Fondos v2.0")
    print("=" * 50)
    
    # Configurar rutas de modelos
    try:
        u2net_path = setup_u2net_path()
    except Exception as e:
        print(f"⚠️ Error configurando modelos: {e}")
    
    # Solicitar carpeta de entrada
    input_folder = input("👉 Ingrese la ruta de la carpeta con imágenes: ").strip().strip('"')
    
    if not input_folder:
        print("❌ Debe ingresar una ruta válida.")
        input("Presiona Enter para salir...")
        return
    
    if not os.path.isdir(input_folder):
        print(f"❌ La ruta '{input_folder}' no existe o no es una carpeta.")
        input("Presiona Enter para salir...")
        return

    print(f"📁 Carpeta de entrada: {input_folder}")
    
    # Crear carpeta de salida
    output_folder = os.path.join(input_folder, "imagenes_sin_fondo")
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"📁 Carpeta de salida: {output_folder}")
    except Exception as e:
        print(f"❌ Error creando carpeta de salida: {e}")
        input("Presiona Enter para salir...")
        return
    
    # Verificar permisos de escritura
    if not verificar_permisos(output_folder):
        print("❌ No se tienen permisos de escritura en la carpeta de salida.")
        input("Presiona Enter para salir...")
        return

    # Buscar archivos de imagen
    archivos = []
    for f in os.listdir(input_folder):
        if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS:
            archivos.append(f)

    if not archivos:
        print("⚠️ No se encontraron imágenes válidas en la carpeta.")
        print(f"Extensiones soportadas: {', '.join(VALID_EXTENSIONS)}")
        input("Presiona Enter para salir...")
        return

    print(f"🖼️ Se encontraron {len(archivos)} imágenes para procesar")
    print("\nArchivos encontrados:")
    for i, archivo in enumerate(archivos, 1):
        print(f"  {i}. {archivo}")
    
    print(f"\n🔄 Iniciando procesamiento...\n")

    # Procesar imágenes (reducir workers para evitar problemas de memoria)
    resultados_exitosos = 0
    resultados_con_error = 0
    
    try:
        # Usar menos workers para evitar problemas de memoria en exe
        max_workers = min(2, len(archivos))
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            tareas = [(input_folder, output_folder, f) for f in archivos]
            
            for i, resultado in enumerate(executor.map(procesar_imagen, tareas), 1):
                print(f"[{i}/{len(archivos)}] {resultado}")
                
                if "✅" in resultado:
                    resultados_exitosos += 1
                else:
                    resultados_con_error += 1
                    
    except Exception as e:
        print(f"❌ Error durante el procesamiento multiproceso: {e}")
        print("\n🔄 Intentando procesamiento secuencial...")
        
        # Fallback a procesamiento secuencial
        for i, archivo in enumerate(archivos, 1):
            resultado = procesar_imagen((input_folder, output_folder, archivo))
            print(f"[{i}/{len(archivos)}] {resultado}")
            
            if "✅" in resultado:
                resultados_exitosos += 1
            else:
                resultados_con_error += 1

    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DEL PROCESAMIENTO:")
    print(f"✅ Exitosos: {resultados_exitosos}")
    print(f"❌ Con errores: {resultados_con_error}")
    print(f"📁 Imágenes guardadas en: {output_folder}")
    
    if resultados_exitosos > 0:
        print("\n🎉 ¡Procesamiento completado!")
    else:
        print("\n⚠️ No se pudo procesar ninguna imagen.")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    freeze_support()  # Necesario para multiproceso en Windows
    main()