"""Miniproyecto 1: la serie del grupo, de las líneas base al mejor modelo clásico.

Se corre de principio a fin con

    python miniproyecto.py

y deja las figuras en figuras/ y la tabla en resultados/metricas.csv. Las
partes marcadas con TODO las completa el grupo; mientras falten, el guion las
reporta como pendientes y sigue. El informe, docs/informe.md, cita las cifras
y las figuras que produce este guion.
"""
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from comun import (RAIZ, backtest, cargar_serie, estacional_ingenuo,  # noqa: E402
                   fechas_siguientes, ingenuo)

warnings.filterwarnings("ignore")
FIGURAS = RAIZ / "figuras"
RESULTADOS = RAIZ / "resultados"
FIGURAS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

# ============================================================
# 1. La serie
# ============================================================
# Cambie estos cuatro datos por los de la serie del grupo y documente la
# fuente en datos/README.md. La serie de ejemplo solo sirve para probar que
# el guion corre.
ARCHIVO = "datos/SeriesReport-Not Seasonally Adjusted Sales - Monthly (Millions of Dollars).csv"
FECHA = "Period"
VALOR = "Value"
PERIODO = 12

# Lo que se hizo con los huecos y con los datos atípicos, en una línea. Va
# a la columna `decision` de la tabla de métricas.
DECISION = (
    "Se eliminaron los meses de junio a diciembre de 2020 por valores faltantes "
    "al final de la serie; no se identificaron atípicos extremos adicionales."
)

def preparar(serie):
    """Aplique la decisión del grupo sobre huecos y datos atípicos.

    Por ejemplo, interpolar los meses vacíos o recortar el tramo afectado.
    Debe devolver una serie sin NaN.
    """
    serie = serie.dropna()
    return serie


def graficar_serie(serie):
    figura, eje = plt.subplots(figsize=(9, 3.4))
    eje.plot(serie.index, serie.to_numpy())
    eje.set_title(f"{VALOR}: serie mensual")
    eje.set_ylabel(VALOR)
    figura.tight_layout()
    figura.savefig(FIGURAS / "serie.png", dpi=120)
    plt.close(figura)


# ============================================================
# 2. Descomposición
# ============================================================

def descomponer(serie):
    """STL robusta con el periodo de la serie; guarde figuras/stl.png."""
    stl = STL(
        serie,
        period=PERIODO,
        robust=True
    ).fit()

    # estadísticas para el informe

    componente_estacional = stl.seasonal.groupby(
        stl.seasonal.index.month
    ).mean()

    mes_max = componente_estacional.idxmax()
    mes_min = componente_estacional.idxmin()

    residuo_max = stl.resid.max()
    residuo_min = stl.resid.min()

    fecha_residuo_max = stl.resid.idxmax()
    fecha_residuo_min = stl.resid.idxmin()

    figura = stl.plot()
    figura.set_size_inches(10, 8)

    # Residuo máximo
    figura.axes[3].scatter(
        fecha_residuo_max,
        stl.resid.max(),
        color="red",
        s=100,
        label="Residuo máximo"
    )

    # Residuo mínimo
    figura.axes[3].scatter(
        fecha_residuo_min,
        stl.resid.min(),
        color="darkred",
        s=100,
        label="Residuo mínimo"
    )

    figura.axes[3].legend()

    plt.tight_layout()
    plt.savefig(FIGURAS / "stl.png", dpi=120)
    plt.close()

    print("\n=== STL ===")
    print("Mes estacional más alto:", mes_max)
    print("Mes estacional más bajo:", mes_min)
    print("Residuo máximo:", residuo_max)
    print("Residuo mínimo:", residuo_min)
    print("Fecha residuo máximo:", fecha_residuo_max)
    print("Fecha residuo mínimo:", fecha_residuo_min)


def detectar_atipicos(serie):
    """
    Detecta posibles valores atípicos mediante los residuos
    de una descomposición STL robusta.
    """
    stl = STL(
        serie,
        period=PERIODO,
        robust=True
    ).fit()

    residuos = stl.resid.dropna()

    # MAD: desviación absoluta mediana
    mediana = residuos.median()
    mad = np.median(np.abs(residuos - mediana))

    if mad == 0:
        print("No fue posible calcular el umbral MAD.")
        return pd.DataFrame()

    # Puntaje robusto
    z_robusto = 0.6745 * (residuos - mediana) / mad

    atipicos = pd.DataFrame({
        "valor_original": serie.loc[residuos.index],
        "tendencia": stl.trend.loc[residuos.index],
        "estacionalidad": stl.seasonal.loc[residuos.index],
        "residuo": residuos,
        "z_robusto": z_robusto
    })

    # Umbral habitual para señalar observaciones candidatas
    atipicos = atipicos[
        atipicos["z_robusto"].abs() > 3.5
    ].copy()

    print("\n=== POSIBLES VALORES ATÍPICOS ===")

    if atipicos.empty:
        print("No se detectaron observaciones con |z robusto| > 3.5.")
    else:
        print(atipicos.sort_values(
            "z_robusto",
            key=abs,
            ascending=False
        ).to_string())

    return atipicos


