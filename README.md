# DEUSTO iDesign RES

Generador de perfiles anuales industriales para:
- demanda electrica
- demanda termica

El repositorio combina perfiles diarios, estacionalidad y factores por sector para producir:
- ficheros `.xlsx` con el perfil anual por aplicacion
- diagramas `.png` en `Generated/diagrams`

## Requisitos

Python 3.10+ y estas librerias:

```bash
pip install pandas numpy matplotlib holidays openpyxl
```

## Funcionamiento

El flujo de calculo sigue 4 modulos:

1. `module_1`: construye perfiles diarios base por tipo de dia (laborable, sabado, domingo, festivo y cargas constantes).
2. `module_2`: aplica factores peak/base y redistribucion por aplicaciones.
3. `module_3`: crea el calendario anual, aplica estacionalidad (HDD) y normaliza a 1000 MWh.
4. `module_4`: escala al consumo anual real y (en electrico) anade fluctuaciones.

Los lanzadores son:
- `ElectricalProfile/LoadGeneratorElectricity.py`
- `ThermalProfile/LoadGeneratorThermal.py`
- `main.py` (entrada recomendada por CLI para ejecutar electrico, termico o ambos)

## Uso rapido (CLI recomendada)

Ejecutar ambos perfiles con valores por defecto:

```bash
python main.py --non-interactive
```

Ejemplo electrico:

```bash
python main.py --profile electric --country ES --year 2020 --electric-industry 1 --weights-mode unsummed --non-interactive
```

Ejemplo termico:

```bash
python main.py --profile thermal --country ES --year 2020 --thermal-industry 1 --non-interactive
```

## Salidas

Despues de ejecutar:
- `Generated/load_profiles/`: perfiles anuales en Excel
- `Generated/diagrams/`: graficos del perfil anual

## Ejemplos de imagenes

### Perfil electrico (ES, ISI, 2020, unsummed)

![Perfil electrico ES ISI 2020](Generated/diagrams/iDesign_RES_ES_ISI_Iron_and_steel_2020_unsummed_rerun_Diagram.png)

### Perfil termico (Primary Steel, ES)

![Perfil termico Primary Steel ES](Generated/diagrams/iDesign_RES_Primary%20Steel_ES_Diagram.png)

## Estructura principal

- `main.py`: interfaz CLI (interactiva y no interactiva).
- `ElectricalProfile/LoadGeneratorElectricity.py`: pipeline electrico completo.
- `ThermalProfile/LoadGeneratorThermal.py`: pipeline termico completo.
- `Modules/module_1.py` a `Modules/module_4.py`: logica de generacion.
- `Modules/module_plot.py`: render y guardado de diagramas.
