# PokéGym Battle Validator 🧪⚡ — Solución con Poke‑MCP (README)

> **Objetivo de hackatón:** validar que un servicio `PokéGym` calcule correctamente el **multiplicador de daño** entre tipos (🔥, 🌿, ⚡, …) comparándolo contra una **fuente de verdad** obtenida vía **Poke‑MCP** (que a su vez consume datos de PokéAPI). Foco en ser **sencillo**, **demo‑friendly** y ejecutable en **<5 min**.

---

## 0) Resumen ejecutivo

- Construirás un **sistema multiagente** que:
  1) Descarga/compone una **matriz de tipos** (oráculo) usando **Poke‑MCP**.  
  2) Genera un **lote pequeño de casos** (felices/inefectivos/poco efectivos/neutros/erróneos).  
  3) Ejecuta los casos contra tu **servicio bajo test** `GET /battle?attacker=...&defender=...`.  
  4) Compara resultados y produce un **informe** con métricas (score, p95, top fallos).

- **Tecnologías:** Python (FastAPI/requests/pytest), **Poke‑MCP** (Node/HTTP SSE o stdio).  
- **Salida principal:** `runs/<timestamp>/report.md` + artefactos JSON.

---

## 1) Arquitectura multiagente (roles y responsabilidades)

### Agentes
1. **Spec‑Reader (Fuente de verdad)**  
   - **Input:** `{ "generation": 9 }` (opcional)  
   - **Acción:** consulta **Poke‑MCP** para obtener información de tipos y compone un `TypeChart` con multiplicadores `2.0`, `0.5`, `0.0`, `1.0`.  
   - **Output:** `artifacts/type_chart.json`

2. **Test‑Suggester (Plan de pruebas)**  
   - **Input:** `type_chart.json`, `{ "budget": 40 }`  
   - **Acción:** crea un lote balanceado:  
     - 8 felices (p.ej. `fire→grass=2.0`)  
     - 8 inefectivos (`electric→ground=0.0`)  
     - 8 poco efectivos (`water→grass=0.5`)  
     - 8 neutros (`normal→fire=1.0`)  
     - 4 inválidos (tipo inexistente, case raro, etc.)  
   - **Output:** `plan/tests.json`

3. **Oracle (Expected‑Calculator)**  
   - **Input:** `type_chart.json`, `plan/tests.json`  
   - **Acción:** rellena `expect` para cada test usando el oráculo; marca como `invalid` los tipos desconocidos.  
   - **Output:** `plan/expectations.json` (mismo shape que tests, con `expect`)

4. **Runner (Ejecución del SUT)**  
   - **Input:** `BASE_URL`, `plan/tests.json`  
   - **Acción:** llama `GET /battle?attacker=...&defender=...` (o `POST /battle`)  
   - **Output:** `runs/raw_results.json` (incluye `status`, `latency_ms`, `multiplier` y `raw`)

5. **Comparator/Analyzer (Asersiones y métricas)**  
   - **Input:** `runs/raw_results.json`, `plan/expectations.json`  
   - **Acción:** compara `actual.multiplier` vs `expect` (tolerancia ±0.01); valida códigos esperados (200/400/422).  
   - **Output:** `runs/assertions.json` con `pass/fail`, `delta`, y motivos.

6. **Reporter (Informe final)**  
   - **Input:** `runs/assertions.json` + latencias  
   - **Acción:** genera `runs/<ts>/report.md` con: **Score**, **p95**, **Top 5 fallos** (request/response + recomendación) y **cobertura por categoría**.

### Flujo de datos (resumen)
```
Spec‑Reader  →  type_chart.json
      └──> Test‑Suggester → tests.json
                      └──> Oracle → expectations.json
                                   └──> Runner → raw_results.json
                                                 └──> Analyzer → assertions.json
                                                               └──> Reporter → report.md
```

---

## 2) API objetivo PokéGym (SUT)

### Endpoint mínimo (GET)
```http
GET /battle?attacker={type}&defender={type}
200 OK
{
  "attacker": "fire",
  "defender": "grass",
  "multiplier": 2.0,
  "explanation": "Fire is super effective against Grass."
}
```

**Errores esperados:**  
- `422 Unprocessable Entity` → tipo mal formado o inexistente.  
- `400 Bad Request` → parámetros faltantes.