# ============================================================
# 3. Estacionariedad e identificación
# ============================================================
def comparar_d_D(serie):

    escenarios = [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1)
    ]

    filas = []

    for d, D in escenarios:

        print(f"\nProbando d={d}, D={D}")

        orden, estacional = elegir_sarima(
            serie,
            d,
            D
        )

        metricas = fila(
            f"SARIMA{orden}{estacional}",
            serie,
            modelo_sarima(
                orden,
                estacional
            )
        )

        filas.append({
            "d": d,
            "D": D,
            "modelo": f"SARIMA{orden}{estacional}",
            "RMSE": metricas["RMSE"],
            "MAE": metricas["MAE"],
            "MAPE": metricas["MAPE"]
        })

    tabla = pd.DataFrame(filas)

    tabla = tabla.sort_values("RMSE")

    print("\n=== Comparación d y D ===")
    print(tabla.to_string(index=False))

    tabla.to_csv(
        RESULTADOS / "comparacion_d_D.csv",
        index=False
    )

    return tabla

def estacionariedad(serie):
    """ADF sobre la serie, su diferencia regular, la estacional y las dos.

    Imprima el valor p de cada versión, elija d y D, y guarde la ACF y la
    PACF de la serie elegida en figuras/acf_pacf.png. Devuelva (d, D).
    """
    serie_original = serie.dropna()

    diff_regular = serie_original.diff().dropna()

    diff_estacional = serie_original.diff(12).dropna()

    diff_ambas = (
        serie_original
        .diff()
        .diff(12)
        .dropna()
    )

    print("\n=== ADF ===")

    p_original = adfuller(
        serie_original,
        regression="ct"
    )[1]

    p_regular = adfuller(
        diff_regular,
        regression="c"
    )[1]

    p_estacional = adfuller(
        diff_estacional,
        regression="c"
    )[1]

    p_ambas = adfuller(
        diff_ambas,
        regression="c"
    )[1]

    print(f"Serie original: {p_original:.5f}")
    print(f"Diferencia regular: {p_regular:.5f}")
    print(f"Diferencia estacional: {p_estacional:.5f}")
    print(f"Regular + estacional: {p_ambas:.5f}")

    #d = 1 if p_original > 0.05 else 0
    #D = 1 if p_estacional < 0.05 else 0
    d=0
    D=1
    
    if d == 0 and D == 0:
        serie_modelo = serie_original
    elif d == 1 and D == 0:
        serie_modelo = diff_regular
    elif d == 0 and D == 1: #modelo elegido utiliza solamente diferenciación estacional
        serie_modelo = diff_estacional 
    else:
        serie_modelo = diff_ambas #serie con diferenciación regular y estacional

    figura, ejes = plt.subplots(
        2,
        1,
        figsize=(10, 7)
    )

    plot_acf(
        serie_modelo,
        lags=48,
        ax=ejes[0]
    )

    ejes[0].set_title("ACF")

    plot_pacf(
        serie_modelo,
        lags=48,
        ax=ejes[1],
        method="ywm"
    )

    ejes[1].set_title("PACF")

    plt.tight_layout()

    plt.savefig(
        FIGURAS / "acf_pacf.png",
        dpi=120
    )

    plt.close()

    print(f"\nd elegido = {d}")
    print(f"D elegido = {D}")

    return d, D


# ============================================================
# 4. Modelos clásicos
# ============================================================
# Cada modelo es una función modelo(entrenamiento, h) que devuelve h
# pronósticos y solo usa `entrenamiento`. Así entra al backtest común.

