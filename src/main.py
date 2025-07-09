import flet as ft
from datetime import datetime, date
import requests
import pytz

API_URL = "https://api-telchac-production-45c8.up.railway.app/"

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED)
    page.title = "Recibos - Version de Escritorio"
    page.padding = 10

    todos_los_recibos = []
    pagina_actual = 0
    tamanio_pagina = 11


    zona_horaria = pytz.timezone("America/Merida")
    hoy = datetime.now(zona_horaria).date()
    hoy_str = hoy.isoformat()

    logo = ft.Image(
        src="https://i.ibb.co/SDz9CZXS/Imagen-de-Whats-App-2025-04-22-a-las-15-46-24-f6a2c21e.jpg",
        width=60, height=60, fit=ft.ImageFit.CONTAIN
    )

    titulo_empresa = ft.Text("TELCHAC PUERTO", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    titulo = ft.Text("Consulta de Recibos", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    txt_fecha_desde = ft.TextField(label="Desde", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
    txt_fecha_desde.data = hoy_str

    txt_fecha_hasta = ft.TextField(label="Hasta", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
    txt_fecha_hasta.data = hoy_str

    def actualizar_fecha(txt, nueva_fecha):
        txt.data = nueva_fecha
        txt.value = datetime.fromisoformat(nueva_fecha).strftime("%d-%m-%Y")
        buscar_producto(contribuyente_input.value)
        page.update()

    date_picker_desde = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_desde, e.data), value=date.today(), expand=1)
    date_picker_hasta = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_hasta, e.data), value=date.today(), expand=1)
    page.overlay.extend([date_picker_desde, date_picker_hasta])

    fecha_desde_btn = ft.ElevatedButton("Fecha desde", icon=ft.icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_desde), expand=1)
    fecha_hasta_btn = ft.ElevatedButton("Fecha hasta", icon=ft.icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_hasta), expand=1)

    contribuyente_input = ft.TextField(
        label="Filtrar por contribuyente (opcional)",
        width=400,
        text_size=14,
        border_color=ft.Colors.GREY,
        color=ft.Colors.BLACK,
        cursor_color=ft.Colors.BLACK,
        expand=True
    )

    buscar_btn = ft.ElevatedButton("Buscar",
        width=300, height=40, icon=ft.icons.SEARCH,
        bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE, expand=1
    )
    desplegar_btn = ft.ElevatedButton("Resumen",
        width=150, height=40, icon=ft.icons.INFO,
        bgcolor=ft.Colors.AMBER, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE, expand=1
    )
    buscar_btn.on_click = lambda e: buscar_producto(contribuyente_input.value)
    desplegar_btn.on_click = lambda e: mostrar_despliegue_totales()

    desplegar_dialog = ft.AlertDialog(title=ft.Text("Despliegue de Totales"))

    encabezado = ft.Container(
                content=ft.Column([
                    ft.Row([logo, titulo_empresa], alignment=ft.MainAxisAlignment.START),
                    titulo,
                    ft.Row([
                        fecha_desde_btn,
                        fecha_hasta_btn
                    ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Row([
                        txt_fecha_desde,
                        txt_fecha_hasta
                    ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Row([
                        buscar_btn,
                        desplegar_btn
                    ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    contribuyente_input,
                ],
                spacing=10,
                expand=True),
                padding=20,
                bgcolor=ft.Colors.RED,
                border_radius=ft.BorderRadius(0, 0, 20, 20),
            )


    resultado_card = ft.Container(content=ft.Column([], expand=True, scroll=ft.ScrollMode.AUTO), padding=10)
    totales_card = ft.Container()
    loader = ft.ProgressRing(visible=False, color=ft.Colors.ORANGE, stroke_width=4)

    def formatear_fecha_mejor(fecha_str):
        try:
            fecha = datetime.strptime(fecha_str, "%y%m%d")  # convierte a objeto datetime
            return fecha.strftime("%d/%m/%Y")  # convierte a string en formato DD/MM/YYYY
        except Exception as e:
            return f"Formato inválido: {fecha_str}"  # por si acaso
        
    def cambiar_pagina(delta):
        nonlocal pagina_actual
        pagina_actual += delta
        mostrar_pagina()
        
    def mostrar_resultados(data):
        nonlocal todos_los_recibos, pagina_actual
        todos_los_recibos = data
        pagina_actual = 0
        mostrar_pagina()

    def mostrar_pagina():
        nonlocal pagina_actual, tamanio_pagina, todos_los_recibos

        inicio = pagina_actual * tamanio_pagina
        fin = inicio + tamanio_pagina
        fragmento = todos_los_recibos[inicio:fin]

        # Encabezados de tabla
        columnas = [
            ft.DataColumn(label=ft.Text("Recibo")),
            ft.DataColumn(label=ft.Text("Contribuyente")),
            ft.DataColumn(label=ft.Text("Concepto")),
            ft.DataColumn(label=ft.Text("Fecha")),
            ft.DataColumn(label=ft.Text("Neto")),
            ft.DataColumn(label=ft.Text("Descuento")),
        ]

        filas = []

        for r in fragmento:
            es_cancelado = r.get("status", r.get("id_status", "0")) == "1"
            color_texto = ft.Colors.GREY if es_cancelado else ft.Colors.BLACK
            estado = "❌ CANCELADO" if es_cancelado else ""

            fila = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"{r['recibo']} {estado}", color=color_texto)),
                    ft.DataCell(ft.Text(r['contribuyente'], color=color_texto, size=10)),
                    ft.DataCell(ft.Text(r['concepto'], color=color_texto, size=10)),
                    ft.DataCell(ft.Text(formatear_fecha_mejor(r['fecha']), color=color_texto)),
                    ft.DataCell(ft.Text(f"${float(r['neto']):,.2f}", color=ft.Colors.GREEN_800 if not es_cancelado else color_texto)),
                    ft.DataCell(ft.Text(f"${float(r['descuento']):,.2f}", color=color_texto)),
                ]
            )
            filas.append(fila)

        botones_navegacion = []

        if pagina_actual > 0:
            botones_navegacion.append(ft.ElevatedButton("⬅️ Anteriores", on_click=lambda e: cambiar_pagina(-1)))

        if fin < len(todos_los_recibos):
            botones_navegacion.append(ft.ElevatedButton("Siguientes ➡️", on_click=lambda e: cambiar_pagina(1)))

        resultado_card.content = ft.Column([
            ft.DataTable(
                columns=columnas,
                rows=filas,
                heading_row_color=ft.Colors.RED_100,
                data_row_min_height=40,
                divider_thickness=0.8,
                show_checkbox_column=False
            ),
            ft.Row(botones_navegacion, alignment=ft.MainAxisAlignment.CENTER)
        ], scroll=ft.ScrollMode.ALWAYS)

        page.update()

    def buscar_producto(nombre_raw):
        buscar_btn.disabled = True
        loader.visible = True
        fecha_desde_btn.disabled = True
        fecha_hasta_btn.disabled = True
        desplegar_btn.visible = False
        buscar_btn.width = 300
        page.update()

        desde_date = datetime.fromisoformat(txt_fecha_desde.data).date()
        hasta_date = datetime.fromisoformat(txt_fecha_hasta.data).date()
        
        desde = desde_date.strftime("%y%m%d")  # Formato YYMMDD
        hasta = hasta_date.strftime("%y%m%d")  # Formato YYMMDD
        
        params = {"desde": desde, "hasta": hasta}

        nombre = nombre_raw.strip()
        if nombre:
            params["contribuyente"] = nombre

        cancelados = 0
        data = []

        try:
            url = f"{API_URL}recibos/filtrar" if "contribuyente" in params else f"{API_URL}recibos"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                cancelados = sum(1 for r in data if r.get("status", r.get("id_status", "0")) == "1")
                mostrar_resultados(data)
            else:
                print("Error:", response.status_code, response.json().get("detail"))
        except Exception as e:
            print("Error al buscar recibos:", str(e))

        try:
            response_totales = requests.get(f"{API_URL}recibos/totales", params=params)
            if response_totales.status_code == 200:
                d = response_totales.json()
                totales_card.content = ft.Column([
                    ft.Text(f"Total Neto: ${float(d.get('total_neto', 0)):,.2f}", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Total Descuento: ${float(d.get('total_descuento', 0)):,.2f}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Recibos encontrados: {len(data)}", size=14, color=ft.Colors.BLACK),
                    ft.Text(f"Recibos cancelados: {d.get('cantidad_status_1', 0)}", size=14, color=ft.Colors.RED_700)
                ])
        except Exception as e:
            print("Error al obtener totales:", str(e))

        loader.visible = False
        buscar_btn.disabled = False
        fecha_hasta_btn.disabled = False
        fecha_desde_btn.disabled = False
        buscar_btn.width = 150
        desplegar_btn.visible = True
        page.update()

    def mostrar_despliegue_totales():
        desde_date = datetime.fromisoformat(txt_fecha_desde.data).date()
        hasta_date = datetime.fromisoformat(txt_fecha_hasta.data).date()

        desde = desde_date.strftime("%y%m%d")  # Formato YYMMDD
        hasta = hasta_date.strftime("%y%m%d")  # Formato YYMMDD

        params = {"desde": desde, "hasta": hasta}
        try:
            response = requests.get(f"{API_URL}recibos/totales/despliegue", params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    desplegar_dialog.content = ft.Text("No se encontraron totales en este rango de fechas.")
                    page.open(desplegar_dialog)
                    return

                columnas_tabla = [
                    ft.DataColumn(label=ft.Text("Cuenta", weight=ft.FontWeight.BOLD, expand=True)),
                    ft.DataColumn(label=ft.Text("Total Neto", weight=ft.FontWeight.BOLD, expand=True)),
                    ft.DataColumn(label=ft.Text("Total Descuento", weight=ft.FontWeight.BOLD, expand=True)),
                ]

                filas_tabla = []
                for cuenta_data in data:
                    cuenta = cuenta_data.get("cuenta", "Sin cuenta")
                    total_neto = cuenta_data.get("total_neto", 0.0)
                    total_descuento = cuenta_data.get("total_descuento", 0.0)

                    fila = ft.DataRow(cells=[
                        ft.DataCell(ft.Text(cuenta)),
                        ft.DataCell(ft.Text(f"${total_neto:,.2f}", color=ft.Colors.GREEN_700)),
                        ft.DataCell(ft.Text(f"${total_descuento:,.2f}")),
                    ])
                    filas_tabla.append(fila)

                tabla = ft.DataTable(
                    columns=columnas_tabla,
                    rows=filas_tabla,
                    heading_row_color=ft.Colors.AMBER_100,
                    divider_thickness=0.6,
                    show_checkbox_column=False,
                )

                desplegar_dialog.content = ft.Container(
                    content=ft.Column(
                        [
                            tabla
                        ], scroll=ft.ScrollMode.AUTO
                    ),
                    padding=0,
                    width=800,
                    height=400
                )
                page.open(desplegar_dialog)


            else:
                desplegar_dialog.content = ft.Text(f"Error al obtener datos: {response.status_code}")
                page.open(desplegar_dialog)
        except Exception as e:
            print("Error al obtener totales:", str(e))
            desplegar_dialog.content = ft.Text("Hubo un error al intentar obtener los datos.")
            page.open(desplegar_dialog)


    page.add(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                            [
                                encabezado,
                                loader,
                                totales_card,
                            ],
                            spacing=20,
                            expand=1
                            
                        ), bgcolor=ft.Colors.RED_50
                        ),
                        ft.Container(
                                content=ft.Column(
                                [
                                    resultado_card,
                                ],
                                spacing=20,
                                expand=2,
                                scroll=ft.ScrollMode.AUTO ,
                            ), alignment=ft.alignment.top_center, expand=2
                        )
                    ],
                    expand=True 
                ),
                expand=True,
                height=page.height
            )
        )

    buscar_producto("")

ft.app(target=main)