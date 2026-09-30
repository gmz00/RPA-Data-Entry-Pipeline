# RPA Pipeline: Automated Data Entry System

Este repositorio contiene un pipeline de Automatización Robótica de Procesos (RPA) desarrollado íntegramente en Python. Su objetivo es automatizar la extracción de datos desde un portal operativo web y su posterior carga en un ERP corporativo (Oracle REIM), eliminando la necesidad de realizar procesos repetitivos de *data entry* manual.

## 1. El Desafío Operativo

En el contexto de las operaciones de Cuentas por Pagar y análisis de datos, el equipo procesa flujos continuos de comprobantes de mercadería. El flujo original requería:

* Extracción visual de datos desde un portal web externo.
* Tipeo manual, campo por campo, en la interfaz del ERP.
* Una dedicación intensiva dentro de la jornada laboral que generaba cuellos de botella para el análisis financiero profundo.
* Alta propensión a errores de tipeo o desajustes contables debido a la fatiga visual generada por la carga secuencial masiva.

## 2. La Solución y Arquitectura

Para resolver este desafío, diseñé una arquitectura modular dividida en dos procesos desacoplados que se comunican mediante archivos de datos estructurados (`.csv`). Se implementó una estrategia de validación en origen: al requerir que los datos se indexen correctamente en el portal web antes de ejecutar el script, se eliminó la propagación de errores humanos hacia el ERP.

La arquitectura se compone de:

1. **Extractor:** Navega el portal operativo, recolecta la información financiera, normaliza las estructuras y exporta un set de datos limpio.
2. **Loader:** Consume los datos estructurados, orquesta el ERP de destino navegando directamente por su DOM, interactúa con ventanas emergentes, desglosa múltiples líneas de impuestos y valida la aprobación final del registro.

## 3. Impacto y Métricas de Negocio

La implementación de este pipeline transformó la jornada operativa diaria, logrando una eficiencia técnica medible y un alto grado de resiliencia frente a las interfaces corporativas.

* **Ahorro de Tiempo Neto:** Esta automatización le devuelve al operador un promedio de **2 a 3 horas productivas por día**. Mientras el pipeline se ejecuta de manera asíncrona y autónoma, el recurso humano queda liberado para realizar tareas financieras paralelas de mayor impacto, como imputaciones contables o gestión de débitos.
* **Velocidad de Procesamiento:** Tras analizar una muestra real de 864 comprobantes a lo largo de 12 lotes de ejecución operativa, el bot demostró tardar un promedio de **49.06 segundos** en orquestar el DOM, calcular impuestos y cargar exitosamente cada documento desde cero.
* **Tasa de Éxito (Resiliencia):** El sistema sostiene una efectividad del **94.56%** en cargas exitosas sin ninguna intervención humana (817 registros consolidados sobre un total de 864).
* **Manejo de Excepciones:** El ~5.4% restante corresponde a desviaciones de negocio detectadas y atrapadas correctamente por el código (ej. inconsistencias de IVA, proveedores no listados, u Órdenes de Compra inhabilitadas). El bot las rechaza, genera un reporte detallado en el log de fallidos para su posterior auditoría, y continúa operando con el siguiente documento.

## 4. Stack Tecnológico

* **Lenguaje:** Python 3
* **Automatización y Orquestación Web:** Playwright (manejo de múltiples contextos, selectores dinámicos, tiempos de espera y estados de red).
* **Procesamiento de Datos:** Pandas, módulo nativo CSV.
* **Calidad y Mantenibilidad:** Pytest (testing automatizado), arquitectura de Logging avanzado (trazabilidad y rotación de archivos).
* **Seguridad:** `python-dotenv` para la inyección segura de credenciales y variables de entorno.

## 5. Documentación Técnica por Módulo

Para revisar los detalles de implementación técnica, arquitectura de código, patrones de diseño aplicados y manuales de ejecución, por favor dirigirse a la documentación específica de cada módulo en este *monorepo*:

* 📖 [Módulo Extractor - Documentación Técnica y Configuración](https://github.com/gmz00/RPA-Data-Entry-Pipeline/blob/main/extractor/README.md)
* 📖 [Módulo Loader - Documentación Técnica y Configuración](https://github.com/gmz00/RPA-Data-Entry-Pipeline/blob/main/loader/README.md)