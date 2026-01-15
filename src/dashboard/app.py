import flet as ft
from src.shared.config_loader import config
from src.dashboard.engine import contar_alertas, contar_clases_hoy
from src.dashboard.funciones import crear_tarjeta

# configuración básica de la ventana
def main(page: ft.Page):
  # importamos los estilos definidos de config.yaml
  estilo = config['dashboard']['estilo']
  textos = config['dashboard']['textos']

  # Configuración de la página
  page.title = 'Academic Suite - dashboard'
  page.theme_mode = ft.ThemeMode.DARK
  page.bgcolor = estilo['color_fondo']
  page.vertical_alignment = ft.MainAxisAlignment.CENTER
  page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

  # llamamos a engine.py
  num_alertas = contar_alertas()
  num_clases = contar_clases_hoy()

  # Componente visual barra de progreso 
  color_alertas = estilo['color_alerta'] if num_alertas > 0 else ft.Colors.GREEN
  color_clases = ft.Colors.BLUE_ACCENT if num_clases > 0 else ft.Colors.BLUE_GREY_700


  #----------------------------------
  # Tarjetas usando las funciones
  #----------------------------------
  tarjeta_alerta = crear_tarjeta(
    titulo=textos['titulo_alerta'],
    valor=num_alertas,
    subtitulo=textos['subtitulo_alerta'],
    color_principal=color_alertas,
    color_fondo=estilo['color_tarjeta'],
    ancho=300
  )

  tarjeta_clases = crear_tarjeta(
    titulo="CLASES HOY",
    valor=num_clases,
    subtitulo="Sesiones programadas",
    color_principal=color_clases,
    color_fondo=estilo['color_tarjeta'],
    ancho=300
  )

  # --- 5. LAYOUT FINAL ---
  page.add(
    ft.Row(
      controls=[tarjeta_alerta, tarjeta_clases],
      alignment=ft.MainAxisAlignment.CENTER,
      spacing=30
    )
  )

if __name__ == '__main__':
  ft.app(target=main)
