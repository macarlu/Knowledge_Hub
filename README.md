"Organizador Personal de Recursos Profesionales" ("KnowledgeHub"). Es una aplicación web para centralizar información útil en tu carrera, con funcionalidades prácticas pero sin excesiva complejidad.
📝 Descripción del Proyecto
Un sistema donde puedas guardar, organizar y buscar recursos como:
•	Enlaces web (artículos, tutoriales, documentación)
•	Documentos locales (PDFs, imágenes)
•	Notas rápidas
•	Tareas pendientes
Con capacidad para etiquetar contenido y buscar eficientemente.
________________________________________
⚙️ Stack Tecnológico
Componente	Tecnología
Backend	Python + Flask
Frontend	HTML + CSS + Bootstrap
Base de Datos	MongoDB
Contenedorización	Docker
Extra	Requests (descargas web)
________________________________________
🧩 Funcionalidades Clave
1.	Gestión de Recursos
o	Añadir URLs con captura automática de título
o	Subir documentos (PDF, imágenes)
o	Crear notas rápidas
o	Sistema de etiquetas (ej: "Python", "Docker", "Urgente")
2.	Búsqueda Inteligente
o	Filtros por tipo (enlace/nota/documento)
o	Búsqueda por palabras clave en contenido
o	Búsqueda por etiquetas
3.	Descargas Web (Extra)
o	Guardar copia local de páginas web (HTML)
o	Almacenar contenido textual para búsquedas offline
4.	Organización Visual
o	Vista de tarjetas clasificables
o	Sistema de favoritos
o	Marcado de recursos "Para revisar"
________________________________________
🗄️ Estructura de la Base de Datos (MongoDB)
// Colección: recursos
{
  "_id": ObjectId,
  "tipo": "enlace|nota|documento|tarea",
  "titulo": String,
  "descripcion": String,
  "contenido": String, // Texto para notas o HTML descargado
  "url": String,       // Para enlaces
  "ruta_archivo": String, // Para documentos subidos
  "etiquetas": [String],
  "favorito": Boolean,
  "fecha_creacion": DateTime,
  "para_revisar": Boolean
}
________________________________________
🐳 Configuración Docker (docker-compose.yml)
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./app:/app
      - ./uploads:/app/uploads  # Para archivos subidos
    environment:
      - MONGO_URI=mongodb://db:27017/knowledgehub
    depends_on:
      - db

  db:
    image: mongo:5.0
    volumes:
      - db_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=knowledgehub

volumes:
  db_data:
________________________________________
📂 Estructura de Archivos
knowledgehub/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── app/
    ├── __init__.py
    ├── routes.py
    ├── models.py
    ├── utils.py         # Funciones helper (ej: descargar webs)
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   ├── add_resource.html
    │   └── search.html
    ├── static/
    │   ├── css/
    │   └── js/
    └── uploads/         # Carpeta para archivos subidos
________________________________________
🧠 Conceptos que Practicarás
1.	Flask:
o	Rutas, formularios, sesiones
o	Manejo de archivos estáticos
o	Renderizado de templates Jinja2
2.	MongoDB:
o	Operaciones CRUD
o	Consultas con filtros compuestos
o	Gestión de documentos binarios (GridFS opcional)
3.	Docker:
o	Contenedorización de app y DB
o	Volúmenes persistentes
o	Comunicación entre contenedores
4.	Frontend:
o	Diseño responsive con Bootstrap
o	Interacciones AJAX (para búsquedas dinámicas)
________________________________________
💡 Ejemplo de Código (Flask + MongoDB)
# routes.py - Añadir recurso
@app.route('/add', methods=['POST'])
def add_resource():
    tipo = request.form['tipo']
    
    nuevo_recurso = {
        "tipo": tipo,
        "titulo": request.form['titulo'],
        "etiquetas": request.form.getlist('etiquetas'),
        "fecha_creacion": datetime.utcnow()
    }
    
    if tipo == "enlace":
        nuevo_recurso["url"] = request.form['url']
        # Opcional: Descargar contenido web automático
        if 'descargar' in request.form:
            contenido = utils.descargar_web(request.form['url'])
            nuevo_recurso["contenido"] = contenido
    
    # Insertar en MongoDB
    mongo.db.recursos.insert_one(nuevo_recurso)
    return redirect(url_for('index'))