def elegir_sarima(serie, d, D):
    """rejilla pequeña de órdenes (p, q, P, Q) comparada por AIC.

    Ajuste con toda la serie preparada, imprima la tabla de AIC, revise los
    residuos del elegido con Ljung-Box y guarde figuras/residuos.png.
    Devuelva el orden y el orden estacional elegidos.
    """
    p_vals = [0, 1, 2]
    q_vals = [0, 1, 2]

    P_vals = [0, 1]
    Q_vals = [0, 1]

    resultados = []

    for p in p_vals:
        for q in q_vals:
            for P in P_vals:
                for Q in Q_vals:

                    try:
                        modelo = SARIMAX(
                            serie,
                            order=(p,d,q),
                            seasonal_order=(P,D,Q,12),
                            enforce_stationarity=True,
                            enforce_invertibility=True
                        )

                        ajuste = modelo.fit(disp=False)

                        if not ajuste.mle_retvals.get("converged", False):
                            continue

                        if not np.isfinite(ajuste.aic):
                            continue

                        if abs(ajuste.llf) < 1:
                            continue

                        resultados.append({
                            "p": p,
                            "q": q,
                            "P": P,
                            "Q": Q,
                            "AIC": ajuste.aic,
                            "BIC": ajuste.bic,
                            "LLF": ajuste.llf
                        })

                    except:
                        pass

    tabla = (
        pd.DataFrame(resultados)
        .sort_values("AIC")
    )

    print("\n=== Rejilla SARIMA ===")
    print(tabla.head(10))

    mejor = tabla.iloc[0]

    orden = (
        int(mejor["p"]),
        d,
        int(mejor["q"])
    )

    estacional = (
        int(mejor["P"]),
        D,
        int(mejor["Q"]),
        12
    )

    print("\nMejor modelo:")
    print("order =", orden)
    print("seasonal_order =", estacional)

    modelo_final = SARIMAX(
        serie,
        order=orden,
        seasonal_order=estacional,
        enforce_stationarity=True,
        enforce_invertibility=True
    )

    ajuste_final = modelo_final.fit(disp=False)

    print("\n=== Mejor modelo completo ===")
    print(ajuste_final.summary())

    lb = acorr_ljungbox(
        ajuste_final.resid,
        lags=[12, 24,36],
        return_df=True
    )

    print("\nModelo para Ljung-Box:")
    print("order =", orden)
    print("seasonal_order =", estacional)

    print("\n=== Ljung-Box ===")
    print(lb)

    figura, eje = plt.subplots(figsize=(10,4))

    eje.plot(ajuste_final.resid)

    print("\n=== Estadísticas residuos ===")
    print(ajuste_final.resid.describe())

    eje.axhline(
        0,
        color="red",
        linestyle="--"
    )

    eje.set_title("Residuos del modelo SARIMA")

    plt.tight_layout()

    plt.savefig(
        FIGURAS / "residuos.png",
        dpi=120
    )

    plt.close()

    return orden, estacional


def modelo_sarima(orden, orden_estacional):
    """devuelva la función modelo(entrenamiento, h) del SARIMA elegido."""
    def modelo(entrenamiento, h):

        try:

            ajuste = SARIMAX(
                entrenamiento,
                order=orden,
                seasonal_order=orden_estacional,
                enforce_stationarity=True,
                enforce_invertibility=True
            ).fit(disp=False)

            return ajuste.forecast(steps=h)

        except Exception:

            return estacional_ingenuo(
                entrenamiento,
                h,
                PERIODO
            )

    return modelo


def exogenas(serie):
    """DataFrame de variables conocidas de antemano, con el índice de la serie.

    Por ejemplo, el número de festivos o de días hábiles de cada mes. Debe
    cubrir también los 12 meses que siguen al final de la serie.
    """
    inicio = serie.index.min()
    fin = serie.index.max() + pd.DateOffset(months=12)

    fechas = pd.date_range(
        start=inicio,
        end=fin,
        freq="MS"
    )

    dias_habiles = []

    for fecha in fechas:
        fin_mes = fecha + pd.offsets.MonthEnd(0)

        cantidad = len(pd.date_range(
            start=fecha,
            end=fin_mes,
            freq="B"
        ))

        dias_habiles.append(cantidad)

    x = pd.DataFrame(
        {"dias_habiles": dias_habiles},
        index=fechas
    )

    return x


