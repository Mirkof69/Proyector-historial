"""
=============================================================================
GRAFICOS ESTADISTICOS — FETAL MEDICAL BOLIVIA
=============================================================================
Genera graficos para el analisis de Investigacion de Operaciones.
Requiere: matplotlib, numpy (pip install matplotlib numpy)
=============================================================================
"""

import os
import statistics

# Intentar importar matplotlib
try:
    import matplotlib
    matplotlib.use("Agg")  # Backend sin GUI para generacion de archivos
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False
    print("matplotlib no disponible. Instalar: pip install matplotlib")

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "resultados", "graficos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def grafico_comparacion_modelos(modelos_data):
    """Grafico de barras comparando metricas de los 3 modelos CNN."""
    if not MATPLOTLIB_OK:
        print("  [SKIP] grafico_comparacion_modelos — matplotlib no disponible")
        return

    metricas = ["sensibilidad", "especificidad", "auc_roc", "f1_score", "kappa_cohen", "accuracy"]
    labels = ["Sensibilidad", "Especificidad", "AUC-ROC", "F1-Score", "Kappa", "Accuracy"]
    colores = ["#2196F3", "#4CAF50", "#FF5722"]
    nombres_modelos = ["A: EfficientNet-B4", "B: DenseNet-121", "C: ResNet50+Att"]
    umbrales = [0.92, 0.85, 0.90, 0.85, 0.75, 0.88]

    fig, ax = plt.subplots(figsize=(14, 7))
    x = list(range(len(metricas)))
    ancho = 0.22

    for i, (clave, color, nombre) in enumerate(zip(["A", "B", "C"], colores, nombres_modelos)):
        vals = [modelos_data[clave]["metricas"][m] for m in metricas]
        offset = (i - 1) * ancho
        barras = ax.bar([xi + offset for xi in x], vals, ancho, label=nombre, color=color, alpha=0.85, edgecolor="white")

        for barra, val in zip(barras, vals):
            ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 0.005,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    # Lineas de umbral
    for xi, umbral in zip(x, umbrales):
        ax.hlines(umbral, xi - 0.35, xi + 0.35, colors="red", linewidths=1.5, linestyles="--", alpha=0.7)

    ax.set_xlim(-0.5, len(metricas) - 0.5)
    ax.set_ylim(0.5, 1.02)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Valor de metrica", fontsize=11)
    ax.set_title("Comparacion de Metricas — 3 Modelos CNN\nFetal Medical Bolivia — UNIFRANZ 2026",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.axhline(y=0.92, color="red", linewidth=0.5, linestyle=":", alpha=0.4)
    ax.text(len(metricas) - 0.3, 0.921, "Umbral Sens. 0.92", fontsize=7, color="red", alpha=0.7)

    linea_umbral = mpatches.Patch(color="red", linestyle="--", label="Umbral clinico", alpha=0.7)
    handles, labels_leg = ax.get_legend_handles_labels()
    ax.legend(handles + [linea_umbral], labels_leg + ["Umbral clinico"], loc="lower right", fontsize=9)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "1_comparacion_modelos_cnn.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_radar_modelos(modelos_data):
    """Grafico radar (spider) con metricas normalizadas de los 3 modelos."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    metricas = ["sensibilidad", "especificidad", "auc_roc", "f1_score", "kappa_cohen", "accuracy"]
    labels = ["Sensibilidad", "Especificidad", "AUC-ROC", "F1-Score", "Kappa\nCohen", "Accuracy"]
    colores = ["#2196F3", "#4CAF50", "#FF5722"]

    N = len(metricas)
    angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8), subplot_kw=dict(polar=True))

    for i, (clave, color) in enumerate(zip(["A", "B", "C"], colores)):
        vals = [modelos_data[clave]["metricas"][m] for m in metricas]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", color=color, linewidth=2, label=modelos_data[clave]["nombre"])
        ax.fill(angles, vals, color=color, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0.6, 1.0)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["0.7", "0.8", "0.9", "1.0"], fontsize=8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    ax.set_title("Perfil de Metricas — Modelos CNN\n(Grafico Radar)", fontsize=12, fontweight="bold", pad=20)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "2_radar_modelos_cnn.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_distribucion_patologias(datos):
    """Grafico de torta con distribucion de patologias."""
    if not MATPLOTLIB_OK:
        return

    conteos = {}
    for d in datos:
        pat = d["patologia_real"]
        conteos[pat] = conteos.get(pat, 0) + 1

    ordenados = sorted(conteos.items(), key=lambda x: -x[1])
    etiquetas = [k.replace("_", "\n") for k, _ in ordenados]
    valores = [v for _, v in ordenados]
    colores = plt.cm.Set3.colors[:len(valores)]

    fig, ax = plt.subplots(figsize=(12, 8))
    wedges, texts, autotexts = ax.pie(
        valores, labels=etiquetas, autopct="%1.1f%%",
        colors=colores, startangle=90, pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.5)
    )

    for autotext in autotexts:
        autotext.set_fontsize(8)
    for text in texts:
        text.set_fontsize(8)

    ax.set_title(
        f"Distribucion de Patologias en Dataset Obstetrico\n"
        f"N={sum(valores)} registros — Fetal Medical Bolivia",
        fontsize=12, fontweight="bold"
    )

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "3_distribucion_patologias.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_riesgo_edad(datos):
    """Scatter: edad vs nivel de riesgo con color por patologia."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    riesgo_num = {"bajo": 1, "moderado": 2, "alto": 3, "muy_alto": 4}
    colores_pat = {
        "normal": "#4CAF50", "preeclampsia": "#F44336", "rciu": "#FF9800",
        "oligohidramnios": "#2196F3", "polihidramnios": "#9C27B0",
        "placenta_previa": "#FF5722", "diabetes_gestacional": "#00BCD4",
        "anemia_severa": "#795548", "amenaza_parto_prematuro": "#607D8B",
        "embarazo_multiple": "#E91E63"
    }

    fig, ax = plt.subplots(figsize=(12, 7))

    patologias_vistas = set()
    for d in datos:
        color = colores_pat.get(d["patologia_real"], "#999999")
        jitter = np.random.normal(0, 0.08)
        y_val = riesgo_num[d["nivel_riesgo"]] + jitter
        label = d["patologia_real"] if d["patologia_real"] not in patologias_vistas else None
        ax.scatter(d["edad_anios"], y_val, c=color, alpha=0.6, s=25, label=label)
        patologias_vistas.add(d["patologia_real"])

    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["Bajo", "Moderado", "Alto", "Muy Alto"])
    ax.set_xlabel("Edad de la paciente (anos)", fontsize=11)
    ax.set_ylabel("Nivel de riesgo obstétrico", fontsize=11)
    ax.set_title("Distribucion Edad vs Riesgo por Patologia\nFetal Medical Bolivia — N=500", fontsize=12, fontweight="bold")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, title="Patologia")
    ax.axvline(x=35, color="red", linestyle="--", alpha=0.5, linewidth=1.5)
    ax.text(35.5, 4.1, "Edad avanzada\n(>=35 anos)", fontsize=8, color="red")

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "4_edad_vs_riesgo.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_biometria_distribucion(datos):
    """Histogramas de biometria fetal."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    vars_bio = [
        ("bpd_mm", "BPD — Diametro Biparietal (mm)"),
        ("hc_mm", "HC — Circunferencia Cefalica (mm)"),
        ("ac_mm", "AC — Circunferencia Abdominal (mm)"),
        ("fl_mm", "FL — Longitud Femoral (mm)"),
    ]
    colores = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]

    for (campo, titulo), ax, color in zip(vars_bio, axes.flat, colores):
        vals = [d[campo] for d in datos]
        ax.hist(vals, bins=30, color=color, alpha=0.75, edgecolor="white")
        media = statistics.mean(vals)
        de = statistics.stdev(vals)
        ax.axvline(media, color="red", linewidth=2, linestyle="--", label=f"Media={media:.1f}")
        ax.axvline(media - de, color="orange", linewidth=1.5, linestyle=":", label=f"-1DE={media-de:.1f}")
        ax.axvline(media + de, color="orange", linewidth=1.5, linestyle=":", label=f"+1DE={media+de:.1f}")
        ax.set_title(titulo, fontsize=10, fontweight="bold")
        ax.set_xlabel("mm", fontsize=9)
        ax.set_ylabel("Frecuencia", fontsize=9)
        ax.legend(fontsize=8)

    fig.suptitle("Distribucion de Biometria Fetal — Dataset Obstetrico\nN=500 pacientes", fontsize=13, fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "5_biometria_distribucion.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_tiempo_analisis_cnn(datos):
    """Histograma del tiempo de analisis CNN con comparacion de modelos."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    tiempos = [d["tiempo_analisis_ms"] for d in datos]
    t_modelo_a = 1450
    t_modelo_b = 890
    t_modelo_c = 1100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(tiempos, bins=40, color="#2196F3", alpha=0.75, edgecolor="white", label="Simulacion Modelo A")

    ax.axvline(t_modelo_a, color="#2196F3", linewidth=2.5, linestyle="--", label=f"A: EfficientNet-B4 ({t_modelo_a}ms)")
    ax.axvline(t_modelo_b, color="#4CAF50", linewidth=2.5, linestyle="--", label=f"B: DenseNet-121 ({t_modelo_b}ms)")
    ax.axvline(t_modelo_c, color="#FF9800", linewidth=2.5, linestyle="--", label=f"C: ResNet50+Att ({t_modelo_c}ms)")
    ax.axvline(3000, color="red", linewidth=2, linestyle="-", alpha=0.8, label="Limite clinico (3000ms)")

    media_t = statistics.mean(tiempos)
    ax.text(media_t + 30, ax.get_ylim()[1] * 0.7, f"Media={media_t:.0f}ms", fontsize=9, color="#2196F3")

    ax.set_xlabel("Tiempo de analisis (ms)", fontsize=11)
    ax.set_ylabel("Frecuencia", fontsize=11)
    ax.set_title("Distribucion del Tiempo de Analisis CNN\nComparacion de 3 Modelos", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "6_tiempo_analisis_cnn.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_curva_roc_simulada(modelos_data):
    """Curvas ROC simuladas para los 3 modelos."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    fig, ax = plt.subplots(figsize=(9, 8))

    colores = {"A": "#2196F3", "B": "#4CAF50", "C": "#FF5722"}

    for clave, color in colores.items():
        m = modelos_data[clave]
        auc = m["metricas"]["auc_roc"]
        sens = m["metricas"]["sensibilidad"]
        espec = m["metricas"]["especificidad"]

        # Generar curva ROC aproximada pasando por el punto de operacion
        fpr_op = 1 - espec
        tpr_op = sens

        # Puntos de la curva (simplificacion de curva ROC)
        fpr = np.array([0, 0.02, fpr_op * 0.5, fpr_op, fpr_op * 1.5, 0.5, 0.8, 1.0])
        tpr_base = np.array([0, 0.4, 0.7, tpr_op, tpr_op + 0.02, 0.96, 0.99, 1.0])
        tpr_base = np.clip(tpr_base, 0, 1)

        ax.plot(fpr, tpr_base, "-", color=color, linewidth=2.5,
                label=f"{m['nombre']} (AUC={auc:.3f})")
        ax.plot(fpr_op, tpr_op, "o", color=color, markersize=10)

    # Diagonal de referencia
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.5, label="Clasificador aleatorio (AUC=0.5)")
    ax.axhline(0.92, color="red", linestyle=":", linewidth=1.5, alpha=0.6, label="Sensibilidad minima (0.92)")

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel("Tasa de Falsos Positivos (1 - Especificidad)", fontsize=11)
    ax.set_ylabel("Tasa de Verdaderos Positivos (Sensibilidad)", fontsize=11)
    ax.set_title("Curvas ROC — Comparacion de Modelos CNN\n(Aproximacion basada en metricas clinicas)", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "7_curvas_roc.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_cpm_gantt(fases_data, rc_data):
    """Diagrama de Gantt con ruta critica."""
    if not MATPLOTLIB_OK or not NUMPY_OK:
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    fases = list(fases_data.items())
    n = len(fases)
    criticas = set(rc_data["critica"])

    for i, (fase_id, info) in enumerate(fases):
        es = rc_data["es"][fase_id]
        ef = rc_data["ef"][fase_id]
        color = "#F44336" if fase_id in criticas else "#2196F3"
        barra = ax.barh(i, ef - es, left=es, color=color, alpha=0.8, edgecolor="white", height=0.6)
        ax.text(es + (ef - es) / 2, i, f"{info['nombre'][:20]}", ha="center", va="center",
                fontsize=7.5, color="white", fontweight="bold")
        ax.text(ef + 0.05, i, f"H={rc_data['holgura'][fase_id]:.1f}", ha="left", va="center", fontsize=8, color="gray")

    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{fid}: {info['nombre'][:25]}" for fid, info in fases], fontsize=9)
    ax.set_xlabel("Semanas desde inicio", fontsize=11)
    ax.set_title("Diagrama Gantt — Ruta Critica del Proyecto\n(Rojo = Ruta Critica, Azul = Con holgura)",
                 fontsize=12, fontweight="bold")
    ax.axvline(rc_data["duracion_total_semanas"], color="black", linestyle="--", linewidth=1.5, alpha=0.5)
    ax.text(rc_data["duracion_total_semanas"] + 0.1, n - 0.5,
            f"{rc_data['duracion_total_semanas']:.0f} sem", fontsize=9)

    critico_patch = mpatches.Patch(color="#F44336", label="Ruta Critica (holgura=0)")
    libre_patch = mpatches.Patch(color="#2196F3", label="Con holgura")
    ax.legend(handles=[critico_patch, libre_patch], loc="lower right", fontsize=10)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "8_gantt_ruta_critica.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def grafico_colas_comparacion(escenarios_colas):
    """Grafico comparando Wq (tiempo de espera en cola) por escenario."""
    if not MATPLOTLIB_OK:
        return

    nombres = [e["escenario"] for e in escenarios_colas if e["wq_min"] is not None]
    wq_vals = [e["wq_min"] for e in escenarios_colas if e["wq_min"] is not None]
    colores = ["#4CAF50" if w < 2 else ("#FF9800" if w < 5 else "#F44336") for w in wq_vals]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(nombres)), wq_vals, color=colores, alpha=0.85, edgecolor="white")

    for barra, val in zip(bars, wq_vals):
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 0.05,
                f"{val:.2f}min", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.axhline(2, color="green", linewidth=2, linestyle="--", alpha=0.7, label="Optimo (<2 min)")
    ax.axhline(5, color="orange", linewidth=2, linestyle="--", alpha=0.7, label="Limite aceptable (<5 min)")

    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Tiempo promedio de espera en cola (minutos)", fontsize=11)
    ax.set_title("Teoria de Colas M/M/c — Wq por Escenario\nFetal Medical Bolivia", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)

    verde_patch = mpatches.Patch(color="#4CAF50", label="Optimo (Wq<2min)")
    naranja_patch = mpatches.Patch(color="#FF9800", label="Aceptable (2-5 min)")
    rojo_patch = mpatches.Patch(color="#F44336", label="Critico (>5 min)")
    handles, lbls = ax.get_legend_handles_labels()
    ax.legend(handles + [verde_patch, naranja_patch, rojo_patch],
              lbls + ["Optimo", "Aceptable", "Critico"], loc="upper left", fontsize=9)

    plt.tight_layout()
    ruta = os.path.join(OUTPUT_DIR, "9_teoria_colas_wq.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Guardado: {ruta}")


def generar_todos_los_graficos(modelos_data, datos_pacientes, fases_proyecto, rc_data, escenarios_colas):
    """Genera todos los graficos estadisticos."""
    print("\n" + "=" * 78)
    print("GENERANDO GRAFICOS ESTADISTICOS")
    print("=" * 78)

    if not MATPLOTLIB_OK:
        print("\n  [!] matplotlib no instalado. Instalar con:")
        print("      pip install matplotlib numpy")
        print("  Los graficos no se generaran pero el analisis numerico es completo.")
        return

    print(f"\n  Graficos guardados en: {OUTPUT_DIR}/\n")
    grafico_comparacion_modelos(modelos_data)
    grafico_radar_modelos(modelos_data)
    grafico_distribucion_patologias(datos_pacientes)
    grafico_riesgo_edad(datos_pacientes)
    grafico_biometria_distribucion(datos_pacientes)
    grafico_tiempo_analisis_cnn(datos_pacientes)
    grafico_curva_roc_simulada(modelos_data)
    grafico_cpm_gantt(fases_proyecto, rc_data)
    grafico_colas_comparacion(escenarios_colas)

    print(f"\n  Total: 9 graficos generados en {OUTPUT_DIR}/")


if __name__ == "__main__":
    # Ejecutar integrado con modelo_matematico.py
    from modelo_matematico import MODELOS_CNN, FASES_PROYECTO, calcular_ruta_critica
    from modelo_matematico import generar_paciente_sintetico, teoria_de_colas_mmc

    print("Generando dataset sintetico...")
    datos = [generar_paciente_sintetico(i) for i in range(500)]

    print("Calculando ruta critica...")
    rc = calcular_ruta_critica()

    print("Calculando colas...")
    escenarios = [
        {"escenario": "Normal 1GPU", "lambda": 10, "mu": 20, "c": 1},
        {"escenario": "Normal 2GPUs", "lambda": 10, "mu": 20, "c": 2},
        {"escenario": "Pico 1GPU", "lambda": 18, "mu": 20, "c": 1},
        {"escenario": "Pico 2GPUs", "lambda": 18, "mu": 20, "c": 2},
        {"escenario": "Critico 2GPUs", "lambda": 25, "mu": 20, "c": 2},
        {"escenario": "Critico 3GPUs", "lambda": 25, "mu": 20, "c": 3},
    ]
    resultados_colas = []
    for e in escenarios:
        resultado, _ = teoria_de_colas_mmc(e["lambda"], e["mu"], e["c"])
        if resultado:
            resultados_colas.append({**e, "wq_min": resultado["Wq_minutos"]})
        else:
            resultados_colas.append({**e, "wq_min": None})

    generar_todos_los_graficos(MODELOS_CNN, datos, FASES_PROYECTO, rc, resultados_colas)