### OpenAPI (snippet)
```yaml
openapi: 3.0.3
info: { title: PokéGym, version: "0.1.0" }
paths:
  /battle:
    get:
      parameters:
        - { name: attacker, in: query, required: true, schema: { type: string } }
        - { name: defender, in: query, required: true, schema: { type: string } }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  attacker: { type: string }
                  defender: { type: string }
                  multiplier: { type: number, format: float }
                  explanation: { type: string }
        "400": { description: Missing params }
        "422": { description: Unknown type }
```

> Si no tienes el SUT aún, más abajo hay un **stub FastAPI** listo para correr.

---

## 3) Integración con **Poke‑MCP** (simplificado)

### 3.1. ¿Qué es Poke‑MCP?
Un **servidor MCP** de la comunidad que facilita operaciones relacionadas con Pokémon (consulta de datos a partir de PokéAPI, utilidades, etc.). Se puede ejecutar **localmente** y exponer por:  
- **stdio** (ideal para integrarlo en clientes MCP nativos), o  
- **HTTP** (SSE / Streamable HTTP) en `http://127.0.0.1:3000` (puerto sugerido).

> Para la hackatón usaremos **modo HTTP** para no escribir un cliente stdio.

### 3.2. Variables de entorno recomendadas
```bash
# Transportes posibles: http-sse (recomendado), stdio
export MCP_TRANSPORT=http-sse
# URL del servidor Poke‑MCP levantado en local (ajusta si cambias el puerto)
export MCP_URL=http://127.0.0.1:3000/sse
# Timeout en segundos para llamadas al MCP
export MCP_TIMEOUT=15
```

### 3.3. ¿Qué herramienta MCP usamos?
- **`pokemon-query`** o una herramienta similar del Poke‑MCP que permita recuperar entidades y, en particular, **tipos** y **damage_relations**.  
- El **Spec‑Reader** llama a esa herramienta para obtener, por cada tipo (fire, water, grass, …), sus conjuntos:  
  - `double_damage_to`, `half_damage_to`, `no_damage_to`.  
- Con esos sets compone el `TypeChart` (18×18) con multiplicadores `{2.0, 0.5, 0.0, 1.0}`.

> **Fallback**: si alguna herramienta no expone `damage_relations` directamente, el Spec‑Reader puede degradar a pedir la ruta **PokéAPI** `https://pokeapi.co/api/v2/type/{type}` (vía el mismo Poke‑MCP si ofrece un tool HTTP genérico, o directamente con `requests`).

---

## 4) Estructura de carpetas (sugerida)
```
pokegym-validator/
├─ app/
│  ├─ sut/                 # (opcional) SUT de ejemplo (FastAPI /battle)
│  │  ├─ main.py
│  │  └─ requirements.txt
│  ├─ agents/
│  │  ├─ spec_reader.py
│  │  ├─ test_suggester.py
│  │  ├─ oracle.py
│  │  ├─ runner.py
│  │  ├─ analyzer.py
│  │  └─ reporter.py
│  ├─ core/
│  │  ├─ mcp_client.py     # cliente HTTP‑SSE muy simple
│  │  └─ io.py             # helpers lectura/escritura artefactos
│  ├─ run.py               # orquestador CLI
│  └─ settings.py
├─ runs/                   # artefactos por ejecución (se autogenera)
├─ Makefile
└─ README.md               # este archivo
```

---

## 5) Contratos I/O (JSON)

**`TypeChart` (simplificado)**  
```json
{
  "fire":   { "fire": 1.0, "water": 0.5, "grass": 2.0, "rock": 0.5, "...": 1.0 },
  "water":  { "fire": 2.0, "grass": 0.5, "rock": 2.0, "...": 1.0 },
  "electric": { "water": 2.0, "ground": 0.0, "...": 1.0 },
  "...": {}
}
```

**`TestCase`**  
```json
{ "id": "fire-grass-1", "attacker": "fire", "defender": "grass", "expect": 2.0, "kind": "happy" }
```

**`RunResult`**  
```json
{ "id": "fire-grass-1", "status": 200, "multiplier": 2.0, "latency_ms": 31, "raw": { "attacker":"fire", "defender":"grass" } }
```

**`Assertion`**  
```json
{ "id": "fire-grass-1", "pass": true, "delta": 0.0 }
```

---

## 6) Setup rápido

### 6.1. Prerrequisitos
- **Python 3.11+** (con `venv`)  
- **Node 18+** (para correr Poke‑MCP)  
- `make` (opcional pero cómodo)

### 6.2. Instalar dependencias Python
```bash
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn requests httpx pydantic rich pytest
```

