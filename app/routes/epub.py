from flask import Blueprint, render_template, flash, redirect, url_for, current_app, send_file
from flask_login import login_required
from .. import mongo
import html
import re
import os
import zipfile
import xml.etree.ElementTree as ET
import io

epub_bp = Blueprint('epub', __name__)

@epub_bp.route('/ver_epub/<filename>')
@login_required
def ver_epub(filename):
    """
    Muestra el contenido de un EPUB en línea
    """
    try:
        # Buscar el documento en la base de datos
        documento = mongo.db.documents.find_one({'ruta_archivo': filename})
        if not documento:
            flash('Documento no encontrado', 'error')
            return redirect(url_for('main.index'))
            
        # Ruta completa del archivo
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        # Valores por defecto
        title = filename
        author = 'Sin autor'
        chapters = []
        content = ''
        
        try:
            # Intentar abrir el archivo como ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Buscar el contenido.opf
                    opf_files = [f for f in zip_ref.namelist() if f.endswith('content.opf')]
                    if opf_files:
                        # Leer el contenido.opf para obtener la estructura
                        opf_content = zip_ref.read(opf_files[0]).decode('utf-8')
                        root = ET.fromstring(opf_content)
                        
                        # Obtener el título del libro
                        title_elements = root.findall('.//{http://purl.org/dc/elements/1.1/}title')
                        if title_elements:
                            title = title_elements[0].text or filename
                        
                        # Obtener el autor del libro
                        creator_elements = root.findall('.//{http://purl.org/dc/elements/1.1/}creator')
                        if creator_elements:
                            author = creator_elements[0].text or 'Sin autor'
                        
                        # Buscar y procesar todos los archivos HTML/XHTML
                        for file_name in zip_ref.namelist():
                            if file_name.lower().endswith(('.html', '.xhtml')):
                                try:
                                    # Leer el contenido del archivo
                                    html_content = zip_ref.read(file_name)
                                    # Intentar decodificar con diferentes codificaciones
                                    try:
                                        content = html.unescape(html_content.decode('utf-8'))
                                    except:
                                        try:
                                            content = html.unescape(html_content.decode('utf-16'))
                                        except:
                                            try:
                                                content = html.unescape(html_content.decode('utf-8-sig'))
                                            except:
                                                content = html.unescape(html_content.decode('latin1'))
                                    
                                    # Mantener la estructura HTML original
                                    # Solo eliminar tags innecesarios
                                    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<head.*?>.*?</head>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<meta.*?>', '', content)
                                    content = re.sub(r'<link.*?>', '', content)
                                    
                                    # Actualizar las rutas de las imágenes
                                    # Buscar todas las imágenes y actualizar sus rutas
                                    image_pattern = r'<img[^>]+src=["\'](.*?)["\'][^>]*>'
                                    for match in re.finditer(image_pattern, content):
                                        img_src = match.group(1)
                                        # Verificar si la imagen existe en el EPUB
                                        try:
                                            # Buscar la imagen en el ZIP
                                            image_path = None
                                            for zip_file in zip_ref.namelist():
                                                # Intentar encontrar la imagen por nombre
                                                if os.path.basename(zip_file) == os.path.basename(img_src):
                                                    image_path = zip_file
                                                    break
                                            
                                            # Si encontramos la imagen, actualizar la ruta
                                            if image_path:
                                                # Crear una URL única para la imagen
                                                img_url = f'/epub/image/{filename}/{os.path.basename(image_path)}'
                                                # Actualizar la ruta en el contenido
                                                content = content.replace(img_src, img_url)
                                        except:
                                            continue
                                    
                                    # Mantener las estructuras importantes
                                    content = content.replace('<body>', '<div class="chapter-content">')
                                    content = content.replace('</body>', '</div>')
                                    
                                    # Limpiar espacios extra pero mantener saltos de línea
                                    content = re.sub(r'\s+', ' ', content)
                                    content = content.strip()
                                    
                                    if content:
                                        # Usar el nombre del archivo como título
                                        title = os.path.basename(file_name)
                                        chapters.append({
                                            'title': title,
                                            'content': content
                                        })
                                except Exception as e:
                                    print(f"Error al procesar {file_name}: {str(e)}")
                                    continue
                        
                        # Ordenar los capítulos por nombre de archivo
                        chapters.sort(key=lambda x: x['title'])
                        
                    else:
                        chapters.append({
                            'title': 'Error',
                            'content': 'No se encontró el archivo content.opf en el EPUB.'
                        })
                        
            except zipfile.BadZipFile:
                # Si no es un ZIP válido, intentar abrir como archivo normal
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        if content:
                            chapters.append({
                                'title': 'Contenido',
                                'content': content
                            })
                except Exception as e:
                    chapters.append({
                        'title': 'Error',
                        'content': f'Error al leer el archivo: {str(e)}'
                    })
            
        except Exception as e:
            # Si hay error al abrir el EPUB, mostrar un mensaje más descriptivo
            chapters = [{
                'title': 'Error',
                'content': f'Error al procesar el EPUB: {str(e)}'
            }]
            
        return render_template('ver_epub.html', 
                             title=title,
                             author=author,
                             chapters=chapters)
        
    except Exception as e:
        flash(f'Error al abrir el EPUB: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@epub_bp.route('/image/<epub_name>/<image_name>')
@login_required
def get_image(epub_name, image_name):
    """
    Devuelve una imagen del EPUB
    """
    try:
        # Buscar el documento en la base de datos
        documento = mongo.db.documents.find_one({'ruta_archivo': epub_name})
        if not documento:
            return "Imagen no encontrada", 404
            
        # Ruta completa del archivo
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, epub_name)
        
        # Abrir el EPUB como ZIP
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Buscar la imagen en el ZIP
            for zip_file in zip_ref.namelist():
                if os.path.basename(zip_file) == image_name:
                    # Leer la imagen
                    image_data = zip_ref.read(zip_file)
                    # Crear una respuesta con la imagen
                    # Determinar el tipo MIME de la imagen
        mime_type = 'image/jpeg'  # Por defecto
        if image_name.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_name.lower().endswith('.gif'):
            mime_type = 'image/gif'
        
        return send_file(
            io.BytesIO(image_data),
            mimetype=mime_type
        )
        
        return "Imagen no encontrada", 404
        
    except Exception as e:
        print(f"Error al obtener imagen: {str(e)}")
        return "Error al obtener la imagen", 500
    """
    Muestra el contenido de un EPUB en línea
    """
    try:
        # Buscar el documento en la base de datos
        documento = mongo.db.documents.find_one({'ruta_archivo': filename})
        if not documento:
            flash('Documento no encontrado', 'error')
            return redirect(url_for('main.index'))
            
        # Ruta completa del archivo
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        # Valores por defecto
        title = filename
        author = 'Sin autor'
        chapters = []
        content = ''
        
        try:
            # Intentar abrir el archivo como ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Buscar el contenido.opf
                    opf_files = [f for f in zip_ref.namelist() if f.endswith('content.opf')]
                    if opf_files:
                        # Leer el contenido.opf para obtener la estructura
                        opf_content = zip_ref.read(opf_files[0]).decode('utf-8')
                        root = ET.fromstring(opf_content)
                        
                        # Obtener el título del libro
                        title_elements = root.findall('.//{http://purl.org/dc/elements/1.1/}title')
                        if title_elements:
                            title = title_elements[0].text or filename
                        
                        # Obtener el autor del libro
                        creator_elements = root.findall('.//{http://purl.org/dc/elements/1.1/}creator')
                        if creator_elements:
                            author = creator_elements[0].text or 'Sin autor'
                        
                        # Buscar y procesar todos los archivos HTML/XHTML
                        for file_name in zip_ref.namelist():
                            if file_name.lower().endswith(('.html', '.xhtml')):
                                try:
                                    # Leer el contenido del archivo
                                    html_content = zip_ref.read(file_name)
                                    # Intentar decodificar con diferentes codificaciones
                                    try:
                                        content = html.unescape(html_content.decode('utf-8'))
                                    except:
                                        try:
                                            content = html.unescape(html_content.decode('utf-16'))
                                        except:
                                            try:
                                                content = html.unescape(html_content.decode('utf-8-sig'))
                                            except:
                                                content = html.unescape(html_content.decode('latin1'))
                                    
                                    # Mantener la estructura HTML original
                                    # Solo eliminar tags innecesarios
                                    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<head.*?>.*?</head>', '', content, flags=re.DOTALL)
                                    content = re.sub(r'<meta.*?>', '', content)
                                    content = re.sub(r'<link.*?>', '', content)
                                    
                                    # Actualizar las rutas de las imágenes
                                    # Buscar todas las imágenes y actualizar sus rutas
                                    image_pattern = r'<img[^>]+src=["\'](.*?)["\'][^>]*>'
                                    for match in re.finditer(image_pattern, content):
                                        img_src = match.group(1)
                                        # Verificar si la imagen existe en el EPUB
                                        try:
                                            # Buscar la imagen en el ZIP
                                            image_path = None
                                            for zip_file in zip_ref.namelist():
                                                # Intentar encontrar la imagen por nombre
                                                if os.path.basename(zip_file) == os.path.basename(img_src):
                                                    image_path = zip_file
                                                    break
                                            
                                            # Si encontramos la imagen, actualizar la ruta
                                            if image_path:
                                                # Crear una URL única para la imagen
                                                img_url = f'/epub/image/{filename}/{os.path.basename(image_path)}'
                                                # Actualizar la ruta en el contenido
                                                content = content.replace(img_src, img_url)
                                        except:
                                            continue
                                    
                                    # Mantener las estructuras importantes
                                    content = content.replace('<body>', '<div class="chapter-content">')
                                    content = content.replace('</body>', '</div>')
                                    
                                    # Limpiar espacios extra pero mantener saltos de línea
                                    content = re.sub(r'\s+', ' ', content)
                                    content = content.strip()
                                    
                                    if content:
                                        # Usar el nombre del archivo como título
                                        title = os.path.basename(file_name)
                                        chapters.append({
                                            'title': title,
                                            'content': content
                                        })
                                except Exception as e:
                                    print(f"Error al procesar {file_name}: {str(e)}")
                                    continue
                                except Exception as e:
                                    print(f"Error al procesar {file_name}: {str(e)}")
                                    continue
                        
                        # Si se obtuvo contenido
                        if content:
                            chapters.append({
                                'title': 'Contenido',
                                'content': content
                            })
                        
                        # Ordenar los capítulos por nombre de archivo
                        chapters.sort(key=lambda x: x['title'])
                        
                    else:
                        chapters.append({
                            'title': 'Error',
                            'content': 'No se encontró el archivo content.opf en el EPUB.'
                        })
                        
            except zipfile.BadZipFile:
                # Si no es un ZIP válido, intentar abrir como archivo normal
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        if content:
                            chapters.append({
                                'title': 'Contenido',
                                'content': content
                            })
                except Exception as e:
                    chapters.append({
                        'title': 'Error',
                        'content': f'Error al leer el archivo: {str(e)}'
                    })
            
        except Exception as e:
            # Si hay error al abrir el EPUB, mostrar un mensaje más descriptivo
            chapters = [{
                'title': 'Error',
                'content': f'Error al procesar el EPUB: {str(e)}'
            }]
            
        return render_template('ver_epub.html', 
                             title=title,
                             author=author,
                             chapters=chapters)
        
    except Exception as e:
        flash(f'Error al abrir el EPUB: {str(e)}', 'error')
        return redirect(url_for('main.index'))
        
        return render_template('ver_epub.html', 
                             title=title,
                             author=author,
                             chapters=chapters)
        
    except Exception as e:
        flash(f'Error al abrir el EPUB: {str(e)}', 'error')
        return redirect(url_for('main.index'))
