# Informe del miniproyecto 1

Llene cada sección reemplazando los marcadores `{{...}}`, sin quitar las
secciones. Las cifras salen de lo que imprime `python miniproyecto.py` y las
figuras son las que ese guion deja en `figuras/`. Las fórmulas van en LaTeX
(`$...$` o `$$...$$`).

## 1. La serie

{{Para el desarrollo del miniproyecto se utilizó una serie temporal mensual de ventas minoristas de Estados Unidos, correspondiente al periodo comprendido entre enero de 1992 y diciembre de 2020. La variable representa el comportamiento de las ventas minoristas a lo largo del tiempo y permite estudiar su evolución, tendencia y patrones estacionales.

La serie fue seleccionada porque presenta una frecuencia mensual, un periodo histórico amplio y un comportamiento estacional visible, características que permiten aplicar técnicas de análisis y pronóstico de series temporales, especialmente modelos de la familia SARIMA y SARIMAX.

La serie original contiene 348 observaciones mensuales. Durante la preparación de los datos se identificaron 7 valores faltantes al final del periodo, por lo que la serie utilizada efectivamente por los modelos comprende 341 observaciones, desde enero de 1992 hasta mayo de 2020.

Fuente: U.S. Census Bureau. Dataset "USA Monthly Retail Sales" (https://www.kaggle.com/datasets/landlord/usa-monthly-retail-trade/data)

Licencia: CC0: Public Domain
}}

![La serie](../figuras/serie.png)

{{Se identificaron siete valores faltantes correspondientes a los meses finales de 2020. Debido a que no se contaba con información observada para esos meses, se decidió no imputarlos ni utilizarlos en el entrenamiento y evaluación de los modelos.

Adicionalmente, se aplicó una descomposición STL robusta y el método MAD (desviación absoluta mediana) para identificar posibles valores atípicos. Entre las observaciones detectadas se destacan abril de 2020, marzo de 2020 y mayo de 2020, así como algunos meses de 2008 y 2009.

Estos valores se conservaron en la serie, ya que podrían representar acontecimientos económicos reales y no necesariamente errores de registro. En particular, las variaciones de 2008-2009 esta relaciona a la crisis financiera conocida como la Gran Recesión (Se originó por el colapso de la burbuja inmobiliaria en Estados Unidos, impulsada por las hipotecas subprime (créditos de alto riesgo otorgados a personas con baja capacidad de pago))y 2020 esta relacionada por la pandemia del Covid-19 el cual generó cambios importantes en la actividad económica. Por tanto, se consideró que eliminarlos sin evidencia adicional podría alterar el comportamiento real de las ventas}}

## 2. Componentes

![STL](../figuras/stl.png)

{{La descomposición STL permitió identificar los componentes principales de la serie: tendencia, estacionalidad y residuo.

Tendencia: se observa un crecimiento general de las ventas minoristas de Estados Unidos entre 1992 y 2020. Sin embargo, alrededor de 2008 y 2009 se presenta una disminución temporal, seguida de una recuperación progresiva. Esta variación podría estar relacionada con el contexto de la crisis financiera internacional.

Estacionalidad: se identifica un patrón que se repite anualmente. El mes con mayor efecto estacional es diciembre (mes 12), lo que refleja el incremento de las ventas asociado a la temporada navideña. Por el contrario, febrero (mes 2) presenta el menor efecto estacional, lo que puede estar relacionado con la disminución de las compras después de la temporada de fin de año.

Residuos: representan la variación que no es explicada por la tendencia ni por la estacionalidad. El residuo más negativo fue de aproximadamente -97.178,89 y se presentó en abril de 2020. El residuo más positivo fue de aproximadamente 20.214,25 y ocurrió en febrero de 2020.

El comportamiento de abril de 2020 evidencia una observación considerablemente inferior a la esperada según los componentes de tendencia y estacionalidad. Este comportamiento coincide temporalmente con el impacto inicial de la pandemia sobre la actividad comercial.}}

## 3. Líneas base y backtest

{{Cómo es el backtest: cuántos orígenes, horizonte y qué meses quedan en la
prueba. Por qué ningún dato posterior al origen entra al modelo.}}

{{RMSE, MAE y MAPE del ingenuo y del estacional ingenuo, y cuál gana.}}

## 4. Estacionariedad e identificación

{{Valor p de la prueba ADF para la serie, su diferencia regular, la
estacional y las dos juntas. El d y el D elegidos.}}

![ACF y PACF](../figuras/acf_pacf.png)

{{Qué rezagos salen de las bandas y qué órdenes sugieren.}}

## 5. Modelos clásicos

{{La rejilla de órdenes y su AIC. El modelo elegido, escrito con su
ecuación.}}

![Residuos](../figuras/residuos.png)

{{Diagnóstico de los residuos: Ljung-Box y lo que muestran la gráfica y su
ACF.}}

{{La variable exógena: qué es, por qué se conoce de antemano y si mejora al
SARIMA.}}

## 6. Tabla de métricas

{{Copie aquí `resultados/metricas.csv` como tabla de Markdown, ordenada por
RMSE.}}

| Modelo | Decisión | RMSE | MAE | MAPE (%) |
|---|---|---|---|---|
| {{...}} | {{...}} | {{...}} | {{...}} | {{...}} |

## 7. Conclusión

{{El mejor modelo clásico, cuánto mejora a la mejor línea base en cada
métrica y en qué meses o tramos sigue fallando. Es el modelo que el
miniproyecto 2 debe superar.}}