### 6.3. Levantar **Poke‑MCP** en local (modo HTTP)
> Consulta el README del proyecto de Poke‑MCP que elijas; típicamente:
```bash
# En el repo de Poke‑MCP (o paquete equivalente)
# 1) instalar dependencias
npm install
# 2) lanzar servidor en 127.0.0.1:3000 con SSE habilitado
npm run start
# (si el script usa otro puerto, ajusta MCP_URL)
```
Exporta las variables:
```bash
export MCP_TRANSPORT=http-sse
export MCP_URL=http://127.0.0.1:3000/sse
```

### 6.4. (Opcional) Levantar SUT de ejemplo `/battle`
```bash
cd app/sut
pip install -r requirements.txt  # (fastapi uvicorn pydantic)
uvicorn main:app --reload --port 8001
```

### 6.5. Ejecutar el orquestador
```bash
cd app
python run.py --base-url http://127.0.0.1:8001 --budget 40
# Artefactos en runs/<timestamp>/
```

---

## 7) Snippets útiles

### 7.1. **Stub del SUT** (FastAPI `/battle`) — *opcional para demo*
```python
# app/sut/main.py
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="PokéGym")

# Matriz mínima (demo). En producción, consulta tu propia lógica.
TYPE_CHART = {
    "fire":   {"grass": 2.0, "water": 0.5, "fire": 1.0, "rock": 0.5},
    "water":  {"fire": 2.0, "grass": 0.5, "rock": 2.0},
    "electric":{"water": 2.0, "ground": 0.0},
    "normal": {"ghost": 0.0},
    "fairy":  {"dragon": 2.0},
}

def resolve_multiplier(attacker: str, defender: str) -> float:
    att = attacker.lower().strip()
    deff = defender.lower().strip()
    # inválidos
    if not att or not deff: raise ValueError("bad-params")
    # multiplicador por defecto = 1.0
    return TYPE_CHART.get(att, {}).get(deff, 1.0)

@app.get("/battle")
def battle(attacker: str = Query(...), defender: str = Query(...)):
    a = attacker.lower().strip()
    d = defender.lower().strip()
    # tipos conocidos (demo simple): si no están en algún set conocido, 422
    KNOWN = set(TYPE_CHART.keys()) | set(t for m in TYPE_CHART.values() for t in m.keys())
    if a not in KNOWN or d not in KNOWN:
        raise HTTPException(status_code=422, detail="Unknown type")
    try:
        mult = resolve_multiplier(a, d)
    except ValueError:
        raise HTTPException(status_code=400, detail="Missing params")
    return {
        "attacker": a, "defender": d, "multiplier": float(mult),
        "explanation": f"{a} vs {d} multiplier = {mult}"
    }
```

`requirements.txt`
```
fastapi
uvicorn
pydantic
```

### 7.2. **Cliente MCP muy simple (HTTP‑SSE)** — *consulta tipos*
```python
# app/core/mcp_client.py (pseudo‑simplificado)
import os, json, time, httpx

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:3000/sse")
MCP_TIMEOUT = float(os.getenv("MCP_TIMEOUT", "15"))

class PokeMCP:
    """Cliente mínimo para invocar una herramienta 'pokemon-query'."""
    def __init__(self, url=MCP_URL, timeout=MCP_TIMEOUT):
        self.url = url
        self.timeout = timeout

    def query_type(self, type_name: str) -> dict:
        """
        Devuelve un dict con damage_relations para `type_name`.
        Este método asume que el servidor expone una herramienta que permite
        recuperar el JSON de tipo. Si no, usa fallback directo a PokéAPI.
        """
        # Fallback directo si no tienes un tool MCP que exponga 'type'
        r = httpx.get(f"https://pokeapi.co/api/v2/type/{type_name}", timeout=self.timeout)
        r.raise_for_status()
        return r.json()
```

### 7.3. **Spec‑Reader (construcción de TypeChart)**
```python
# app/agents/spec_reader.py
from typing import Dict, Set
from app.core.mcp_client import PokeMCP

MULTS = {"double_damage_to": 2.0, "half_damage_to": 0.5, "no_damage_to": 0.0}

def build_type_chart(types=("normal","fire","water","grass","electric","ground","rock","ice","fighting","poison","flying","psychic","bug","ghost","steel","dragon","dark","fairy")) -> Dict[str, Dict[str, float]]:
    mcp = PokeMCP()
    chart: Dict[str, Dict[str, float]] = {}
    for t in types:
        data = mcp.query_type(t)
        rel = data.get("damage_relations", {})
        chart[t] = {}
        # Inicializa a 1.0 por defecto al final (no listado = neutro)
        for key, mult in MULTS.items():
            for entry in rel.get(key, []):
                name = entry.get("name")
                if name:
                    chart[t][name] = mult
        # Completa tipos faltantes a 1.0 (neutro)
        for d in types:
            chart[t].setdefault(d, 1.0)
    return chart
```

