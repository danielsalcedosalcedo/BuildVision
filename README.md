# 🏗️ BuildVision AI · Medición de Avance Físico con Visión Computacional

**Diplomado en Inteligencia Artificial Aplicada a la Industria AEC**  
**Entrega Grupal - Hito 02**  
**Grupo 15:** Diego Avella · Patricia Luna · Daniel Salcedo  
**Caso Ancla del MVP:** Red de rociadores contra incendio (*sprinklers*, NFPA 13)

---

## 📋 Resumen del Proyecto y Contexto

El avance físico de obra en la industria de la construcción habitualmente se estima visualmente, de forma subjetiva y mediante fotografías dispersas en mensajería, lo que retrasa y debilita los reportes semanales. 

**BuildVision AI** resuelve esta problemática mediante una aplicación web de terreno para el **Inspector Técnico de Obra (ITO)**:
1. Fotografía los vanos o sectores de obra.
2. Un modelo de visión computacional (**Ultralytics YOLO**) detecta 5 clases clave de la red contra incendio.
3. El sistema calcula un porcentaje de avance sugerido contrastando las detecciones contra el plan de unidades por zona (CSV).
4. El ITO revisa, aprueba o corrige con pocos toques (**Human-in-the-Loop - HITL**: *"La IA propone; la persona decide"*).
5. Se emite un reporte semanal ejecutivo en **PDF** con evidencia fotográfica auditada, semáforos de desviación y trazabilidad inmutable.

---

## 🎨 Implementación y Mejoras del Punto 7 (UX/UI)

El prototipo implementa y mejora sustancialmente las **cuatro pantallas clave del wireframe** (Figura 5 del informe):

| Pantalla Wireframe | Nombre en App | Mejoras e Implementación Técnica Realizada |
| :--- | :--- | :--- |
| **(a) Subir Fotos** | `BuildVision · Subir` | • Selector jerárquico de Proyecto, Nivel y Vano/Zona.<br/>• **Control de Calidad Automático (RF-02):** evaluación de resolución ($\ge 8$ MP / 1280 px) y análisis de nitidez mediante varianza del operador Laplaciano.<br/>• **Simulador de Resiliencia sin Conexión (CP-01):** cola de almacenamiento local que retiene fotos en sótanos/obras sin señal.<br/>• Carga directa por archivo, cámara del dispositivo o 1-click preset del **Caso Dorado CP-05**. |
| **(b) Revisión HITL** | `Revisión 2 de 8 (HITL)` | • Superposición visual de **bounding boxes** de YOLO con semáforo de confianza tricolor ($\ge 0.80$ verde, $0.40 - 0.79$ ámbar, $< 0.40$ rojo).<br/>• Conteo discriminado de las 5 clases: rociadores instalados, tapones de rociador (salidas pendientes), tramos de tubería, soportes y válvula de control.<br/>• **Ergonomía de terreno:** botones táctiles amplios ($\ge 48$ px) ubicados al alcance del pulgar:<br/>  - `Aprobar Verdes (en bloque)`: aprueba detecciones confiables en 1 toque.<br/>  - `Corregir / Revisar ⚠`: ajuste manual de cantidades con recálculo dinámico en tiempo real.<br/>  - `Rechazar Foto (repetir)`.<br/>• **Botón "Deshacer" (CP-07):** revierte ajustes accidentales.<br/>• **Registro de Auditoría (Trazabilidad G):** bitácora inmutable de quién, qué, cuándo y valores antes/después. |
| **(c) Panel de Avance** | `Avance · Nivel 4` | • **KPI Global:** Avance real consolidado (**80.4%**) vs Plan semanal (**85.0%**), brecha de $-4.6$ pp.<br/>• **Semáforo de Desviaciones (RF-07):** alertas automáticas amarillas ($\ge 5$ pp) y rojas críticas ($\ge 10$ pp), destacando el caso de alerta en Vano E-F ($-22.0$ pp).<br/>• Barras de avance comparativo por vano (C-D, D-E, E-F, F-G, G-H).<br/>• Alerta de cobertura parcial (CP-06) y filtro de vanos con fotos pendientes de revisión.<br/>• Panel interactivo para auditar y recalibrar los pesos de ponderación ($w_1$ a $w_5$). |
| **(d) Reporte Semanal** | `Reporte Semanal · Sem. 42` | • Encabezado oficial con datos de obra, partida e ITO.<br/>• Indicador de completitud: `8/8 fotos revisadas ✓ Sin pendientes`.<br/>• **Generador de Reporte PDF Oficial (RF-08):** genera y descarga un PDF real maquetado con ReportLab con tablas de avance, desviaciones y evidencia.<br/>• Opciones de compartir y firmas de conformidad técnica del ITO y Administrador de Obra. |