def modelo_sarimax(orden, orden_estacional, x):
    """devuelva modelo(entrenamiento, h) de un SARIMAX con exógenas x.

    Use x.loc[entrenamiento.index] para ajustar y
    x.loc[fechas_siguientes(entrenamiento, h)] para pronosticar.
    """
    def modelo(entrenamiento, h):
        fechas_futuras = fechas_siguientes(entrenamiento, h)

        x_entrenamiento = x.loc[entrenamiento.index]
        x_futuro = x.loc[fechas_futuras]

        ajuste = SARIMAX(
            entrenamiento,
            exog=x_entrenamiento,
            order=orden,
            seasonal_order=orden_estacional,
            enforce_stationarity=True,
            enforce_invertibility=True
        ).fit(disp=False)

        pronostico = ajuste.forecast(
            steps=h,
            exog=x_futuro
        )

        return pronostico.to_numpy()

    return modelo



def evaluar_residuos_sarimax(serie, orden, orden_estacional, x):
    """Evalúa los residuos del SARIMAX ajustado con toda la serie."""

    # Ajustar el SARIMAX con toda la serie
    ajuste = SARIMAX(
        serie,
        exog=x.loc[serie.index],
        order=orden,
        seasonal_order=orden_estacional,
        enforce_stationarity=True,
        enforce_invertibility=True
    ).fit(disp=False)

    # Obtener los residuos
    residuos = ajuste.resid.dropna()

    print("\n=== EVALUACIÓN DE RESIDUOS SARIMAX ===")
    print(residuos.describe())

    # Prueba de Ljung-Box
    lb = acorr_ljungbox(
        residuos,
        lags=[12, 24, 36],
        return_df=True
    )

    print("\n=== LJUNG-BOX SARIMAX ===")
    print(lb)

    # Gráfica de residuos
    figura, eje = plt.subplots(figsize=(10, 4))
    eje.plot(residuos)
    eje.axhline(0, color="red", linestyle="--")
    eje.set_title("Residuos del modelo SARIMAX")
    eje.set_xlabel("Fecha")
    eje.set_ylabel("Residuo")

    plt.tight_layout()
    plt.savefig(FIGURAS / "residuos_sarimax.png", dpi=120)
    plt.close()

    # ACF de los residuos
    figura, eje = plt.subplots(figsize=(10, 4))
    plot_acf(residuos, lags=36, ax=eje)
    eje.set_title("ACF de los residuos SARIMAX")

    plt.tight_layout()
    plt.savefig(FIGURAS / "acf_residuos_sarimax.png", dpi=120)
    plt.close()

    return lb

# ============================================================
# 5. La tabla de métricas
# ============================================================

def fila(nombre, serie, modelo):
    _, promedio = backtest(serie, modelo)
    return {"modelo": nombre, "decision": DECISION,
            "RMSE": round(promedio["RMSE"], 2), "MAE": round(promedio["MAE"], 2),
            "MAPE": round(promedio["MAPE"], 2)}


def pendiente(parte, error):
    print(f"  pendiente: {parte} ({error})")


def main():
    cruda = cargar_serie(ARCHIVO, FECHA, VALOR)
    print(f"Serie: {len(cruda)} meses, de {cruda.index[0]:%Y-%m} a "
          f"{cruda.index[-1]:%Y-%m}, {cruda.isna().sum()} vacíos")
    serie = preparar(cruda)

    atipicos = detectar_atipicos(serie)
    atipicos.to_csv( RESULTADOS / "posibles_atipicos.csv")
    comparar_d_D(serie)


    graficar_serie(serie)

    filas = [fila("ingenuo", serie, ingenuo),
             fila("estacional ingenuo", serie,
                  lambda t, h: estacional_ingenuo(t, h, PERIODO))]

    try:
        descomponer(serie)
    except NotImplementedError as error:
        pendiente("parte 2", error)

    try:
        d, D = estacionariedad(serie)
    except NotImplementedError as error:
        pendiente("parte 3", error)
        d = D = None

    if d is not None:
        try:
            orden, estacional = elegir_sarima(serie, d, D)
            filas.append(fila(f"SARIMA{orden}{estacional}", serie,
                              modelo_sarima(orden, estacional)))
            x = exogenas(serie)
            filas.append(fila(f"SARIMAX{orden}{estacional} + exógenas", serie,
                              modelo_sarimax(orden, estacional, x)))

            # Evaluar los residuos del SARIMAX
            evaluar_residuos_sarimax(serie, orden, estacional, x)
        except NotImplementedError as error:
            pendiente("parte 4", error)

    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(RESULTADOS / "metricas.csv", index=False)
    print(tabla.drop(columns="decision").to_string(index=False))
    print("Mejor modelo por RMSE:", tabla.iloc[0]["modelo"])


if __name__ == "__main__":
    main()
