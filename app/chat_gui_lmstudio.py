import tkinter as tk
from tkinter import scrolledtext
import requests
import json

# URL y modelo
URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "deepseek-r1-distill-llama-8b"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer lm-studio"
}

conversation = [
    {"role": "system", "content": "Eres un asistente útil que responde en español."}
]

def send_message():
    user_input = entry.get()
    if not user_input.strip():
        return

    chat_window.insert(tk.END, f"Tú: {user_input}\n")
    entry.delete(0, tk.END)

    conversation.append({"role": "user", "content": user_input})

    payload = {
        "model": MODEL,
        "messages": conversation,
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post(URL, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()

        reply = response.json()["choices"][0]["message"]["content"].strip()
        conversation.append({"role": "assistant", "content": reply})

        chat_window.insert(tk.END, f"🤖 Modelo: {reply}\n\n")
        chat_window.see(tk.END)

    except Exception as e:
        chat_window.insert(tk.END, f"❌ Error: {e}\n")

# Crear ventana principal
root = tk.Tk()
root.title("Chat LM Studio (Interfaz Gráfica)")

# Área de chat
chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=25, font=("Segoe UI", 10))
chat_window.pack(padx=10, pady=10)
chat_window.insert(tk.END, "💬 Bienvenido al chat con tu modelo local.\n\n")

# Campo de entrada de texto
entry = tk.Entry(root, width=60, font=("Segoe UI", 10))
entry.pack(padx=10, pady=(0, 10), side=tk.LEFT)
entry.bind("<Return>", lambda event: send_message())

# Botón de enviar
send_button = tk.Button(root, text="Enviar", command=send_message, width=10)
send_button.pack(pady=(0, 10), padx=(0, 10), side=tk.LEFT)

# Ejecutar la app
root.mainloop()
