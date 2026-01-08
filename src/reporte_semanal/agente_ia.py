import os
from groq import Groq
from dotenv import load_dotenv
from rich.console import Console

console = Console()
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def redactar_correo(df_alertas):
    """Redacta el correo con estilo ejecutivo, breve y sin firmas."""
    
    incidencias = df_alertas[df_alertas['MOTIVO'] != ""].to_dict(orient='records')
    
    if not incidencias:
        return "Estimado Wilbert, informo que las sesiones de esta semana se desarrollaron sin novedades."

    # Prompt ajustado para eliminar el 'floro' y la firma
    prompt = f"""
    Eres un asistente administrativo eficiente. Redacta un mensaje BREVE para Wilbert.
    
    DATOS:
    {incidencias}
    
    REGLAS DE REDACCIÓN:
    1. Estilo directo y ejecutivo (máximo 3 o 4 líneas).
    2. Menciona puntualmente el curso, el PERIODO, el NRC (PERIODO.NRC) y la incidencia.
    3. NO incluyas despedidas como 'Atentamente' ni firmas. 
    4. NO inventes cargos (no pongas 'Coordinador').
    5. Empieza directamente con el saludo 'Estimado Wilbert,'.
    """

    with console.status("[bold green]⚡ Groq está ajustando el texto...[/bold green]"):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5 # Bajamos la temperatura para que sea menos creativo y más preciso
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"❌ Error en Groq: {str(e)}"