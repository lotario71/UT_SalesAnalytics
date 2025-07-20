from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.carousel import MDCarousel
import requests  # Para llamadas HTTP
import xml.etree.ElementTree as ET  # Para procesar SOAP XML

import datetime
import config   

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar

# ─── Plotting Support ──────────────────────────────
import matplotlib
matplotlib.use("Agg")  # use non-GUI backend for saving plots
import matplotlib.pyplot as plt



from kivymd.uix.navigationdrawer import (
    MDNavigationLayout,
    MDNavigationDrawer,
    MDNavigationDrawerMenu,
    MDNavigationDrawerHeader,
    MDNavigationDrawerItem
)

import json
import pandas as pd

# >>> DIAGNÓSTICO: Escribir log al arrancar <<<
try:
    with open("arranque_android.txt", "w") as f:
        f.write("main.py ejecutado\n")
except Exception as e:
    pass
# <<< FIN DIAGNÓSTICO <<<



def fetch_sales_summary(from_date, to_date, only_paid=False, first_level_client_id=None):
    """
    Obtiene datos de ventas mediante el servicio SOAP
    GetServicesSalesStatistics y devuelve un DataFrame de pandas.
    """
    
    # Endpoint SOAP
    url = "https://www.umbrellatravel.com/Services/PublicServices.svc"

    # ─── Etiqueta de cliente opcional ───────────────────────────────────
    first_level_tag = (
        f"<firstLevelClientId>{first_level_client_id}</firstLevelClientId>"
        if first_level_client_id not in (None, "")
        else ""
    )

    # Construye el sobre SOAP
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
        "SOAPAction": "\"http://tempuri.org/IPublicServices/GetServicesSalesStatistics\""
    }

    # Envía la petición
    response = requests.post(url, headers=headers, data=envelope)
    response.raise_for_status()


    # Procesa la respuesta XML
    ns = {
        "s": "http://schemas.xmlsoap.org/soap/envelope/",
        "t": "http://tempuri.org/"
    }
    root = ET.fromstring(response.text)
    # ─── Recorremos todos los bloques de resultados ─────────────────────
    # ─── Recolectar TODOS los nodos «…TotalSalesStatisticsDto» ───────────
    records = []
    for item in root.iter():
        if item.tag.endswith("TotalSalesStatisticsDto"):
            record = {}
            for child in item:
                key = child.tag.split('}')[-1]          # quita el namespace
                record[key] = child.text
            records.append(record)

    df = pd.DataFrame(records)



    return pd.DataFrame(records)




class MainScreen(MDScreen):
    """Root screen for the app."""
    pass


