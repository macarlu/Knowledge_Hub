import requests
from bs4 import BeautifulSoup

def descargar_web(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Usar BeautifulSoup para extraer texto principal
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style"]):
            script.extract()
        
        # Obtener texto limpio
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error al descargar {url}: {e}")
        return ""