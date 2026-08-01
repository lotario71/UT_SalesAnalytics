"""
Sales Analytics — Android (versión simple SOAP).
Cuadrantes + Todas vs pagadas + Tipos + Comportamiento + Evolución PE.
Sin conta: gasto desde config.txt (respaldo).
"""
from __future__ import annotations

import datetime
import json
import traceback
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import requests
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField

import android_charts as charts
import android_expense as expense
import android_history as pe_history
import android_metrics as metrics
import android_paths as apaths
import android_year_cache as year_cache
import android_year_data as year_data
import app_version
import config


def _cpath(name: str) -> str:
    """Ruta escribible para graficas (PC o storage Android)."""
    return apaths.chart_path(name)


def _tipos_paths(year: int) -> tuple[str, str]:
    return (
        _cpath(f"chart_tipos_{year}.png"),
        _cpath(f"chart_tipos_paid_{year}.png"),
    )
SOAP_URL = "https://www.umbrellatravel.com/Services/PublicServices.svc"


def fetch_sales_summary(from_date, to_date, only_paid=False, first_level_client_id=None):
    first_level_tag = (
        f"<firstLevelClientId>{first_level_client_id}</firstLevelClientId>"
        if first_level_client_id not in (None, "")
        else ""
    )
    envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetServicesSalesStatistics xmlns="http://tempuri.org/">
      <from>{from_date.strftime("%Y-%m-%dT00:00:00")}</from>
      <to>{to_date.strftime("%Y-%m-%dT23:59:59")}</to>
      {first_level_tag}
      <computeOnlyPaidServices>{"true" if only_paid else "false"}</computeOnlyPaidServices>
    </GetServicesSalesStatistics>
  </soap:Body>