### 7.4. **Test‑Suggester (plan de casos)**
```python
# app/agents/test_suggester.py
import random, json, time

def suggest_tests(chart: dict, budget: int = 40) -> list:
    rng = random.Random(42)
    types = list(chart.keys())
    cases = []

    def pick(kind, predicate):
        # genera hasta n casos que cumplan predicate
        n = max(1, budget // 5)
        tries = 0
        while len([c for c in cases if c["kind"] == kind]) < n and tries < 500:
            a, d = rng.choice(types), rng.choice(types)
            if predicate(chart[a][d]):
                cases.append({"id": f"{a}-{d}-{len(cases)}", "attacker": a, "defender": d, "kind": kind})
            tries += 1

    pick("happy",       lambda m: abs(m - 2.0) < 1e-9)
    pick("ineffective", lambda m: abs(m - 0.0) < 1e-9)
    pick("resisted",    lambda m: abs(m - 0.5) < 1e-9)
    pick("neutral",     lambda m: abs(m - 1.0) < 1e-9)

    # inválidos
    invalids = [{"id": f"plasma-water-{i}", "attacker":"plasma", "defender":"water", "kind":"invalid"} for i in range(max(1, budget//10))]
    cases.extend(invalids)
    return cases
```

### 7.5. **Oracle (rellena expects)**
```python
# app/agents/oracle.py
def fill_expectations(chart: dict, tests: list) -> list:
    out = []
    for t in tests:
        a, d = t["attacker"], t["defender"]
        expect = chart.get(a, {}).get(d, None)
        if a not in chart or d not in chart[a]:
            out.append({**t, "expect": None, "invalid": True})
        else:
            out.append({**t, "expect": expect, "invalid": False})
    return out
```

### 7.6. **Runner (llamadas al SUT)**
```python
# app/agents/runner.py
import time, httpx

def run_cases(base_url: str, tests: list, timeout: float = 5.0) -> list:
    results = []
    with httpx.Client(timeout=timeout) as client:
        for t in tests:
            a, d = t["attacker"], t["defender"]
            url = f"{base_url.rstrip('/')}/battle"
            start = time.perf_counter()
            try:
                resp = client.get(url, params={"attacker": a, "defender": d})
                latency = (time.perf_counter() - start) * 1000
                data = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {}
                results.append({
                    "id": t["id"], "status": resp.status_code,
                    "latency_ms": round(latency, 2),
                    "multiplier": data.get("multiplier"),
                    "raw": data
                })
            except Exception as e:
                latency = (time.perf_counter() - start) * 1000
                results.append({"id": t["id"], "status": 599, "latency_ms": round(latency, 2), "error": str(e)})
    return results
```

### 7.7. **Analyzer (asersiones)**
```python
# app/agents/analyzer.py
def compare(results: list, expectations: list, tol=0.01):
    exp_map = {e["id"]: e for e in expectations}
    out = []
    for r in results:
        e = exp_map.get(r["id"])
        # reglas de estado esperado
        if e and e.get("invalid"):
            status_ok = (r["status"] == 422)
            pass_ = status_ok
            why = None if pass_ else f"expected 422 for invalid types, got {r['status']}"
        else:
            # requiere 200 y multiplier cercano a expect
            status_ok = (r["status"] == 200)
            mult_ok = (e is not None and isinstance(r.get("multiplier"), (int,float)) and abs(r["multiplier"] - e["expect"]) <= tol)
            pass_ = status_ok and mult_ok
            why = None if pass_ else f"expected {e['expect']} got {r.get('multiplier')} (status={r['status']})"
        out.append({"id": r["id"], "pass": bool(pass_), "delta": None if not e else (None if e.get('invalid') else round((r.get('multiplier', 0) - e['expect']), 3)), "why": why})
    return out
```