---

## 📐 Modelo Matemático de Cálculo (Sección 5 y CP-05)

La conversión de detecciones al avance de una zona $z$ se rige por:

$$p(c, z) = \min\left(\frac{n(c, z)}{N(c, z)},\, 1.0\right)$$

$$A(z) = \sum_{c} w(c) \cdot p(c, z)$$

### Caso Dorado Validado (CP-05 · Vano C-D):
| Componente | Peso $w$ | Validado $\div$ Plan | Ratio $p(c,z)$ | Aporte $w \cdot p$ |
| :--- | :---: | :---: | :---: | :---: |
| **Tubería (tramos)** | 0.45 | 12 $\div$ 12 | 1.000 | 0.4500 |
| **Soportes y Colgadores** | 0.15 | 14 $\div$ 18 | 0.778 | 0.1167 |
| **Rociadores Instalados** | 0.30 | 15 $\div$ 24 | 0.625 | 0.1875 |
| **Válvula de Control** | 0.05 | 1 $\div$ 1 | 1.000 | 0.0500 |
| **Prueba Hidráulica (manual)** | 0.05 | 0 $\div$ 1 | 0.000 | 0.0000 |
| **Avance Total Vano C-D $A(z)$** | **1.00** | — | — | **80.4%** |

*El sistema reproduce de forma exacta el valor de **80.4%** del documento, validado con prueba unitaria automática.*

---

## 🚀 Instrucciones de Instalación y Ejecución

### 1. Requisitos Previos
Tener instalado Python 3.10 o superior (compatible con Python 3.14).

### 2. Instalación de Dependencias
En la carpeta del proyecto, ejecute:
```bash
pip install -r requirements.txt
```
*(Librerías utilizadas: `streamlit`, `pillow`, `numpy`, `pandas`, `reportlab`, `altair`)*

### 3. Ejecutar la Aplicación Streamlit
Puede iniciar la aplicación de cualquiera de las siguientes formas:

**Opción A (Línea de comandos):**
```bash
python -m streamlit run app.py
```
o bien:
```bash
streamlit run app.py
```

**Opción B (Windows 1-Click):**
Hacer doble clic en el archivo [run_app.bat](file:///d:/AECODE/Diplomado%20IA%20AEC/Entrega%20Grupal%2002/run_app.bat).

La aplicación se abrirá automáticamente en su navegador en:  
`http://localhost:8501`

---

## 📂 Estructura del Código

```text
Entrega Grupal 02/
├── app.py                      # Interfaz gráfica principal Streamlit (Pantallas a, b, c, d)
├── run_app.bat                 # Script de ejecución rápida en Windows
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación técnica completa
├── core/
│   ├── __init__.py
│   ├── progress_calculator.py  # Motor de cálculo matemático y alertas (Sección 5)
│   ├── quality_control.py      # Control de nitidez Laplaciana y resolución (RF-02)
│   ├── model.py                # Visualizador de bounding boxes YOLO y semáforo
│   ├── audit.py                # Bitácora de trazabilidad HITL y función Deshacer (RF-06, CP-07)
│   ├── report_generator.py     # Generador de reportes en PDF con ReportLab (RF-08)
│   └── sample_data.py          # Datos de prueba de obra y fotos sintéticas
└── tests/
    └── test_engine.py          # Test unitario automatizado del Caso Dorado CP-05 (80.4%)
```

---

## 👥 Créditos
- **Diego Avella** (Producto e IA)
- **Patricia Luna** (Procesos AEC, Plan de Unidades y Validación)
- **Daniel Salcedo** (Software, Nube y Desarrollo de Plataforma)
