# Brayton Simulator

An educational Python project for exploring **Brayton-cycle thermodynamics** and **simplified aircraft turbojet performance**. It combines numerical models with a local Flask interface so aerospace engineering students can change operating conditions, inspect physical balances and investigate how a gas turbine responds.

The project is intended for learning and software verification, **not** for sizing or certifying a real engine.

## What you can study

### Brayton cycle

- Ideal and non-ideal cycle calculations, including compressor and turbine performance, pressure losses, heat input, specific work and thermal efficiency.
- The historical constant-property model and a separate, more recent air-property model with temperature-dependent heat capacity, **cp(T)**.
- Numerical searches for operating regions and optima, one-variable sensitivity studies and pressure-ratio/temperature design maps.
- Thermodynamic state tables, energy and second-law/exergy analysis, diagrams and locally generated reports. Diagram availability depends on the model and view selected.

Historical report files are preserved as records; opening one does not recompute it with a newer physical model.

### Turbojet

A separate turbojet model represents the inlet/diffuser, compressor, simplified combustion-energy addition, turbine and nozzle. Depending on the configuration, it provides:

- Stagnation and static states, pressure and temperature changes, shaft-work balance and fuel-equivalent consumption.
- Convergent and convergent-divergent (C-D) nozzles, including implemented compressible-flow regimes and normal-shock treatment where applicable.
- Nozzle mass flow, throat/exit areas, equivalent diameters and a simplified conical geometry.
- Flight and exhaust velocities, specific thrust, absolute thrust **when mass flow is defined**, thrust contributions and thrust-specific fuel consumption (TSFC).
- A coupled single-spool operating-point calculation using normalized compressor and turbine maps.

The fuel/combustor model is an energy-balance approximation, not detailed chemical combustion.

### Interactive engine bench

Open **`/turborreactor/interactivo`** to work with three operating modes:

| Mode | What you specify | What the simulator determines |
| --- | --- | --- |
| **A — Prescribed mass flow** | Air mass flow and engine/flight conditions | Nozzle behavior and propulsive performance for the prescribed flow |
| **B — Fixed geometry** | Nozzle throat/exit geometry and engine/flight conditions | Compatible flow and nozzle/engine performance under the geometric constraints |
| **C — Coupled engine** | Flight/thermal conditions and nozzle geometry | A numerically verified operating point, if found, coupling compressor and turbine maps with the nozzle |

All three modes allow parameter exploration; their prescribed and calculated variables are not interchangeable.

In **mode C**, the **Reset design geometry** button explicitly restores the reference throat and exit areas calculated by the existing design model. The reference is **convergent** (Ag = Ae), even if the C-D nozzle option is selected: it is not a C-D optimum. Custom areas remain editable, and switching modes does not silently overwrite them. Some geometries do not yield a numerically verified coupled solution; this alone does not establish physical impossibility.

## Graphs and interactive analysis

The engine bench groups results into:

- **Cycle:** schematic T–s diagram; total temperatures and pressures at calculated stations; compressor/turbine and shaft-work displays; energy balance.
- **Nozzle:** geometry and, where the solved geometry supports them, axial Mach, static pressure, static temperature and velocity profiles. Shock discontinuities are shown without fictitious interpolation.
- **Performance:** specific and (when available) absolute thrust decomposition, plus flight and exhaust velocities.

Technical graphs support point inspection, zoom and export to SVG or PNG where the respective graph offers those controls. Plots show the information available from the selected model; a graph is omitted when its underlying data or geometric profile is unavailable. Connecting discrete station values does **not** imply a spatially resolved component simulation.

### Parametric studies

The interactive bench also provides:

- Thrust versus flight Mach number.
- Thrust and TSFC versus turbine-inlet temperature **T3**.
- Mach–T3 performance maps.
- Comparison of compatible configurations/curves.
- CSV data export and graphical export where offered.

Unresolved or invalid operating points are identified rather than filled with invented values. Mode C generally requires more numerical work, so sweep and map resolutions are bounded more tightly than in A/B. These studies explore the implemented model; they are **not** measured engine operating maps.

