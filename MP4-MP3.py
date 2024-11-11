from moviepy.editor import *
from tkinter import Tk, filedialog

# Inicializar tkinter (sin mostrar la ventana principal)
root = Tk()
root.withdraw()

# Seleccionar archivo MP4
video_path = filedialog.askopenfilename(title="Selecciona el archivo MP4", filetypes=[("Video files", "*.mp4")])
if not video_path:
    print("No se seleccionó ningún archivo.")
else:
    # Seleccionar ubicación y nombre para el archivo MP3
    save_path = filedialog.asksaveasfilename(title="Guardar archivo MP3", defaultextension=".mp3", filetypes=[("Audio files", "*.mp3")])
    if not save_path:
        print("No se seleccionó una ubicación para guardar el archivo.")
    else:
        # Cargar el archivo de video
        video = VideoFileClip(video_path)

        # Extraer el audio y guardarlo en formato MP3
        video.audio.write_audiofile(save_path)
        print("Archivo MP3 guardado correctamente en:", save_path)
