import flet as ft

def handle_hover(e): # función de interacción
  es_hover = str(e.data).lower() == "true" # efecto mouse
  e.control.scale = 1.05 if es_hover else 1.0 # cambio de escala
  colores = e.control.border.top.color #si la tarjeta es Azul, el brillo será Azul. Si es Roja, será Roja.
  e.control.border = ft.border.all(3, colores) if es_hover else ft.border.all(2, colores) # efecto brillo en el borde
  e.control.update()


def crear_tarjeta(titulo, valor, subtitulo, color_principal, color_fondo, ancho=None):
  """
  Crea una tarjeta estandarizada con los datos y colores que le pases.
  """
  return ft.Container(
    content=ft.Column(
      controls=[
        ft.Text(titulo, size=20, color=color_principal, weight=ft.FontWeight.BOLD),
        ft.Text(f"{valor}", size=60, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        ft.Text(subtitulo, size=16, color=ft.Colors.GREY_400),
      ],
      horizontal_alignment=ft.CrossAxisAlignment.CENTER,
      spacing=10
    ),
    width=ancho,
    padding=40,
    border_radius=20,
    # Aquí asignamos el color inicial (Rojo o Azul)
    border=ft.border.all(2, color_principal),
    bgcolor=color_fondo,
        
    # Conectamos la animación y el hover genérico
    on_hover=handle_hover,
    animate_scale=ft.Animation(300, ft.AnimationCurve.DECELERATE),
  ) 