### 7.8. **Reporter (markdown)**
```python
# app/agents/reporter.py
from statistics import quantiles

def mk_report(assertions: list, results: list) -> str:
    total = len(assertions)
    passed = sum(1 for a in assertions if a["pass"])
    latencies = [r["latency_ms"] for r in results if isinstance(r.get("latency_ms"), (int,float))]
    p95 = round(quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else (max(latencies) if latencies else 0)
    lines = []
    lines.append(f"# PokéGym Battle Validator — Reporte")
    lines.append("")
    lines.append(f"- **Score:** {passed}/{total} ({(passed/total*100):.1f}%)")
    lines.append(f"- **p95 latencia:** {p95} ms")
    lines.append("")
    lines.append("## Fallos destacados")
    for a in assertions:
        if not a["pass"]:
            lines.append(f"- `{a['id']}` → {a.get('why','')}".strip())
    return "\n".join(lines)
```

### 7.9. **Orquestador CLI (`run.py`)**
```python
# app/run.py
import json, time, argparse
from pathlib import Path
from agents.spec_reader import build_type_chart
from agents.test_suggester import suggest_tests
from agents.oracle import fill_expectations
from agents.runner import run_cases
from agents.analyzer import compare
from agents.reporter import mk_report

def main(base_url: str, budget: int = 40):
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = Path("../runs") / ts
    outdir.mkdir(parents=True, exist_ok=True)

    chart = build_type_chart()
    (outdir / "type_chart.json").write_text(json.dumps(chart, indent=2))

    tests = suggest_tests(chart, budget=budget)
    (outdir / "tests.json").write_text(json.dumps(tests, indent=2))

    exps = fill_expectations(chart, tests)
    (outdir / "expectations.json").write_text(json.dumps(exps, indent=2))

    results = run_cases(base_url, tests)
    (outdir / "raw_results.json").write_text(json.dumps(results, indent=2))

    assertions = compare(results, exps)
    (outdir / "assertions.json").write_text(json.dumps(assertions, indent=2))

    report = mk_report(assertions, results)
    (outdir / "report.md").write_text(report)
    print((outdir / "report.md").as_posix())

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--budget", type=int, default=40)
    args = ap.parse_args()
    main(args.base_url, args.budget)
```

---

## 8) Métricas y criterios (SMART)

- **Tiempo total:** `< 5 min` (de orquestación completa en local).  
- **Cobertura de categorías:** probar al menos 1 caso por cada categoría (2×, ½×, 0×, 1×, inválidos).  
- **Detección de errores:** 100% de inválidos devuelven **422**; >95% de casos válidos aciertan el multiplicador.  
- **Rendimiento:** p95 de latencia del SUT **< 100 ms** (local).  
- **Usabilidad:** `python app/run.py --base-url http://127.0.0.1:8001 --budget 40` produce `report.md` sin intervención.

---

## 9) Makefile (opcional)
```makefile
.PHONY: venv deps sut run lint test clean

venv:
	python -m venv .venv

deps:
	. .venv/bin/activate && pip install -r app/sut/requirements.txt && pip install requests httpx fastapi uvicorn pydantic rich pytest

sut:
	. .venv/bin/activate && uvicorn app.sut.main:app --reload --port 8001

run:
	. .venv/bin/activate && python app/run.py --base-url http://127.0.0.1:8001 --budget 40

clean:
	rm -rf runs/*
```

---

## 10) Plan de demo (3–4 min)

1) **Arranque:** `npm run start` (Poke‑MCP) y `uvicorn app.sut.main:app` (SUT).  
2) **Ejecutar:** `python app/run.py --base-url http://127.0.0.1:8001 --budget 40`.  
3) **Mostrar `report.md`:** score, p95, 2–3 fallos con explicación.  
4) **Stretch:** cambiar `TYPE_CHART` del SUT para introducir un bug (p.ej. `electric→ground=0.5`) y rerun → ver fallo.

---

## 11) Troubleshooting

- **Poke‑MCP no responde:** confirma `MCP_URL` y puerto correcto, revisa CORS si lo publicas.  
- **Tipos “desconocidos” en masa:** habilita el **fallback a PokéAPI** en `PokeMCP.query_type`.  
- **Latencia alta:** aumenta timeout del Runner o reduce `budget`.  
- **SUT devuelve 200 para inválidos:** asegura lógica de validación (422).

---

## 12) Extensiones posibles

- **Soporte dual‑tipo** (atacante/defensor con 2 tipos: multiplicar factores).  
- **Snapshots contractuales** (comparar tu SUT con releases previas).  
- **Export HTML/Badges** del reporte.  
- **Baseline de rendimiento** (alerta si p95 ↑ >20% vs. baseline).

---

### Créditos
- **PokéAPI** por los datos de tipos.  
- **Poke‑MCP** por simplificar la integración con el ecosistema Pokémon.