# --- Baseline KV layout -------------------------------------------------
kv = """
#:import MDTopAppBar kivymd.uix.toolbar.MDTopAppBar

MDNavigationLayout:

    ScreenManager:

        MainScreen:
            name: "main"

            MDBoxLayout:
                orientation: "vertical"

                AnchorLayout:
                    anchor_x: "left"
                    anchor_y: "top"
                    size_hint_y: None
                    height: "48dp"

                    MDIconButton:
                        icon: "menu"
                        pos_hint: {"center_y": 0.5}
                        on_release: nav_drawer.set_state("open")

                MDCarousel:
                    id: sales_carousel
                    loop: False
                    swipe_distance: "20dp"

                    # ───────────────────── Slide 1 ──────────────────────
                    MDScreen:
                        AnchorLayout:
                            anchor_x: "center"
                            anchor_y: "center"

                            MDBoxLayout:
                                orientation: "vertical"
                                spacing: "8dp"
                                padding: "0dp"
                                size_hint_x: .9
                                size_hint_y: None
                                adaptive_height: True

                                MDLabel:
                                    id: year_header_all
                                    text: "2025"
                                    font_style: "H4"
                                    halign: "center"
                                    theme_text_color: "Primary"

                                Widget:
                                    size_hint_y: None
                                    height: "8dp"

                                MDCard:
                                    elevation: 2
                                    radius: 12
                                    padding: "12dp"
                                    spacing: "8dp"
                                    orientation: "vertical"
                                    size_hint_x: 1
                                    size_hint_y: None
                                    adaptive_height: True
                                    md_bg_color: app.theme_cls.bg_light

                                    MDLabel:
                                        id: subheader_all
                                        text: "Resultados para All Data:"
                                        font_style: "Subtitle1"
                                        halign: "center"

                                    Widget:
                                        size_hint_y: None
                                        height: "8dp"

                                    MDLabel:
                                        id: metrics_all
                                        text: "Cargando métricas..."
                                        halign: "center"
                                        theme_text_color: "Secondary"
                                        markup: True
                                        size_hint_y: None
                                        height: self.texture_size[1]

                    # ───────────────────── Slide 2 ──────────────────────
                    MDScreen:
                        AnchorLayout:
                            anchor_x: "center"
                            anchor_y: "center"

                            MDBoxLayout:
                                orientation: "vertical"
                                spacing: "8dp"
                                padding: "0dp"
                                size_hint_x: .9
                                size_hint_y: None
                                adaptive_height: True

                                MDLabel:
                                    id: year_header_paid
                                    text: "2025"
                                    font_style: "H4"
                                    halign: "center"
                                    theme_text_color: "Primary"

                                Widget:
                                    size_hint_y: None
                                    height: "16dp"

                                MDCard:
                                    elevation: 2
                                    radius: 12
                                    padding: "12dp"
                                    spacing: "8dp"
                                    orientation: "vertical"
                                    size_hint_x: 1
                                    size_hint_y: None
                                    adaptive_height: True
                                    md_bg_color: app.theme_cls.bg_light

                                    MDLabel:
                                        id: subheader_paid
                                        text: "Reservas Pagadas"
                                        font_style: "Subtitle1"
                                        halign: "center"

                                    Widget:
                                        size_hint_y: None
                                        height: "8dp"

                                    MDLabel:
                                        id: metrics_paid
                                        text: "Cargando métricas..."
                                        halign: "center"
                                        theme_text_color: "Secondary"
                                        markup: True
                                        size_hint_y: None
                                        height: self.texture_size[1]

                    # ───────────────────── Slide 3 ──────────────────────
                    MDScreen:
                        name: "slide_graph"

                        AnchorLayout:
                            anchor_x: "center"
                            anchor_y: "center"

                            Image:
                                id: graph_image
                                source: "plot.png"
                                allow_stretch: True
                                keep_ratio: True
                                size_hint: 0.95, 0.95


                    # ───────────────────── Slide 4 ──────────────────────
                    MDScreen:
                        name: "slide_daily_sales"

                        AnchorLayout:
                            anchor_x: "center"
                            anchor_y: "center"

                            Image:
                                id: daily_sales_image
                                source: "daily_sales_plot.png"
                                allow_stretch: True
                                keep_ratio: True
                                size_hint: 0.95, 0.95




    # ──────────── Navigation Drawer (Menu) ─────────────
    MDNavigationDrawer:
        id: nav_drawer
        width: 320  # You can adjust this value if still not enough!


        MDNavigationDrawerMenu:

            MDNavigationDrawerHeader:
                title: "Sales Analytics"
                title_color: app.theme_cls.primary_color
                padding: "16dp"
                spacing: "4dp"

            MDNavigationDrawerItem:
                icon: "cash"
                text: "Set Average Monthly Expense"
                on_release: app.show_expense_dialog()
                max_text_lines: 2
                divider: None

            MDNavigationDrawerItem:
                icon: "delete"
                text: "Clear Daily Sales History"
                on_release: app.clear_sales_history()
                max_text_lines: 2
                divider: None

            MDNavigationDrawerItem:
                icon: "exit-to-app"
                text: "Salir"
                on_release: app.exit_app()
                max_text_lines: 2
                divider: None



"""
# -----------------------------------------------------------------------


