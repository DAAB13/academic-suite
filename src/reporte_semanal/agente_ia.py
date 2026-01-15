import os
from groq import Groq
from dotenv import load_dotenv
from rich.console import Console

console = Console() # rich para darle formato visual a la terminal
load_dotenv() # cargamos variables de .env

client = Groq(api_key=os.getenv("GROQ_API_KEY")) # conexión con el cliente groq

def redactar_correo(df_alertas):
    """Redacta el correo con estilo ejecutivo, breve y sin firmas."""
    
    incidencias = df_alertas[df_alertas['MOTIVO'] != ""].to_dict(orient='records') # lo convierte a una lista de diccionarios que la ia entiende mejor 
    
    if not incidencias:
        return "Estimado Wilbert, informo que las sesiones de esta semana se desarrollaron sin novedades."
    prompt = f"""
    Eres un asistente administrativo eficiente. Redacta un mensaje BREVE para William.
    
    DATOS:
    {incidencias}
    
    REGLAS DE REDACCIÓN:
    1. Estilo directo y ejecutivo (máximo 3 o 4 líneas).
    2. Menciona puntualmente el curso, el PERIODO, el NRC (PERIODO.NRC) y la incidencia.
    3. NO incluyas despedidas como 'Atentamente' ni firmas. 
    4. NO inventes cargos (no pongas 'Coordinador').
    5. Empieza directamente con el saludo 'Estimado William,'.
    """
    # bloque de 'status' de Rich para mostrar un mensaje de carga mientras la IA responde.
    with console.status("[bold green]⚡ Groq está ajustando el texto...[/bold green]"):
        try:
            # llamada a la API de GROQ para generar texto
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5 # Bajamos la temperatura para que sea menos creativo y más preciso
            )
            # Retornamos solo el texto de la respuesta generada
            return completion.choices[0].message.content
        except Exception as e:
            return f"❌ Error en Groq: {str(e)}"