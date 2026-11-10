# Brayton Simulator

**Simulación termodinámica y propulsión aeronáutica · Thermodynamic simulation and aircraft propulsion**

**[🇪🇸 Español](README.es.md) · [🇬🇧 English](README.en.md)**

> **Español:** Brayton Simulator es una aplicación educativa en Python y Flask para estudiar ciclos Brayton y turborreactores simplificados. Incluye modelos ideales y no ideales, propiedades variables cp(T), toberas convergentes y convergentes-divergentes, y un banco interactivo con tres modalidades de funcionamiento. Ofrece gráficas y estudios paramétricos, con limitaciones físicas y numéricas documentadas.
>
> **English:** Brayton Simulator is an educational Python and Flask application for exploring Brayton cycles and simplified turbojets. It includes ideal and non-ideal models, variable properties cp(T), convergent and convergent-divergent nozzles, and a three-mode interactive engine bench. Graphs, parametric studies, and physical/numerical limitations are documented.

## Documentación / Documentation

- 🇪🇸 **[Leer documentación completa en español](README.es.md)** — modelos, modalidades A/B/C, instalación, gráficas, pruebas y limitaciones.
- 🇬🇧 **[Read the full documentation in English](README.en.md)** — models, A/B/C modes, installation, graphs, verification and limitations.

## Inicio rápido / Quick start (Windows)

```powershell
git clone https://github.com/cferper/Brayton_simutalor.git
cd Brayton_simutalor
git switch mejoras/cp-variable
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_app.py
```

Abre / Open: **[http://127.0.0.1:5000/turborreactor/interactivo](http://127.0.0.1:5000/turborreactor/interactivo)**

Otras interfaces / Other interfaces: `/turborreactor` · `/brayton`.

**Proyecto educativo, no motor certificado. / Educational project, not a certified engine model.**

[Arquitectura y código / Architecture and code](CODE_WALKTHROUGH.md) · [Documentación técnica / Technical notes](docs/milestones/)