class SalesAnalyticsApp(MDApp):
    """Main application class."""



    def clear_sales_history(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        def confirm_clear(*_):
            import os
            json_file = "daily_sales_history.json"
            try:
                if os.path.exists(json_file):
                    os.remove(json_file)
                self.on_start()  # Refresh all metrics and charts
                self.root.ids.nav_drawer.set_state("close")  # Close the menu
                snackbar = Snackbar()
                snackbar.text = "Historial de ventas diarias eliminado."
                snackbar.open()


                
            except Exception as e:
                import traceback
                print("ERROR while clearing sales history:", e)
                traceback.print_exc()
                snackbar = Snackbar()
                snackbar.text = f"Error: {e}"
                snackbar.open()
            dialog.dismiss()

        def cancel(*_):
            dialog.dismiss()

        dialog = MDDialog(
            title="¿Borrar historial?",
            text="¿Estás seguro que deseas borrar el historial de ventas diarias? Esta acción no se puede deshacer.",
            buttons=[
                MDFlatButton(text="Cancelar", on_release=cancel),
                MDFlatButton(text="Borrar", on_release=confirm_clear)
            ]
        )
        dialog.open()



    def build_daily_sales_chart(self):
        import matplotlib.dates as mdates

        json_file = "daily_sales_history.json"

        # Load data from JSON
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        if not history:
            print("No daily sales history to plot.")
            return

        # Prepare lists for plotting
        dates = []
        all_data = []
        paid_only = []

        for entry in sorted(history, key=lambda x: x["date"]):
            dates.append(datetime.datetime.fromisoformat(entry["date"]))
            all_data.append(entry.get("all_data_avg", 0))
            paid_only.append(entry.get("paid_only_avg", 0))

        fig, ax = plt.subplots(figsize=(8, 5))

        # Preparar listas históricas
        pe_values = [entry.get("pe_value", 0) for entry in history]

        if any(all_data):
            ax.plot(dates, all_data, marker="o", linestyle="-", color="blue", label="Promedio Todas las Reservas")
        if any(paid_only):
            ax.plot(dates, paid_only, marker="o", linestyle="-", color="teal", label="Promedio Solo Pagadas")
        if any(pe_values):
            ax.plot(dates, pe_values, marker="o", linestyle="--", color="green", label="Punto de Equilibrio (PE)")

        # Ajustar el rango del eje X solo al rango de tus datos
        if dates:
            ax.set_xlim(min(dates), max(dates))

        ax.set_title("Historial de Ventas Diarias")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Venta Promedio Diaria (USD)")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()

        ax.grid(True)
        ax.legend()

        plt.tight_layout()
        fig.savefig("daily_sales_plot.png", dpi=160)
        plt.close(fig)



    def build_sales_plot(self, all_avg, paid_avg, break_even_value, date_label):
        """Modern 2-bar chart with green PE line and paid % inside bar."""
        fig, ax = plt.subplots(figsize=(6, 4))

        labels = ["All Data", "Only Paid"]
        values = [all_avg, paid_avg]
        colors = ["#1976D2", "#009688"]  # Blue, Teal

        bars = ax.bar(labels, values, color=colors, width=0.6)

        # Bar labels above
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + max(values) * 0.03,
                    f"${val:,.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

        # Percentage inside "Only Paid" bar
        if all_avg > 0:
            pct = paid_avg / all_avg * 100
            bar = bars[1]  # second bar = Only Paid
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 0.5,
                    f"{pct:.1f}%", ha="center", va="center",
                    fontsize=12, fontweight="bold", color="white")

        # Green PE line
        ax.axhline(break_even_value, color="green", linestyle="--", linewidth=2, label="Punto de Equilibrio")
        ax.text(1.1, break_even_value + max(values) * 0.01, f"${break_even_value:,.2f}",
                color="green", fontsize=10, va="bottom")

        ax.set_ylim(0, max(max(values), break_even_value) * 1.25)
        ax.set_ylabel("USD")
        ax.set_title(f"Venta diaria vs PE (ALL DATA) – {date_label}", fontsize=14, fontweight="bold", pad=15)
        ax.legend(loc="upper right", frameon=False)

        plt.tight_layout()
        fig.savefig("plot.png", dpi=160)
        plt.close(fig)



    def build(self):
        # ── Modern Material style (use M3 when available) ────────────────
        if hasattr(self.theme_cls, "material_style"):
            self.theme_cls.material_style = "M3"

        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.primary_hue     = "600"
        self.theme_cls.theme_style     = "Light"

        # ----------------------------------------------------------------
        # Always build and return the root widget
        # ----------------------------------------------------------------
        root = Builder.load_string(kv)
        return root

    # -------------------------------------------------------------------
    # Load today's sales summary and display the total value
    # -------------------------------------------------------------------



    # ──────────────────────────────────────────────────────────────
    # Pop-up to edit the monthly fixed expense
    # ──────────────────────────────────────────────────────────────
    def show_expense_dialog(self, *args):
        print("GEAR-TAP")   # ← appears in console every time icon is tapped

        
        cur_value = config.get_monthly_expense()

        tf = MDTextField(
            text=f"{cur_value:.2f}",
            hint_text="Gasto mensual (USD)",
            input_filter="float",
            mode="rectangle",
        )

        def save_callback(*_):
            try:
                new_val = float(tf.text)
                config.save_monthly_expense(new_val)
                self.on_start()                 # recalc all metrics

                self.root.ids.nav_drawer.set_state("close")  # 👈 closes the drawer
                dialog.dismiss()                             # 👈 closes the dialog earlier

                from kivymd.uix.snackbar import Snackbar
                snackbar = Snackbar()
                snackbar.text = "Gasto mensual actualizado"
                snackbar.open()

            except ValueError:
                from kivymd.uix.snackbar import Snackbar
                snackbar = Snackbar()
                snackbar.text = "Número inválido"
                snackbar.open()

        dialog = MDDialog(
            title="Editar gasto mensual",
            type="custom",
            content_cls=tf,
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda *_: (
                        dialog.dismiss(),
                        self.root.ids.nav_drawer.set_state("close")  # 👈 also close drawer
                    )
                ),


                MDFlatButton(text="Guardar",  on_release=save_callback),
            ],
        )
        dialog.open()


    def on_start(self):
        today      = datetime.date.today()
        first_day  = datetime.date(today.year, 1, 1)
        last_day   = datetime.date(today.year, 12, 31)


        df = fetch_sales_summary(first_day, last_day)

        # --- DEBUG: show columns and first rows in the console -----------
        print("DEBUG → DataFrame columns:", list(df.columns))
        print("DEBUG → First 5 rows:\n", df.head())

        # -----------------------------------------------------------------

        # Try a few likely column names
        candidate_cols = ["TotalPrice", "TotalSales", "Total", "SalesTotal", "Importe"]
        total = 0
        for col in candidate_cols:
            if col in df.columns:
                total = df[col].astype(float).sum()
                break

        # ── Update first slide (“Todas las Reservas”) ────────────────────
        # ────────────────────────────  Headers  ──────────────────────────
        self.root.ids.year_header_all.text = str(today.year)
        self.root.ids.subheader_all.text   = "Resultados para All Data:"
        # (label removed from the layout – no action needed here)


        # ─────────────────────  Metric calculations  ─────────────────────
        day_of_year   = today.timetuple().tm_yday
        daily_avg     = total / day_of_year if day_of_year else 0


        total_cost    = df["TotalCost"].astype(float).sum()


        # --- monthly fixed cost from config.py ---------------------------
        monthly_expense = config.get_monthly_expense()   # e.g. 8900.00

        # Windows rounds the margin to 2 decimals first
        gp_raw            = (1 - total_cost / total) * 100 if total else 0.01
        gross_margin_pct  = round(gp_raw, 2)

        # Windows formula: (monthly expense ÷ GP%) ÷ 30 days
        break_even    = (monthly_expense / (gross_margin_pct / 100)) / 30


        # Build chart data for Slide 3
        dates = [today.replace(day=d) for d in range(1, day_of_year + 1) if d <= 28 or d <= today.day]
        daily_averages = [daily_avg for _ in dates]



        diff_be       = daily_avg - break_even
        diff_color    = "00C853" if diff_be >= 0 else "E53935"   # green / red

        predicted_sales  = daily_avg * 365
        gross_profit_est = predicted_sales * gross_margin_pct / 100

        expenses_total   = monthly_expense * 12          # full-year fixed costs
        net_result_est   = gross_profit_est - expenses_total
        net_color        = "00C853" if net_result_est >= 0 else "E53935"



        # ── DEBUG: print the raw sums to the console ─────────────────────
        print("DEBUG → total_price  :", total)          # sales total
        print("DEBUG → total_cost   :", total_cost)     # cost total
        print("DEBUG → day_of_year  :", day_of_year)
        print("DEBUG → monthly_exp  :", monthly_expense)
        # ----------------------------------------------------------------


        # ─────────────────────  Formatted output  ────────────────────────
        metrics_text = (
            f"[b]Ventas Totales:[/b] ${total:,.2f}\n"
            f"[b]Número del Día del Año:[/b] {day_of_year}\n"
            f"[b]Venta Promedio Diaria:[/b] ${daily_avg:,.2f}\n"
            f"[b]Venta diaria para punto de equilibrio:[/b] ${break_even:,.2f}\n"
            f"[color=#{diff_color}][b]Diferencia con el punto de equilibrio:[/b] "
            f"{diff_be:+,.2f}[/color]\n\n"
            f"[b]Predicción de Ventas Totales para el Año:[/b] ${predicted_sales:,.2f}\n"
            f"[b]Porcentaje de Ganancia Bruta Promedio:[/b] {gross_margin_pct:.2f}%\n"
            f"[b]Ganancia Bruta Estimada:[/b] ${gross_profit_est:,.2f}\n"
            f"[b]Gastos Totales estimados:[/b] ${expenses_total:,.2f}\n"
            f"[color=#{net_color}][b]Resultado Neto Estimado para el Año:[/b] "
            f"{net_result_est:+,.2f}[/color]"
        )

        self.root.ids.metrics_all.text = metrics_text


        # -----------------------------------------------------------------

        # ─────────────────────  «Reservas Pagadas» slide  ─────────────────
        paid_df = fetch_sales_summary(first_day, last_day, only_paid=True)

        paid_total      = paid_df["TotalPrice"].astype(float).sum()
        paid_total_cost = paid_df["TotalCost"].astype(float).sum()

        # Same day-count and monthly expense
        paid_daily_avg  = paid_total / day_of_year if day_of_year else 0

        gp_raw_paid         = (1 - paid_total_cost / paid_total) * 100 if paid_total else 0.01
        gross_margin_paid   = round(gp_raw_paid, 2)

        paid_break_even = (monthly_expense / (gross_margin_paid / 100)) / 30
        paid_diff_be    = paid_daily_avg - paid_break_even
        paid_diff_color = "00C853" if paid_diff_be >= 0 else "E53935"

        paid_pred_sales    = paid_daily_avg * 365
        paid_gross_profit  = paid_pred_sales * gross_margin_paid / 100
        paid_net_result    = paid_gross_profit - expenses_total
        paid_net_color     = "00C853" if paid_net_result >= 0 else "E53935"

        # --- update widgets ------------------------------------------------
        self.root.ids.year_header_paid.text = str(today.year)
        self.root.ids.subheader_paid.text   = "Resultados para Only Paid:"

        metrics_paid_text = (
            f"[b]Ventas Totales:[/b] ${paid_total:,.2f}\n"
            f"[b]Número del Día del Año:[/b] {day_of_year}\n"
            f"[b]Venta Promedio Diaria:[/b] ${paid_daily_avg:,.2f}\n"
            f"[b]Venta diaria para punto de equilibrio:[/b] ${paid_break_even:,.2f}\n"
            f"[color=#{paid_diff_color}][b]Diferencia con el punto de equilibrio:[/b] "
            f"{paid_diff_be:+,.2f}[/color]\n\n"
            f"[b]Predicción de Ventas Totales para el Año:[/b] ${paid_pred_sales:,.2f}\n"
            f"[b]Porcentaje de Ganancia Bruta Promedio:[/b] {gross_margin_paid:.2f}%\n"
            f"[b]Ganancia Bruta Estimada:[/b] ${paid_gross_profit:,.2f}\n"
            f"[b]Gastos Totales estimados:[/b] ${expenses_total:,.2f}\n"
            f"[color=#{paid_net_color}][b]Resultado Neto Estimado para el Año:[/b] "
            f"{paid_net_result:+,.2f}[/color]"
        )

        
        self.root.ids.metrics_paid.text = metrics_paid_text

        # ← Ahora que ya existe paid_daily_avg, sí puedes construir la gráfica:
        self.build_sales_plot(daily_avg, paid_daily_avg, break_even, today.strftime("%Y-%m-%d"))


        json_file = "daily_sales_history.json"
        today_str = datetime.date.today().isoformat()

        # Load existing history
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        # Actualizar o agregar registro para hoy
        updated = False
        for entry in history:
            if entry["date"] == today_str:
                entry["all_data_avg"] = round(daily_avg, 2)
                entry["paid_only_avg"] = round(paid_daily_avg, 2)
                entry["pe_value"] = round(break_even, 2)
                updated = True
                break
        if not updated:
            history.append({
                "date": today_str,
                "all_data_avg": round(daily_avg, 2),
                "paid_only_avg": round(paid_daily_avg, 2),
                "pe_value": round(break_even, 2)
            })
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


        self.build_daily_sales_chart()

        # Forzar recarga de la imagen de la gráfica (por si es la primera vez)
        if hasattr(self.root.ids, "daily_sales_image"):
            self.root.ids.daily_sales_image.reload()



        # -----------------------------------------------------------------

    def exit_app(self, *args):
        import sys
        from kivy.app import App
        App.get_running_app().stop()
        sys.exit()



if __name__ == "__main__":
    SalesAnalyticsApp().run()