</soap:Envelope>'''
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"http://tempuri.org/IPublicServices/GetServicesSalesStatistics"',
    }
    response = requests.post(SOAP_URL, headers=headers, data=envelope, timeout=35)
    response.raise_for_status()
    records = []
    root = ET.fromstring(response.text)
    for item in root.iter():
        if item.tag.endswith("TotalSalesStatisticsDto"):
            record = {}
            for child in item:
                record[child.tag.split("}")[-1]] = child.text
            records.append(record)
    return records


class MainScreen(MDScreen):
    pass


kv = """
MDNavigationLayout:
    md_bg_color: 0.067, 0.094, 0.153, 1

    ScreenManager:
        MainScreen:
            name: "main"
            MDBoxLayout:
                id: main_column
                orientation: "vertical"
                md_bg_color: 0.067, 0.094, 0.153, 1
                padding: "0dp", "0dp", "0dp", "12dp"

                MDTopAppBar:
                    id: top_bar
                    title: "Sales Analytics"
                    elevation: 2
                    md_bg_color: 0.06, 0.09, 0.16, 1
                    specific_text_color: 0.89, 0.91, 0.94, 1
                    left_action_items: [["menu", lambda x: app.open_drawer()]]
                    right_action_items: []

                MDBoxLayout:
                    id: row_mode
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "44dp"
                    padding: "8dp", "4dp"
                    spacing: "6dp"
                    MDRaisedButton:
                        id: btn_all
                        text: "Todas"
                        size_hint_x: 0.5
                        md_bg_color: 0.08, 0.72, 0.65, 1
                        on_release: app.set_metrics_mode("all")
                    MDRaisedButton:
                        id: btn_paid
                        text: "Solo pagadas"
                        size_hint_x: 0.5
                        md_bg_color: 0.22, 0.26, 0.34, 1
                        on_release: app.set_metrics_mode("paid")

                MDBoxLayout:
                    id: row_year
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "56dp"
                    padding: "10dp", "6dp"
                    spacing: "10dp"
                    MDRaisedButton:
                        id: year_header
                        text: "2026  v"
                        size_hint_x: 1
                        md_bg_color: 0.08, 0.72, 0.65, 1
                        on_release: app.pick_pe_year()
                    MDIconButton:
                        id: btn_refresh_year
                        icon: "refresh"
                        theme_icon_color: "Custom"
                        icon_color: 0.08, 0.72, 0.65, 1
                        user_font_size: "36sp"
                        on_release: app.refresh_data()

                MDLabel:
                    id: mode_subtitle
                    text: "Toca el anio para cambiar · icono refresh actualiza"
                    font_style: "Body2"
                    halign: "center"
                    valign: "middle"
                    theme_text_color: "Custom"
                    text_color: 0.70, 0.75, 0.82, 1
                    size_hint_y: None
                    height: "40dp"
                    padding: "10dp", "4dp"
                    text_size: self.width, None
                    shorten: False

                MDBoxLayout:
                    id: loading_row
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "0dp"
                    opacity: 0
                    padding: "12dp", "0dp"
                    spacing: "10dp"
                    MDSpinner:
                        id: loading_spinner
                        size_hint: None, None
                        size: "22dp", "22dp"
                        active: False
                    MDLabel:
                        id: loading_banner
                        text: "Actualizando..."
                        font_style: "Caption"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.96, 0.75, 0.20, 1
                        valign: "middle"

                MDLabel:
                    id: expense_chip
                    text: "Gasto mes: —  (menu > Editar gasto)"
                    font_style: "Body2"
                    halign: "center"
                    valign: "middle"
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.88, 0.92, 1
                    size_hint_y: None
                    height: "32dp"
                    padding: "8dp", "2dp"
                    text_size: self.width, None

                MDBottomNavigation:
                    id: bottom_nav
                    panel_color: 0.08, 0.11, 0.18, 1
                    text_color_active: 0.08, 0.72, 0.65, 1

                    MDBottomNavigationItem:
                        name: "resumen"
                        text: "Resumen"
                        icon: "view-dashboard"
                        ScrollView:
                            do_scroll_x: False
                            MDBoxLayout:
                                id: cards_box
                                orientation: "vertical"
                                adaptive_height: True
                                padding: "12dp"
                                spacing: "10dp"

                    MDBottomNavigationItem:
                        name: "vs"
                        text: "Vs pagadas"
                        icon: "chart-bar"
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: "4dp"
                            Image:
                                id: img_vs
                                source: "chart_vs_paid.png"
                                allow_stretch: True
                                keep_ratio: False
                                size_hint: 1, 1

                    MDBottomNavigationItem:
                        name: "tipos"
                        text: "Tipos"
                        icon: "chart-pie"
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: "4dp"
                            Carousel:
                                id: carousel_tipos
                                loop: False
                                Image:
                                    id: img_tipos
                                    source: "chart_tipos.png"
                                    allow_stretch: True
                                    keep_ratio: False
                                Image:
                                    id: img_tipos_paid
                                    source: "chart_tipos_paid.png"
                                    allow_stretch: True
                                    keep_ratio: False

                    MDBottomNavigationItem:
                        name: "comp"
                        text: "Comport."
                        icon: "chart-line"
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: "4dp"
                            Image:
                                id: img_comp
                                source: "chart_comportamiento.png"
                                allow_stretch: True
                                keep_ratio: False
                                size_hint: 1, 1

                    MDBottomNavigationItem:
                        name: "pe"
                        text: "Evol. PE"
                        icon: "finance"
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: "4dp"
                            Image:
                                id: img_pe
                                source: "chart_pe_hist.png"
                                allow_stretch: True
                                keep_ratio: False
                                size_hint: 1, 1

                    MDBottomNavigationItem:
                        name: "actividad"
                        text: "Actividad"
                        icon: "history"
                        ScrollView:
                            do_scroll_x: False
                            MDLabel:
                                id: activity_log
                                text: "Sin actividad aun."
                                padding: "14dp", "12dp"
                                theme_text_color: "Custom"
                                text_color: 0.80, 0.84, 0.90, 1
                                size_hint_y: None
                                markup: False

    MDNavigationDrawer:
        id: nav_drawer
        radius: 0, 18, 18, 0
        width: "300dp"
        md_bg_color: 0.07, 0.10, 0.16, 1
        MDBoxLayout:
            orientation: "vertical"
            padding: "18dp"
            spacing: "12dp"
            MDLabel:
                text: "Sales Analytics"
                bold: True
                font_style: "H6"
                theme_text_color: "Custom"
                text_color: 0.08, 0.72, 0.65, 1
                size_hint_y: None
                height: "28dp"
            MDLabel:
                id: drawer_version
                text: "v2.2.2"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.58, 0.64, 0.72, 1
                size_hint_y: None
                height: "18dp"
            MDRaisedButton:
                text: "Actualizar datos"
                size_hint_x: 1
                md_bg_color: 0.08, 0.72, 0.65, 1
                on_release: app.refresh_data()
            MDRaisedButton:
                text: "Editar gasto mensual"
                size_hint_x: 1
                md_bg_color: 0.16, 0.22, 0.30, 1
                on_release: app.show_expense_dialog()
            MDRaisedButton:
                text: "Salir"
                size_hint_x: 1
                md_bg_color: 0.45, 0.18, 0.20, 1
                on_release: app.exit_app()
            Widget:
                size_hint_y: 1
            MDLabel:
                text: "Windows = SQL/conta · Movil = conta (años cerrados) + SOAP (año en curso)."
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.55, 0.60, 0.68, 1
                size_hint_y: None
                height: "48dp"
"""


class MetricCard(MDCard):
    """Tarjeta táctil estilo Windows (2 líneas), tamaño movil 14T."""

    def __init__(self, key: str, title: str, on_open, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.on_open = on_open
        self.orientation = "vertical"
        self.padding = "14dp"
        self.spacing = "4dp"
        self.radius = [14]
        self.size_hint_y = None
        self.height = "118dp"
        self.md_bg_color = (0.12, 0.16, 0.22, 1)
        self.ripple_behavior = True
        self.title_lbl = MDLabel(
            text=title,
            font_style="Body2",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.08, 0.72, 0.65, 1),
            size_hint_y=None,
            height="24dp",
            shorten=True,
            shorten_from="right",
        )
        self.line1 = MDLabel(
            text="—",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.89, 0.91, 0.94, 1),
            size_hint_y=None,
            height="36dp",
            shorten=True,
            shorten_from="right",
        )
        self.line2 = MDLabel(
            text="",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(0.8, 0.83, 0.88, 1),
            size_hint_y=None,
            height="24dp",
            shorten=True,
            shorten_from="right",
        )
        self.add_widget(self.title_lbl)
        self.add_widget(self.line1)
        self.add_widget(self.line2)

    def on_release(self):
        if callable(self.on_open):
            self.on_open(self.key)


def _rgba_tone(tone):
    if tone == "ok":
        return (0.13, 0.77, 0.37, 1)
    if tone == "bad":
        return (0.94, 0.27, 0.27, 1)
    return (0.89, 0.91, 0.94, 1)


class MetricPopupBody(MDBoxLayout):
    """Contenido visual del detalle de métrica (badge + filas + fórmula)."""

    def __init__(self, popup: dict, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.padding = "4dp", "8dp", "4dp", "4dp"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        badge = (popup or {}).get("badge")
        if badge:
            chip = MDCard(
                size_hint_y=None,
                height="36dp",
                padding="10dp",
                radius=[10],
                md_bg_color=(0.14, 0.18, 0.26, 1),
            )
            chip.add_widget(
                MDLabel(
                    text=str(badge),
                    bold=True,
                    theme_text_color="Custom",
                    text_color=_rgba_tone((popup or {}).get("badge_tone")),
                    halign="center",
                )
            )
            self.add_widget(chip)

        for row in (popup or {}).get("rows") or []:
            card = MDCard(
                orientation="horizontal",
                size_hint_y=None,
                height="44dp",
                padding="12dp",
                radius=[10],
                md_bg_color=(0.10, 0.14, 0.20, 1),
            )
            card.add_widget(
                MDLabel(
                    text=str(row.get("label") or ""),
                    theme_text_color="Custom",
                    text_color=(0.70, 0.74, 0.80, 1),
                    size_hint_x=0.48,
                )
            )
            card.add_widget(
                MDLabel(
                    text=str(row.get("value") or ""),
                    bold=True,
                    halign="right",
                    theme_text_color="Custom",
                    text_color=_rgba_tone(row.get("tone")),
                    size_hint_x=0.52,
                )
            )
            self.add_widget(card)

        formula = (popup or {}).get("formula") or ""
        if formula:
            box = MDCard(
                size_hint_y=None,
                padding="12dp",
                radius=[10],
                md_bg_color=(0.08, 0.11, 0.16, 1),
            )
            box.bind(minimum_height=box.setter("height"))
            lbl = MDLabel(
                text=formula,
                theme_text_color="Custom",
                text_color=(0.58, 0.64, 0.72, 1),
                size_hint_y=None,
            )
            lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]))
            box.add_widget(lbl)
            self.add_widget(box)

        footer = (popup or {}).get("footer") or ""
        if footer:
            self.add_widget(
                MDLabel(
                    text=footer,
                    font_style="Caption",
                    theme_text_color="Custom",
                    text_color=(0.50, 0.55, 0.62, 1),
                    size_hint_y=None,
                    height="36dp",
                )
            )


class SalesAnalyticsApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics_mode = "all"
        self._metrics_all = None
        self._metrics_paid = None
        self._card_data = {}
        self._metric_cards: dict[str, MetricCard] = {}
        self._popup = None
        self.pe_series = "all"
        self.pe_year = datetime.date.today().year
        self._pe_history: list = []
        self._pe_years: list[int] = []
        self._year_cache: dict = {}
        self._load_token = 0
        self._data_source_note = ""
        self._activity_log: list[str] = []
        self._is_loading = False

    def build(self):
        # Xiaomi 14T / pantallas altas: teclado y densidad mas comodos
        try:
            Window.softinput_mode = "below_target"
            from kivy.utils import platform

            if platform == "android":
                try:
                    from android.permissions import Permission, request_permissions

                    request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE])
                except Exception:
                    pass
        except Exception:
            pass
        if hasattr(self.theme_cls, "material_style"):
            self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "400"
        root = Builder.load_string(kv)
        Clock.schedule_once(lambda dt: self._setup_display(), 0)
        return root

    def _setup_display(self):
        """Safe-area Android + tipografia menu inferior."""
        self._apply_system_insets()
        Clock.schedule_once(lambda dt: self._bump_bottom_nav_fonts(), 0.3)

    def _bump_bottom_nav_fonts(self):
        """Letras del menu inferior un poco mas grandes / legibles."""
        try:
            from kivy.uix.label import Label

            nav = self.root.ids.bottom_nav
            for w in nav.walk():
                if isinstance(w, Label) and (w.text or "").strip():
                    try:
                        if float(w.font_size) < dp(13):
                            w.font_size = dp(13)
                    except Exception:
                        w.font_size = dp(13)
        except Exception:
            pass

    def _apply_system_insets(self):
        """Evita que la barra de navegacion Android tape botones de la app."""
        bottom = dp(18)
        try:
            from kivy.utils import platform

            if platform == "android":
                from jnius import autoclass

                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                activity = PythonActivity.mActivity
                # Preferir layout clasico (contenido no debajo de la nav bar)
                try:
                    WindowCompat = autoclass("androidx.core.view.WindowCompat")
                    WindowCompat.setDecorFitsSystemWindows(activity.getWindow(), True)
                except Exception:
                    pass
                try:
                    resources = activity.getResources()
                    res_id = resources.getIdentifier("navigation_bar_height", "dimen", "android")
                    if res_id > 0:
                        bottom = max(bottom, float(resources.getDimensionPixelSize(res_id)))
                except Exception:
                    bottom = dp(28)
        except Exception:
            bottom = dp(18)
        try:
            col = self.root.ids.main_column
            # padding: left, top, right, bottom
            col.padding = (0, 0, 0, bottom)
        except Exception:
            pass
        self._nav_pad_bottom = bottom


    def open_drawer(self, *_):
        try:
            self.root.ids.nav_drawer.set_state("open")
        except Exception:
            pass

    def set_pe_series(self, series: str):
        # Compat: redirige al interruptor global Todas / Solo pagadas
        self.set_metrics_mode(series)

    def _years_list(self) -> list[int]:
        return pe_history.selectable_years(self._pe_history)

    def shift_pe_year(self, delta: int):
        years = self._years_list()
        if not years:
            return
        cur = self.pe_year if self.pe_year in years else years[0]
        idx = years.index(cur)
        # years descendente: +1 = mas reciente (indice menor)
        new_idx = max(0, min(len(years) - 1, idx - int(delta)))
        self.set_selected_year(years[new_idx])

    def pick_pe_year(self, *_):
        """Lista de años: salto directo (como selector de Windows)."""
        years = self._years_list()
        if not years:
            sb = Snackbar()
            sb.text = "No hay años disponibles"
            sb.open()
            return

        scroll = ScrollView(size_hint_y=None, height="360dp", do_scroll_x=False)
        box = MDBoxLayout(
            orientation="vertical",
            spacing="6dp",
            size_hint_y=None,
            padding="4dp",
        )
        box.bind(minimum_height=box.setter("height"))

        def _make_pick(y):
            def _pick(*_):
                dialog.dismiss()
                self.set_selected_year(int(y))

            return _pick

        today_y = datetime.date.today().year
        for y in years:
            mark = "  · en curso" if y == today_y else ""
            selected = y == self.pe_year
            box.add_widget(
                MDRaisedButton(
                    text=f"{y}{mark}",
                    size_hint_x=1,
                    size_hint_y=None,
                    height="44dp",
                    md_bg_color=(0.08, 0.72, 0.65, 1) if selected else (0.16, 0.22, 0.30, 1),
                    on_release=_make_pick(y),
                )
            )

        scroll.add_widget(box)
        dialog = MDDialog(
            title="Ir a un año",
            type="custom",
            content_cls=scroll,
            buttons=[MDFlatButton(text="Cerrar", on_release=lambda *_: dialog.dismiss())],
        )
        dialog.open()

    def set_selected_year(self, year: int):
        """Cambia el año, va a Resumen y recarga el dashboard."""
        year = int(year)
        years = self._years_list()
        if years:
            year = min(max(year, min(years)), max(years))
        if year == self.pe_year and self._metrics_all is not None and year in self._year_cache:
            self._goto_resumen_tab()
            self._refresh_paid_button_state()
            return
        self.pe_year = year
        # Años cerrados: solo vista Todas (conta = cobrado)
        if year < datetime.date.today().year:
            self.metrics_mode = "all"
            self.pe_series = "all"
        try:
            self.root.ids.year_header.text = f"{year}  v"
        except Exception:
            pass
        self._goto_resumen_tab()
        self.log_activity(f"▸ Cambio de año → {year}")
        # Sin SOAP automatico: solo local/cache; red con ↻
        self.reload_dashboard(force=False, allow_network=False)

    def _paid_allowed(self) -> bool:
        """Solo pagadas tiene sentido en el año en curso (SOAP)."""
        return int(self.pe_year) >= datetime.date.today().year

    def _refresh_paid_button_state(self):
        """Activa/desactiva Solo pagadas segun el año."""
        teal = (0.08, 0.72, 0.65, 1)
        muted = (0.22, 0.26, 0.34, 1)
        disabled = (0.12, 0.14, 0.18, 1)
        try:
            btn = self.root.ids.btn_paid
            if self._paid_allowed():
                btn.disabled = False
                btn.opacity = 1
                btn.md_bg_color = teal if self.metrics_mode == "paid" else muted
                btn.text = "Solo pagadas"
            else:
                self.metrics_mode = "all"
                self.pe_series = "all"
                btn.disabled = True
                btn.opacity = 0.45
                btn.md_bg_color = disabled
                btn.text = "Pagadas (N/D)"
                self.root.ids.btn_all.md_bg_color = teal
        except Exception:
            pass

    def _goto_resumen_tab(self):
        try:
            nav = self.root.ids.bottom_nav
            if hasattr(nav, "switch_tab"):
                nav.switch_tab("resumen")
        except Exception:
            pass

    def log_activity(self, message: str, *, level: str = "info"):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = {"ok": "[ok]", "warn": "[!]", "err": "[x]", "step": "-"}.get(level, "-")
        line = f"{stamp}  {prefix}  {message}"
        self._activity_log.insert(0, line)
        self._activity_log = self._activity_log[:120]
        self._persist_activity_log()
        self._refresh_activity_ui()

    def log_activity_block(self, title: str, lines: list[str]):
        stamp = datetime.datetime.now().strftime("%d-%b %H:%M:%S")
        block = [f"-- {title} · {stamp} --"] + [f"   {ln}" for ln in lines] + [""]
        self._activity_log = block + self._activity_log
        self._activity_log = self._activity_log[:120]
        self._persist_activity_log()
        self._refresh_activity_ui()

    def _persist_activity_log(self):
        try:
            path = apaths.activity_log_path()
            path.write_text(
                json.dumps(self._activity_log, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_activity_log(self):
        try:
            path = apaths.activity_log_path()
            if not path.exists():
                return
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self._activity_log = [str(x) for x in raw][:120]
        except Exception:
            pass

    def _refresh_activity_ui(self):
        try:
            w = self.root.ids.activity_log
            if not self._activity_log:
                w.text = (
                    "Registro de sesion\n\n"
                    "Aqui veras el proceso de carga: fuente (conta/SOAP),\n"
                    "tiempos de red, ventas/PE y cache.\n\n"
                    "Pulsa el icono refresh junto al anio para actualizar."
                )
            else:
                w.text = "\n".join(self._activity_log)
            w.texture_update()
            w.height = max(w.texture_size[1] + 28, 240)
        except Exception:
            pass

    def _trace_ui(self, message: str, level: str = "step"):
        """Desde hilo de fondo: encola mensaje a Actividad."""
        Clock.schedule_once(lambda dt: self.log_activity(message, level=level))

    def exit_app(self, *_):
        self.stop()

    def refresh_data(self, *_):
        """Fuerza recarga del año actual (ignora caché)."""
        if self._is_loading:
            return
        try:
            self.root.ids.nav_drawer.set_state("close")
        except Exception:
            pass
        try:
            self._year_cache.pop(self.pe_year, None)
        except Exception:
            pass
        self._set_loading(True, f"Actualizando {self.pe_year}…")
        self.log_activity(f"Actualizar manual · año {self.pe_year}")
        self.reload_dashboard(force=True, allow_network=True)

    def _set_loading(self, active: bool, message: str = "Actualizando…"):
        self._is_loading = bool(active)
        try:
            row = self.root.ids.loading_row
            spin = self.root.ids.loading_spinner
            banner = self.root.ids.loading_banner
            if active:
                row.height = "28dp"
                row.opacity = 1
                spin.active = True
                banner.text = message
                self.root.ids.mode_subtitle.text = message
            else:
                row.height = "0dp"
                row.opacity = 0
                spin.active = False
                banner.text = ""
        except Exception:
            pass

    def _refresh_pe_year_ui(self):
        try:
            self.root.ids.year_header.text = f"{self.pe_year}  v"
        except Exception:
            pass

    def _redraw_pe_chart(self):
        pe_all = self._metrics_all.breakeven if self._metrics_all else 0.0
        pe_paid = self._metrics_paid.breakeven if self._metrics_paid else 0.0
        series = "paid" if self.metrics_mode == "paid" else "all"
        charts.save_pe_history(
            self._pe_history or [],
            pe_all,
            pe_paid,
            _cpath("chart_pe_hist.png"),
            year=self.pe_year,
            series=series,
        )
        self._reload_image("img_pe", _cpath("chart_pe_hist.png"))

    def set_metrics_mode(self, mode: str):
        if mode == "paid" and not self._paid_allowed():
            sb = Snackbar()
            sb.text = "En años pasados todo se asume cobrado (conta)"
            sb.open()
            mode = "all"
        self.metrics_mode = "paid" if mode == "paid" else "all"
        self.pe_series = self.metrics_mode
        self._refresh_mode_ui()
        self._refresh_paid_button_state()
        self._apply_cards()
        self._refresh_pe_year_ui()
        self._redraw_pe_chart()
    def _tone_color(self, tone):
        if tone == "ok":
            return (0.13, 0.77, 0.37, 1)
        if tone == "bad":
            return (0.94, 0.27, 0.27, 1)
        return (0.89, 0.91, 0.94, 1)

    def _ensure_cards(self):
        box = self.root.ids.cards_box
        if self._metric_cards:
            return
        # grid 2 columnas con filas de BoxLayout
        keys = ["sales", "margin", "daily", "pe", "vs_pe", "net"]
        titles = {
            "sales": "Ventas (real vs PE)",
            "margin": "Márgenes %",
            "daily": "Media diaria (real vs PE)",
            "pe": "Punto de equilibrio",
            "vs_pe": "Vs punto de equilibrio",
            "net": "Resultado neto est.",
        }
        row = None
        for i, key in enumerate(keys):
            if i % 2 == 0:
                row = MDBoxLayout(
                    orientation="horizontal",
                    adaptive_height=True,
                    spacing="10dp",
                    size_hint_y=None,
                    height="126dp",
                )
                box.add_widget(row)
            card = MetricCard(key, titles[key], on_open=self.show_metric_popup, size_hint_x=0.5)
            self._metric_cards[key] = card
            row.add_widget(card)
        hint = MDLabel(
            text="Toca una tarjeta para el desglose · Conta (años cerrados) / SOAP (en curso)",
            font_style="Body2",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.55, 0.60, 0.68, 1),
            size_hint_y=None,
            height="36dp",
        )
        box.add_widget(hint)

    def _apply_cards(self):
        m = self._metrics_paid if self.metrics_mode == "paid" else self._metrics_all
        if m is None:
            return
        payload = metrics.cards_payload(m)
        self._card_data = payload
        for key, card in self._metric_cards.items():
            data = payload[key]
            card.title_lbl.text = data["title"]
            card.line1.text = data["line1"]
            card.line2.text = data["line2"]
            card.line1.text_color = self._tone_color(data.get("tone1"))
            card.line2.text_color = self._tone_color(data.get("tone2"))

    def show_metric_popup(self, key: str):
        data = self._card_data.get(key) or {}
        popup = data.get("popup") or {}
        title = data.get("title") or key
        if self._popup:
            try:
                self._popup.dismiss()
            except Exception:
                pass

        def _close(*_):
            self._popup.dismiss()

        # Compat: si algún popup viejo viniera como texto plano
        if isinstance(popup, str):
            body = MDLabel(
                text=popup,
                size_hint_y=None,
                theme_text_color="Custom",
                text_color=(0.85, 0.88, 0.92, 1),
            )
            body.bind(texture_size=lambda *_: setattr(body, "height", body.texture_size[1] + 20))
            content = body
        else:
            content = MetricPopupBody(popup)

        self._popup = MDDialog(
            title=title,
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="Cerrar", on_release=_close)],
        )
        self._popup.open()

    def show_expense_dialog(self, *_):
        try:
            self.root.ids.nav_drawer.set_state("close")
        except Exception:
            pass

        avg, note = expense.average_expense_last_months(6)
        current = config.get_monthly_expense()
        # Por defecto: media 6 meses si existe; si no, el valor guardado
        initial = avg if avg is not None else current

        box = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
            height="160dp",
            padding="4dp",
        )
        tip = MDLabel(
            text=note if avg is not None else "Sin conta: edita el respaldo manualmente.",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.70, 0.74, 0.80, 1),
            size_hint_y=None,
            height="56dp",
        )
        tf = MDTextField(
            text=f"{float(initial):.2f}",
            hint_text="Gasto mensual (USD)",
            input_filter="float",
            mode="rectangle",
        )
        box.add_widget(tip)
        box.add_widget(tf)

        def use_avg(*_):
            if avg is None:
                sb = Snackbar()
                sb.text = "No hay media de conta disponible"
                sb.open()
                return
            tf.text = f"{avg:.2f}"

        def save(*_):
            try:
                config.save_monthly_expense(float(tf.text))
                dialog.dismiss()
                self.on_start()
                sb = Snackbar()
                sb.text = "Gasto mensual actualizado"
                sb.open()
            except ValueError:
                sb = Snackbar()
                sb.text = "Número inválido"
                sb.open()

        dialog = MDDialog(
            title="Editor de gasto mensual",
            type="custom",
            content_cls=box,
            buttons=[
                MDFlatButton(text="Media 6 meses", on_release=use_avg),
                MDFlatButton(text="Cancelar", on_release=lambda *_: dialog.dismiss()),
                MDRaisedButton(text="Guardar", on_release=save, md_bg_color=(0.08, 0.72, 0.65, 1)),
            ],
        )
        dialog.open()

    def clear_sales_history(self, *_):
        try:
            self.root.ids.nav_drawer.set_state("close")
        except Exception:
            pass

        def confirm(*_):
            import os

            try:
                if os.path.exists("daily_sales_history.json"):
                    os.remove("daily_sales_history.json")
                dialog.dismiss()
                self.on_start()
                sb = Snackbar()
                sb.text = "Puntos del movil borrados (el seed del PC sigue)"
                sb.open()
            except Exception as exc:
                sb = Snackbar()
                sb.text = f"Error: {exc}"
                sb.open()

        dialog = MDDialog(
            title="Borrar puntos del movil",
            text=(
                "Solo elimina lo que esta app guardo al abrirse "
                "(daily_sales_history.json).\n\n"
                "NO borra el historial del PC: data_log ni conta "
                "(pe_history_seed.json). La curva historica seguira visible."
            ),
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(text="Borrar", on_release=confirm),
            ],
        )
        dialog.open()

    def _reload_image(self, widget_id: str, path: str):
        try:
            w = self.root.ids[widget_id]
            w.source = path
            w.reload()
        except Exception:
            pass

    def _reload_tipos_images(self, path_all: str, path_paid: str):
        self._reload_image("img_tipos", path_all)
        self._reload_image("img_tipos_paid", path_paid)

    def _render_bundle_charts(self, year: int, bundle: dict) -> dict:
        """Regenera PNGs del bundle (estilo actual) y devuelve rutas."""
        subtitle = f"{year}"
        vs = _cpath(f"chart_vs_paid_{year}.png")
        tipos_all, tipos_paid = _tipos_paths(year)
        comp = _cpath(f"chart_comportamiento_{year}.png")
        m_all = bundle["m_all"]
        m_paid = bundle.get("m_paid") or m_all
        charts.save_vs_paid(m_all.total_sales, m_paid.total_sales, vs, subtitle)
        charts.save_service_pies(
            bundle.get("services_all") or [],
            bundle.get("services_paid") or [],
            tipos_all,
            subtitle,
        )
        charts.save_behavior_monthly(
            bundle.get("monthly_all") or [],
            bundle.get("monthly_paid") or [],
            comp,
            year,
        )
        bundle["img_vs"] = vs
        bundle["img_tipos"] = tipos_all
        bundle["img_tipos_paid"] = tipos_paid
        bundle["img_comp"] = comp
        return bundle

    def _persist_year_bundle(self, year: int, bundle: dict):
        try:
            year_cache.save_year_bundle(year, bundle)
        except Exception:
            traceback.print_exc()

    def on_start(self):
        # UI inmediata con datos locales; SOAP solo con ↻
        Clock.schedule_once(lambda dt: self._bootstrap_local(), 0)

    def _bootstrap_local(self):
        """Arranque rapido: tarjetas + historial local, sin SOAP automatico."""
        self._setup_display()
        self._ensure_cards()
        self._load_activity_log()
        self._refresh_activity_ui()
        try:
            self._pe_history = pe_history.load_merged_history()
            self._pe_years = pe_history.selectable_years(self._pe_history)
        except Exception:
            self._pe_history = []
            self._pe_years = []
        today = datetime.date.today()
        year = int(self.pe_year or today.year)
        try:
            self.root.ids.year_header.text = f"{year}  v"
            self.root.ids.top_bar.title = f"Sales Analytics  {app_version.APP_VERSION_LABEL}"
        except Exception:
            pass

        # 1) Cache en memoria
        cached = self._year_cache.get(year)
        if cached:
            self._apply_year_bundle(year, cached, from_cache=True)
            try:
                self.root.ids.mode_subtitle.text = (
                    f"Cache local {year}. Toca ↻ para actualizar."
                )
            except Exception:
                pass
            self.log_activity(f"Arranque con cache {year}")
            return

        # 2) Ultimo SOAP/conta guardado en disco (prioridad sobre conta seed)
        disk = year_cache.load_year_bundle(year)
        if disk:
            disk = self._render_bundle_charts(year, disk)
            self._year_cache[year] = disk
            self._apply_year_bundle(year, disk, from_cache=True)
            try:
                self.root.ids.mode_subtitle.text = (
                    f"SOAP guardado {year}. Toca ↻ para actualizar."
                )
            except Exception:
                pass
            self.log_activity(f"Arranque cache disco {year}")
            return

        # 3) Conta empaquetada (offline, inmediata)
        for y in (year, year - 1 if year == today.year else year):
            if self._apply_conta_year_offline(y):
                self.pe_year = y
                try:
                    self.root.ids.year_header.text = f"{y}  v"
                except Exception:
                    pass
                self.log_activity(f"Arranque conta local {y} (sin SOAP)")
                return

        # 3) Sin datos: tarjetas vacias pero visibles
        monthly_expense, _ = expense.resolve_monthly_expense(year)
        empty = metrics.compute_year_metrics(
            total_sales=0.0,
            total_cost=0.0,
            day_of_year=1,
            period_days=365,
            monthly_expense=monthly_expense,
        )
        self._metrics_all = empty
        self._metrics_paid = empty
        self._apply_cards()
        self._refresh_pe_year_ui()
        self._redraw_pe_chart()
        try:
            self.root.ids.mode_subtitle.text = "Listo. Toca ↻ para cargar datos."
            self.root.ids.expense_chip.text = (
                f"Gasto mes: ${monthly_expense:,.2f}  ·  menu > Editar gasto"
            )
        except Exception:
            pass
        self.log_activity("Arranque sin red · espera actualizacion manual")

    def reload_dashboard(self, force: bool = False, allow_network: bool = True):
        """Carga el año seleccionado. Red (SOAP) solo si allow_network=True."""
        today = datetime.date.today()
        year = int(self.pe_year or today.year)

        self._ensure_cards()
        try:
            self.root.ids.year_header.text = f"{year}  v"
            self.root.ids.top_bar.title = f"Sales Analytics  {app_version.APP_VERSION_LABEL}"
        except Exception:
            pass

        cached = None if force else self._year_cache.get(year)
        if cached:
            self._apply_year_bundle(year, cached, from_cache=True)
            return

        if not force:
            disk = year_cache.load_year_bundle(year)
            if disk:
                disk = self._render_bundle_charts(year, disk)
                self._year_cache[year] = disk
                self._apply_year_bundle(year, disk, from_cache=True)
                try:
                    self.root.ids.mode_subtitle.text = (
                        f"SOAP guardado {year}. Toca ↻ para actualizar."
                    )
                except Exception:
                    pass
                return

        if not allow_network:
            if self._apply_conta_year_offline(year):
                return
            monthly_expense, _ = expense.resolve_monthly_expense(year)
            empty = metrics.compute_year_metrics(
                total_sales=0.0,
                total_cost=0.0,
                day_of_year=1,
                period_days=365,
                monthly_expense=monthly_expense,
            )
            self._metrics_all = empty
            self._metrics_paid = empty
            self._apply_cards()
            self._refresh_pe_year_ui()
            self._redraw_pe_chart()
            try:
                self.root.ids.mode_subtitle.text = (
                    f"Sin datos locales {year}. Toca ↻ para cargar."
                )
            except Exception:
                pass
            return

        self._set_loading(True, f"Cargando {year}…")

        self._load_token += 1
        token = self._load_token

        def worker():
            try:
                bundle = self._build_year_bundle(year)
            except Exception as exc:
                traceback.print_exc()
                Clock.schedule_once(lambda dt: self._on_load_error(year, token, str(exc)))
                return
            Clock.schedule_once(lambda dt: self._on_load_ok(year, token, bundle))

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def _apply_conta_year_offline(self, year: int) -> bool:
        """Aplica conta local al año. True si habia datos."""
        try:
            pack = year_data.metrics_from_conta(year)
        except Exception:
            pack = None
        if not pack:
            return False
        m_all, monthly, note = pack
        monthly_expense, _exp_note = expense.resolve_monthly_expense(year)
        tipos_all, tipos_paid = _tipos_paths(year)
        try:
            charts.save_vs_paid(
                m_all.total_sales,
                m_all.total_sales,
                _cpath(f"chart_vs_paid_{year}.png"),
                f"{year} conta",
            )
            charts.save_service_pies([], [], tipos_all, f"{year}")
            charts.save_behavior_monthly(
                monthly, [], _cpath(f"chart_comportamiento_{year}.png"), year
            )
        except Exception:
            traceback.print_exc()
        bundle = {
            "m_all": m_all,
            "m_paid": m_all,
            "monthly_all": monthly,
            "monthly_paid": [],
            "services_all": [],
            "services_paid": [],
            "source_note": f"Conta local · {note}",
            "img_vs": _cpath(f"chart_vs_paid_{year}.png"),
            "img_tipos": tipos_all,
            "img_tipos_paid": tipos_paid,
            "img_comp": _cpath(f"chart_comportamiento_{year}.png"),
            "paid_pending": False,
        }
        self._year_cache[year] = bundle
        self._apply_year_bundle(year, bundle, from_cache=True)
        try:
            self.root.ids.mode_subtitle.text = (
                f"Conta local {year}. Toca ↻ para SOAP / actualizar."
            )
            self.root.ids.expense_chip.text = (
                f"Gasto mes: ${monthly_expense:,.2f}  ·  menu > Editar gasto"
            )
        except Exception:
            pass
        return True

    def _on_load_error(self, year: int, token: int, msg: str):
        if token != self._load_token or year != self.pe_year:
            return
        self._set_loading(False)
        self.log_activity(f"Error cargando {year}: {msg}")
        try:
            self.root.ids.mode_subtitle.text = f"Error {year}: {msg}"
        except Exception:
            pass
        try:
            sb = Snackbar()
            sb.text = f"Error al cargar {year}"
            sb.open()
        except Exception:
            pass

    def _on_load_ok(self, year: int, token: int, bundle: dict):
        if token != self._load_token or year != self.pe_year:
            return
        self._year_cache[year] = bundle
        self._persist_year_bundle(year, bundle)
        self._apply_year_bundle(year, bundle, from_cache=False)

    def _build_year_bundle(self, year: int) -> dict:
        """Trabajo pesado (red/disco). NO tocar UI aqui. Emite traza a Actividad."""
        import time

        t0 = time.perf_counter()
        today = datetime.date.today()
        first_day, last_day, day_of_year, days_in_year = year_data.year_bounds(year)
        subtitle = f"01-01-{year} a 31-12-{year}"
        closed = year < today.year
        steps = []

        def step(msg, level="step"):
            steps.append(msg)
            self._trace_ui(msg, level=level)

        step(f"Inicio carga {year} ({'cerrado' if closed else 'en curso'})")
        step(f"Endpoint SOAP: umbrellatravel.com/PublicServices")

        monthly_all = []
        monthly_paid = []
        services_all = []
        services_paid = []
        paid_pending = False

        def _soap(paid: bool):
            t = time.perf_counter()
            df = metrics.prepare_sales_df(
                fetch_sales_summary(first_day, last_day, only_paid=paid)
            )
            ms = (time.perf_counter() - t) * 1000
            tag = "pagadas" if paid else "todas"
            step(f"SOAP {tag}: {ms:.0f} ms · {len(df)} filas", level="ok")
            return df

        if closed:
            t_c = time.perf_counter()
            conta_pack = year_data.metrics_from_conta(year)
            ms_c = (time.perf_counter() - t_c) * 1000
            if conta_pack is None:
                step("Conta: sin datos → fallback SOAP", level="warn")
                monthly_expense, exp_note = expense.resolve_monthly_expense(year)
                df_all = _soap(False)
                m_all = metrics.compute_year_metrics(
                    total_sales=metrics.sum_column(df_all, metrics.SALES_COLS),
                    total_cost=metrics.sum_column(df_all, metrics.COST_COLS),
                    monthly_expense=monthly_expense,
                    day_of_year=day_of_year,
                    period_days=days_in_year,
                    days_in_year=days_in_year,
                )
                monthly_all = metrics.monthly_sales(df_all)
                services_all = metrics.service_sales(df_all)
                source_note = f"SOAP (sin conta) · {exp_note.split(chr(183))[0].strip()}"
                m_paid = m_all
                paid_pending = True
            else:
                m_all, monthly_all, note = conta_pack
                source_note = note
                step(
                    f"Conta local: {ms_c:.0f} ms · ventas ${m_all.total_sales:,.0f} · "
                    f"PE ${m_all.breakeven:,.0f} (como Windows)",
                    level="ok",
                )
                # Años cerrados: conta = cobrado. No SOAP pagadas (mas rapido).
                m_paid = m_all
                paid_pending = False
                step("Solo pagadas: N/D en años cerrados (se asume cobrado)", level="ok")
                # Tipos / comportamiento: conta no trae desglose → 1 SOAP "todas"
                try:
                    df_all = _soap(False)
                    services_all = metrics.service_sales(df_all)
                    services_paid = services_all
                    soap_monthly = metrics.monthly_sales(df_all)
                    if soap_monthly:
                        monthly_all = soap_monthly
                        monthly_paid = soap_monthly
                    step("SOAP tipos/meses para graficas", level="ok")
                except Exception as exc:
                    step(f"SOAP tipos no disponible: {exc}", level="warn")
        else:
            monthly_expense, exp_note = expense.resolve_monthly_expense(year)
            source_note = f"SOAP en vivo · {exp_note.split(chr(183))[0].strip()}"
            step("Año en curso: 2 llamadas SOAP en paralelo…")
            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_all = pool.submit(_soap, False)
                fut_paid = pool.submit(_soap, True)
                df_all = fut_all.result()
                df_paid = fut_paid.result()
            m_all = metrics.compute_year_metrics(
                total_sales=metrics.sum_column(df_all, metrics.SALES_COLS),
                total_cost=metrics.sum_column(df_all, metrics.COST_COLS),
                monthly_expense=monthly_expense,
                day_of_year=day_of_year,
                period_days=days_in_year,
                days_in_year=days_in_year,
            )
            m_paid = metrics.compute_year_metrics(
                total_sales=metrics.sum_column(df_paid, metrics.SALES_COLS),
                total_cost=metrics.sum_column(df_paid, metrics.COST_COLS),
                monthly_expense=monthly_expense,
                day_of_year=day_of_year,
                period_days=days_in_year,
                days_in_year=days_in_year,
            )
            monthly_all = metrics.monthly_sales(df_all)
            monthly_paid = metrics.monthly_sales(df_paid)
            services_all = metrics.service_sales(df_all)
            services_paid = metrics.service_sales(df_paid)
            step(
                f"Resumen SOAP: Todas ${m_all.total_sales:,.0f} · Pagadas ${m_paid.total_sales:,.0f}",
                level="ok",
            )

        t_g = time.perf_counter()
        tipos_all, tipos_paid = _tipos_paths(year)
        charts.save_vs_paid(
            m_all.total_sales, m_paid.total_sales, _cpath(f"chart_vs_paid_{year}.png"), subtitle
        )
        charts.save_service_pies(
            services_all,
            services_paid,
            tipos_all,
            subtitle,
        )
        charts.save_behavior_monthly(
            monthly_all,
            monthly_paid,
            _cpath(f"chart_comportamiento_{year}.png"),
            year,
        )
        step(f"Graficas: {(time.perf_counter() - t_g) * 1000:.0f} ms", level="ok")
        total_ms = (time.perf_counter() - t0) * 1000
        step(f"Total {year}: {total_ms:.0f} ms", level="ok")

        return {
            "m_all": m_all,
            "m_paid": m_paid,
            "source_note": source_note,
            "monthly_all": monthly_all,
            "monthly_paid": monthly_paid,
            "services_all": services_all,
            "services_paid": services_paid,
            "img_vs": _cpath(f"chart_vs_paid_{year}.png"),
            "img_tipos": tipos_all,
            "img_tipos_paid": tipos_paid,
            "img_comp": _cpath(f"chart_comportamiento_{year}.png"),
            "closed": closed,
            "paid_pending": paid_pending,
            "steps": steps,
            "elapsed_ms": total_ms,
            "day_of_year": day_of_year,
            "days_in_year": days_in_year,
        }

    def _ensure_paid_async(self, year: int):
        """Carga SOAP pagadas en fondo para años cerrados."""
        token = self._load_token
        first_day, last_day, day_of_year, days_in_year = year_data.year_bounds(year)

        def worker():
            import time

            t0 = time.perf_counter()
            try:
                df_paid = metrics.prepare_sales_df(
                    fetch_sales_summary(first_day, last_day, only_paid=True)
                )
                sales = metrics.sum_column(df_paid, metrics.SALES_COLS)
                cost = metrics.sum_column(df_paid, metrics.COST_COLS)
                bundle = self._year_cache.get(year) or {}
                exp = (
                    bundle["m_all"].monthly_expense
                    if bundle.get("m_all")
                    else expense.resolve_monthly_expense(year)[0]
                )
                m_paid = metrics.compute_year_metrics(
                    total_sales=sales,
                    total_cost=cost,
                    monthly_expense=exp,
                    day_of_year=day_of_year,
                    period_days=days_in_year,
                    days_in_year=days_in_year,
                )
                ms = (time.perf_counter() - t0) * 1000
                charts.save_vs_paid(
                    bundle["m_all"].total_sales if bundle.get("m_all") else sales,
                    m_paid.total_sales,
                    _cpath(f"chart_vs_paid_{year}.png"),
                    f"01-01-{year} a 31-12-{year}",
                )
                services_all = bundle.get("services_all") or []
                services_paid = metrics.service_sales(df_paid)
                monthly_all = bundle.get("monthly_all") or []
                monthly_paid = metrics.monthly_sales(df_paid)
                tipos_all, tipos_paid = _tipos_paths(year)
                charts.save_service_pies(
                    services_all,
                    services_paid,
                    tipos_all,
                    f"{year}",
                )
                charts.save_behavior_monthly(
                    monthly_all,
                    monthly_paid,
                    _cpath(f"chart_comportamiento_{year}.png"),
                    year,
                )
                bundle["services_paid"] = services_paid
                bundle["monthly_paid"] = monthly_paid
                bundle["img_tipos"] = tipos_all
                bundle["img_tipos_paid"] = tipos_paid
                bundle["img_vs"] = _cpath(f"chart_vs_paid_{year}.png")
                bundle["img_comp"] = _cpath(f"chart_comportamiento_{year}.png")
                Clock.schedule_once(
                    lambda dt: self._on_paid_ready(year, token, m_paid, ms)
                )
            except Exception as exc:
                Clock.schedule_once(
                    lambda dt: self.log_activity(f"SOAP pagadas fallo: {exc}", level="err")
                )

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def _on_paid_ready(self, year: int, token: int, m_paid, ms: float):
        if token != self._load_token or year != self.pe_year:
            return
        bundle = self._year_cache.get(year)
        if not bundle:
            return
        bundle["m_paid"] = m_paid
        bundle["paid_pending"] = False
        bundle["source_note"] = (bundle.get("source_note") or "") + f" · pagadas SOAP {ms:.0f}ms"
        self._year_cache[year] = bundle
        self._metrics_paid = m_paid
        self._persist_year_bundle(year, bundle)
        self.log_activity(
            f"Pagadas {year}: ${m_paid.total_sales:,.0f} · {ms:.0f} ms",
            level="ok",
        )
        if self.metrics_mode == "paid":
            self._apply_cards()
        self._reload_image("img_vs", bundle["img_vs"])
        self._reload_tipos_images(
            bundle.get("img_tipos") or _tipos_paths(year)[0],
            bundle.get("img_tipos_paid") or _tipos_paths(year)[1],
        )
        self._reload_image("img_comp", bundle["img_comp"])
        self._redraw_pe_chart()

    def _apply_year_bundle(self, year: int, bundle: dict, from_cache: bool = False):
        today = datetime.date.today()
        m_all = bundle["m_all"]
        m_paid = bundle["m_paid"]
        self._metrics_all = m_all
        self._metrics_paid = m_paid
        self._data_source_note = bundle.get("source_note") or ""

        try:
            self.root.ids.expense_chip.text = (
                f"Gasto mes: ${m_all.monthly_expense:,.2f}  ·  menu > Editar gasto"
            )
            self.root.ids.drawer_version.text = app_version.APP_VERSION_LABEL
        except Exception:
            pass

        self._refresh_mode_ui()
        self._apply_cards()
        self._refresh_paid_button_state()
        self._set_loading(False)

        # Historial PE live solo año en curso
        json_file = str(apaths.live_history_path())
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                live = json.load(f)
            if not isinstance(live, list):
                live = []
        except (FileNotFoundError, json.JSONDecodeError):
            live = []

        if year == today.year and not from_cache:
            today_str = today.isoformat()
            updated = False
            for entry in live:
                if entry.get("date") == today_str:
                    entry["all_data_avg"] = round(m_all.daily_avg, 2)
                    entry["paid_only_avg"] = round(m_paid.daily_avg, 2)
                    entry["pe_value"] = round(m_all.breakeven, 2)
                    entry["pe_value_paid"] = round(m_paid.breakeven, 2)
                    entry["source"] = "live"
                    updated = True
                    break
            if not updated:
                live.append(
                    {
                        "date": today_str,
                        "all_data_avg": round(m_all.daily_avg, 2),
                        "paid_only_avg": round(m_paid.daily_avg, 2),
                        "pe_value": round(m_all.breakeven, 2),
                        "pe_value_paid": round(m_paid.breakeven, 2),
                        "source": "live",
                    }
                )
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(live, f, ensure_ascii=False, indent=2)

        history = pe_history.merge_history(pe_history.load_seed_points(), live)
        self._pe_history = history
        self._pe_years = pe_history.selectable_years(history)

        self._refresh_pe_year_ui()
        self._redraw_pe_chart()
        self._reload_image("img_vs", bundle["img_vs"])
        self._reload_tipos_images(
            bundle.get("img_tipos") or _tipos_paths(year)[0],
            bundle.get("img_tipos_paid") or _tipos_paths(year)[1],
        )
        self._reload_image("img_comp", bundle["img_comp"])

        label = "Solo pagadas" if self.metrics_mode == "paid" else "Todas"
        note = self._data_source_note
        try:
            self.root.ids.mode_subtitle.text = (
                f"{label} · {year} · {note}"
                + (" · caché" if from_cache else "")
            )
        except Exception:
            pass

        if not from_cache:
            m = m_all
            lines = [
                f"Fuente: {self._data_source_note}",
                f"Ventas Todas: ${m.total_sales:,.2f}",
                f"Coste: ${m.total_cost:,.2f} · Margen {m.margin_pct:.2f}%",
                f"PE diario: ${m.breakeven:,.2f} · Media ${m.daily_avg:,.2f}",
                f"Neto est.: ${m.net_est:,.2f}",
                f"Tiempo total: {bundle.get('elapsed_ms', 0):.0f} ms",
            ]
            if bundle.get("paid_pending"):
                lines.append("Pagadas: pendientes")
            elif bundle.get("closed"):
                lines.append("Vista única Todas (conta = cobrado en años pasados)")
            self.log_activity_block(f"Año {year} listo", lines)
            try:
                sb = Snackbar()
                sb.text = f"{year} listo"
                sb.open()
            except Exception:
                pass
        else:
            self.log_activity(f"Año {year} desde caché (instantaneo)", level="ok")

    def _refresh_mode_ui(self):
        teal = (0.08, 0.72, 0.65, 1)
        muted = (0.22, 0.26, 0.34, 1)
        try:
            self.root.ids.btn_all.md_bg_color = teal if self.metrics_mode == "all" else muted
            label = "Solo pagadas" if self.metrics_mode == "paid" else "Todas las reservas"
            note = getattr(self, "_data_source_note", "") or "SOAP"
            if not self._paid_allowed():
                label = "Todas (años pasados = cobrado)"
            self.root.ids.mode_subtitle.text = (
                f"{label} · año {self.pe_year} · {note}"
            )
        except Exception:
            pass
        self._refresh_paid_button_state()


if __name__ == "__main__":
    SalesAnalyticsApp().run()