________________________________________
🚀 Pasos para Implementar
1.	Configurar entorno Docker con MongoDB
2.	Crear sistema de autenticación básico (opcional pero recomendado)
3.	Implementar CRUD para recursos
4.	Desarrollar sistema de búsqueda con filtros
5.	Añadir función de descarga web (usando requests + BeautifulSoup)
6.	Diseñar interfaz con Bootstrap
7.	Implementar subida de archivos (usar flask.secure_filename)
________________________________________
🌟 Beneficios para tu Carrera
•	Organización centralizada: Todo tu material profesional en un solo lugar
•	Acceso desde cualquier dispositivo: Web = disponible siempre
•	Base para proyectos futuros: Puedes expandirlo (ej: añadir APIs, IA para clasificación automática)
•	Portafolio tangible: Demuestra tus habilidades full-stack
Dificultad estimada: ⭐⭐☆☆☆ (Nivel intermedio, ideal para consolidar conocimientos sin frustraciones)

🧭 Cómo funciona la aplicación actualmente:
1.	Página principal (index):
o	URL: http://localhost:5000/
o	Muestra una lista de recursos (inicialmente vacía)
o	Tienes un botón "Añadir Nuevo Recurso" que lleva al formulario
2.	Formulario de añadir recurso:
o	URL: http://localhost:5000/add
o	Permite seleccionar entre 3 tipos de recursos:
	📎 Enlace web (con opción para descargar contenido)
	📝 Nota (texto libre)
	📄 Documento (subir archivos)
📝 Cómo añadir información:
Paso 1: Accede al formulario
1.	Ve a http://localhost:5000/
2.	Haz clic en el botón "Añadir Nuevo Recurso"
Paso 2: Completa el formulario
•	Campos comunes a todos los recursos:
o	Tipo de recurso: Selecciona uno de los 3 tipos
o	Título: Nombre descriptivo del recurso
o	Descripción: Información adicional
o	Etiquetas: Palabras clave separadas por comas (ej: python, docker, web)
•	Campos específicos:
o	Para Enlace web:
	URL: Dirección completa (ej: https://es.wikipedia.org/)
	Opción: "Descargar contenido para búsqueda offline" (marca si quieres guardar el texto de la página)
o	Para Nota:
	Contenido: Texto libre (puedes escribir lo que necesites)
o	Para Documento:
	Subir archivo: Selecciona un archivo de tu computadora (PDF, imagen, etc.)
Paso 3: Guarda el recurso
•	Haz clic en el botón "Guardar"
•	Serás redirigido a la página principal donde verás:
o	Un mensaje de confirmación: "Recurso añadido correctamente!"
o	Tu nuevo recurso aparecerá en la lista
🔍 Ejemplos prácticos:
1.	Guardar un enlace útil:
o	Tipo: Enlace web
o	Título: "Documentación oficial de Flask"
o	URL: https://flask.palletsprojects.com/
o	Etiquetas: flask, python, documentación
o	Marcar "Descargar contenido" para tenerlo disponible offline
2.	Crear una nota:
o	Tipo: Nota
o	Título: "Comandos Docker importantes"
o	Contenido:
text
Copy
Download
docker-compose up --build
docker ps -a
docker exec -it nombre_contenedor bash
o	Etiquetas: docker, comandos
3.	Subir un documento:
o	Tipo: Documento
o	Título: "Apuntes MongoDB"
o	Seleccionar archivo: mongodb-cheatsheet.pdf
o	Etiquetas: mongodb, base de datos, cheatsheet