The classic turbojet page (`/turborreactor`) also retains its own results, sensitivity and performance-map tools.

## Run locally on Windows

**Requirements:** Python with `venv` and `pip`, and a modern web browser. The repository's `requirements.txt` lists the core Python dependencies: **NumPy, Matplotlib and Flask**. SciPy is optional for selected numerical comparisons; it is not required to start the web application.

Open PowerShell in a folder of your choice:

```powershell
git clone https://github.com/cferper/Brayton_simutalor.git
cd Brayton_simutalor
git switch mejoras/cp-variable
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python web_app.py
```

If PowerShell prevents activation, you can use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe web_app.py` without activating the environment.

Alternatively, once `.venv` is installed, run **`Abrir_Brayton_Simulator.cmd`** to start the local server and open a browser.

The supplied launcher starts Flask on `127.0.0.1:5000`. Other ports can be used by changing the local server setup; **5001/5002 are not physical-model requirements**.

| Address | Interface |
| --- | --- |
| [`/turborreactor/interactivo`](http://127.0.0.1:5000/turborreactor/interactivo) | Interactive bench (modes A/B/C) |
| [`/turborreactor`](http://127.0.0.1:5000/turborreactor) | Classic turbojet interface |
| [`/brayton`](http://127.0.0.1:5000/brayton) | Variable-property Brayton dashboard |

The root URL (`/`) redirects to the interactive turbojet bench. Keep the terminal open while using the app; press **Ctrl+C** to stop it. The Flask development server is intended for local use, not public deployment.

## Verification and limitations

The repository includes automated checks for thermodynamics, balances and numerical boundaries; solvers and optional SciPy comparisons; Flask routes/API contracts; browser-side logic; graphics; and parametric studies. The [milestone 49.6 notes](docs/milestones/49_6_ampliacion_graficas_motor.md) record a Windows regression of **769 passing, 10 skipped and 0 failing Python tests**, plus **9 passing JavaScript tests** after the geometry-reset integration. These are recorded results, not a claim that tests were rerun for this README edit.

**Software verification is not experimental validation.** In particular:

- This is a simplified educational simulator, **not a certified or validated engine model**.
- Fuel chemistry and combustion-product properties are simplified; component models, efficiencies and map assumptions have defined validity ranges.
- Certain parameter combinations have no verified numerical solution. Non-convergence is not, by itself, proof of physical impossibility.
- Some quantities, absolute thrust and axial profiles in particular, require information unavailable in certain modes or nozzle configurations.
- Schematic diagrams of thermodynamic stations should not be interpreted as full three-dimensional or transient flow fields.

## Repository guide

| Path | Purpose |
| --- | --- |
| `web_app.py` | Flask server, routes and API endpoints |
| `ciclo_cp_variable.py`, `cp_variable_web.py` | Variable-property Brayton calculations and web adapter |
| `turborreactor_web.py`, `prestaciones_turborreactor_web.py` | Turbojet model presentation and performance studies |
| `acoplamiento_motor_mapa_47.py` | Coupled-engine operating point and design reference |
| `estudios_parametricos_49_5.py` | Interactive Mach/T3 studies |
| `templates/`, `static/` | HTML templates, JavaScript and styles |
| `data/tmats_47/` | Normalized component-map data and provenance |
| `tests/` | Automated tests |
| `docs/milestones/` | Engineering decisions, verification notes and learning guides |
| `requirements.txt`, `Abrir_Brayton_Simulator.cmd` | Dependencies and Windows launcher |

## Further reading

- [Code walkthrough](CODE_WALKTHROUGH.md) — architecture, numerical methods and implementation.
- [Milestone documentation](docs/milestones/) — detailed technical records and educational explanations.
- [Interactive technical graphs (49.4)](docs/milestones/49_4_graficas_tecnicas_interactivas.md).
- [Parametric studies (49.5)](docs/milestones/49_5_estudios_parametricos_interactivos.md).
- [Engine graphs and mode-C reference geometry (49.6)](docs/milestones/49_6_ampliacion_graficas_motor.md).
- [Development guidelines](AGENTS.md).

Brayton Simulator is a personal aerospace engineering learning project.
