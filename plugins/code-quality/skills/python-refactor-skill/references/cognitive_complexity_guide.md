# Cognitive Complexity: Guida Completa

> La cognitive complexity misura quanto è **difficile capire** il codice, non quanti path di esecuzione esistono.

---

## 📐 Regole di Calcolo

### Regola 1: Incrementi Base (+1)

Ogni **break nel flusso lineare** del codice aggiunge +1:

```python
def example():
    if condition:        # +1
        pass
    for item in items:   # +1
        pass
    while running:       # +1
        pass
    try:                 # +0 (try non incrementa)
        pass
    except Error:        # +1
        pass
    condition and do()   # +1 (operatore logico come branch)
```

**Strutture che incrementano:**
- `if`, `elif`, `else`
- `for`, `while`
- `except`, `with`
- `and`, `or` (quando cambiano il flusso)
- Ricorsione (+1 per chiamata ricorsiva)
- `break`, `continue` con label

**Strutture che NON incrementano:**
- `try` (solo `except` incrementa)
- `finally`
- Lambda semplici
- Ternary operator a top-level

---

### Regola 2: Nesting Penalty (ESPONENZIALE!)

Ogni struttura annidata aggiunge **+1 per ogni livello di nesting**:

```python
def nested_example():
    if a:                    # +1 (nesting=0)
        if b:                # +2 (1 base + 1 nesting)
            if c:            # +3 (1 base + 2 nesting)
                if d:        # +4 (1 base + 3 nesting)
                    pass
# Totale: 1+2+3+4 = 10 per soli 4 if!
```

**Impatto devastante del nesting:**

| Livelli | Formula | Complessità Totale |
|---------|---------|-------------------|
| 1 if | 1 | 1 |
| 2 if annidati | 1+2 | 3 |
| 3 if annidati | 1+2+3 | 6 |
| 4 if annidati | 1+2+3+4 | 10 |
| 5 if annidati | 1+2+3+4+5 | 15 |

**→ Il nesting è il NEMICO PRINCIPALE della leggibilità!**

---

### Regola 3: Boolean Sequences

**Stesso operatore in sequenza = GRATIS:**
```python
# Complessità +1 (conta come singolo break)
if a and b and c and d:
    pass
```

**Cambio di operatore = +1 per ogni cambio:**
```python
# Complessità +3 (ogni cambio and→or o or→and = +1)
if a and b or c and d:
    #       ↑       ↑
    #      +1      +1 (più il +1 base = 3)
    pass
```

**Best practice:** Estrai condizioni complesse in variabili named:
```python
# PRIMA: Complessità +3
if user.active and user.verified or user.is_admin and not user.banned:
    ...

# DOPO: Complessità +1 (singola condizione)
is_regular_authorized = user.active and user.verified
is_admin_authorized = user.is_admin and not user.banned
if is_regular_authorized or is_admin_authorized:
    ...
```

---

### Regola 4: Switch/Match conta UNA VOLTA

**if-elif chain = +1 per ogni branch:**
```python
# Complessità = 4
def get_word(n):
    if n == 1:           # +1
        return "one"
    elif n == 2:         # +1
        return "couple"
    elif n == 3:         # +1
        return "few"
    else:                # +1
        return "lots"
```

**match/switch = +1 TOTALE:**
```python
# Complessità = 1 (!)
def get_word(n):
    match n:             # +1 per l'intero switch
        case 1: return "one"
        case 2: return "couple"
        case 3: return "few"
        case _: return "lots"
```

**→ Usa `match` (Python 3.10+) per ridurre drasticamente la complessità!**

---

### Regola 5: Extract Method RESETTA il Nesting

**Il pattern più potente per ridurre la complessità:**

```python
# PRIMA: Complessità = 6
def process_items(items):
    for item in items:           # +1, nesting +1
        if item.valid:           # +2 (1 + nesting 1)
            if item.ready:       # +3 (1 + nesting 2)
                handle(item)
# Totale: 1+2+3 = 6

# DOPO: Complessità = 3 (divisa tra 2 funzioni)
def process_items(items):
    for item in items:           # +1
        process_single_item(item)
# Complessità funzione 1: 1

def process_single_item(item):   # NESTING RESETTATO A 0!
    if not item.valid:           # +1 (nesting 0)
        return
    if not item.ready:           # +1 (nesting 0)
        return
    handle(item)
# Complessità funzione 2: 2

# Totale: 1 + 2 = 3 (riduzione del 50%!)
```

---

## 🛠️ Tool: Ruff + Complexipy

### Stack Raccomandato

| Tool | Cyclomatic (CC) | Cognitive (CoC) | Velocità |
|------|-----------------|-----------------|----------|
| **Ruff** | ✅ C901 | ❌ | Rust, velocissimo |
| **Complexipy** | ❌ | ✅ | Rust, velocissimo |
| flake8 + plugin | ✅ | ✅ (inattivo) | Python, lento |

**Ruff + Complexipy** è lo stack consigliato: entrambi scritti in Rust, attivamente mantenuti, ecosistema moderno.

### Setup

```bash
pip install ruff complexipy radon wily
```

### Complexipy: Tool Dedicato per Cognitive Complexity

**Caratteristiche:**
- 🦀 Scritto in Rust (velocissimo)
- 📦 Attivamente mantenuto (v5.1.0, dicembre 2025)
- 🔧 Configurazione via pyproject.toml
- 📸 Snapshot per legacy code (adozione graduale)
- 🔌 Pre-commit hook, GitHub Action, VSCode extension

#### Installazione

```bash
pip install complexipy
```

#### CLI

```bash
# Analisi base
complexipy src/

# Custom threshold (default: 15, come SonarQube)
complexipy src/ --max-complexity-allowed 15

# Output JSON per CI
complexipy src/ --output-json

# Mostra tutte le funzioni (ignora threshold)
complexipy src/ --ignore-complexity

# Ordina per complessità
complexipy src/ --sort desc
```

#### Configurazione (pyproject.toml)

```toml
[tool.complexipy]
paths = ["src"]
max-complexity-allowed = 15    # SonarQube default
exclude = ["tests", "migrations", "vendor"]
quiet = false
output-json = false
```

#### API Python

```python
from complexipy import file_complexity, code_complexity

# Analizza file
result = file_complexity("src/user_service.py")
print(f"File: {result.path}")
print(f"Total complexity: {result.complexity}")

for func in result.functions:
    status = "⚠️" if func.complexity > 15 else "✓"
    print(f"  {status} {func.name}: {func.complexity} (lines {func.line_start}-{func.line_end})")

# Analizza stringa di codice
code = """
def example(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
"""
result = code_complexity(code)
print(f"Complexity: {result.complexity}")
```

#### Snapshot per Legacy Code

Feature killer per adozione graduale su codebase esistenti:

```bash
# 1. Crea snapshot dello stato attuale
complexipy src/ --snapshot-create --max-complexity-allowed 15
# Crea: complexipy-snapshot.json

# 2. In CI: blocca solo REGRESSIONI (nuove funzioni complesse)
complexipy src/ --max-complexity-allowed 15
# ✅ Passa se non ci sono nuove funzioni sopra threshold
# ❌ Fallisce se NUOVE funzioni superano threshold
# ✅ Funzioni già nello snapshot sono "grandfathered"

# 3. Quando sistemi una funzione, viene rimossa dallo snapshot automaticamente
```

#### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/rohaquinlop/complexipy-pre-commit
    rev: v3.0.0
    hooks:
      - id: complexipy
        args: [--max-complexity-allowed, "15"]
```

#### GitHub Action

```yaml
- uses: rohaquinlop/complexipy-action@v2
  with:
    paths: src/
    max_complexity_allowed: 15
    output_json: true
```

#### VSCode Extension

Installa "Complexipy" dal marketplace per analisi real-time con indicatori visuali.

### Configurazione Ruff (per cyclomatic + linting)

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E", "W",     # pycodestyle
    "F",          # Pyflakes  
    "C90",        # McCabe cyclomatic complexity
    "B",          # flake8-bugbear
    "SIM",        # flake8-simplify
    "N",          # pep8-naming
    "UP",         # pyupgrade
    "I",          # isort
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # Cyclomatic complexity
```

### Workflow Completo

```bash
# 1. Linting veloce
ruff check src/ --fix

# 2. Cognitive complexity
complexipy src/ --max-complexity-allowed 15

# 3. Maintainability Index
radon mi src/ -s

# 4. Trend storico (opzionale)
wily build src/ && wily report src/
```

---

## 📊 Combinare Metriche

**Non affidarti a una sola metrica!**

| Metrica | Misura | Uso Ottimale |
|---------|--------|--------------|
| **Cognitive Complexity** | Difficoltà di comprensione | Code review, manutenibilità |
| **Cyclomatic Complexity** | Path di esecuzione | Test planning (min test cases) |
| **Maintainability Index** | Salute generale | Dashboard, trend |

### Setup Combinato

```bash
# Installa tutti i tool
pip install flake8 flake8-cognitive-complexity radon wily

# Analisi combinata
flake8 src/ --max-cognitive-complexity=15 --max-complexity=10
radon cc src/ -a -s  # Cyclomatic + Average
radon mi src/ -s     # Maintainability Index
```

### Target Raccomandati

| Metrica | Conservativo | Moderato | Permissivo |
|---------|--------------|----------|------------|
| Cognitive | ≤ 10 | ≤ 15 | ≤ 25 |
| Cyclomatic | ≤ 5 | ≤ 10 | ≤ 20 |
| MI (Maintainability) | ≥ 80 | ≥ 65 | ≥ 50 |

---

## 📈 Threshold Progressivi per Legacy Code

**Non applicare threshold stretti su legacy code!**

### Strategia "Ratcheting"

```yaml
# .github/workflows/quality.yml
- name: Quality Gate (Ratcheting)
  run: |
    # Salva baseline se non esiste
    if [ ! -f .quality-baseline.json ]; then
      python scripts/measure_all_metrics.py > .quality-baseline.json
    fi
    
    # Confronta con baseline
    python scripts/compare_to_baseline.py .quality-baseline.json
    
    # Fail se PEGGIORA, passa se uguale o migliore
```

### Strategia "Changed Files Only"

```bash
# Applica threshold stretti SOLO ai file modificati nel PR
CHANGED_FILES=$(git diff --name-only origin/main...HEAD -- '*.py')

for file in $CHANGED_FILES; do
    flake8 "$file" --max-cognitive-complexity=10  # Strict per nuovo codice
done

# Threshold permissivo per tutto il resto
flake8 src/ --max-cognitive-complexity=25  # Lenient per legacy
```

### Fasi di Adozione

```ini
# Fase 1: Baseline (mese 1-2)
max-cognitive-complexity = 30  # Permissivo, blocca solo casi estremi

# Fase 2: Riduzione (mese 3-6)
max-cognitive-complexity = 20  # Moderato

# Fase 3: Target (mese 6+)
max-cognitive-complexity = 15  # Standard SonarQube

# Fase 4: Strict (solo nuovo codice)
max-cognitive-complexity = 10  # Per codice greenfield
```

---

## 📉 Tracking Storico con Wily

**Monitora i trend nel tempo, non solo i threshold:**

### Setup

```bash
pip install wily

# Build cache (una volta)
wily build src/ -n 100  # Ultimi 100 commit

# Report per file
wily report src/module.py

# Diff tra commit
wily diff src/ -r HEAD~10..HEAD

# Grafico trend
wily graph src/module.py complexity  # Apre browser

# Rank dei file più complessi
wily rank src/ complexity
```

### Integrazione CI

```yaml
# .github/workflows/wily.yml
name: Complexity Trend

on:
  push:
    branches: [main]

jobs:
  wily:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 50  # Serve storia per wily
      
      - name: Setup
        run: pip install wily
      
      - name: Build Wily Cache
        run: wily build src/ -n 50
      
      - name: Check for Regression
        run: |
          # Fail se complessità AUMENTATA rispetto a commit precedente
          wily diff src/ -r HEAD~1..HEAD --exit-zero
          if wily diff src/ -r HEAD~1..HEAD | grep -q "increased"; then
            echo "❌ Complexity increased!"
            exit 1
          fi
```

### Dashboard Output

```
┌──────────────────────────────────────────────────────────────┐
│                    COMPLEXITY TREND                          │
├──────────────────────────────────────────────────────────────┤
│ File: src/services/user_service.py                          │
│                                                              │
│ Commit    Date       CC    MI    CoC                        │
│ ─────────────────────────────────────────                   │
│ abc123    2024-01-01  12    75    18   ████████████████░░   │
│ def456    2024-01-15  10    78    15   █████████████░░░░░   │
│ ghi789    2024-02-01   8    82    12   ██████████░░░░░░░░   │
│ jkl012    2024-02-15   6    85     9   ███████░░░░░░░░░░░   │
│                                                              │
│ TREND: ↓ Improving (-50% complexity in 6 weeks)             │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 Pattern di Refactoring ad Alto Impatto

### Pattern 1: Dictionary Dispatch (elimina if-elif chains)

```python
# PRIMA: Cognitive Complexity = 8
def process_action(action, data):
    if action == "create":           # +1
        return create_item(data)
    elif action == "read":           # +1
        return read_item(data)
    elif action == "update":         # +1
        return update_item(data)
    elif action == "delete":         # +1
        return delete_item(data)
    elif action == "archive":        # +1
        return archive_item(data)
    elif action == "restore":        # +1
        return restore_item(data)
    elif action == "clone":          # +1
        return clone_item(data)
    else:                            # +1
        raise ValueError(f"Unknown action: {action}")

# DOPO: Cognitive Complexity = 1
ACTION_HANDLERS = {
    "create": create_item,
    "read": read_item,
    "update": update_item,
    "delete": delete_item,
    "archive": archive_item,
    "restore": restore_item,
    "clone": clone_item,
}

def process_action(action, data):
    handler = ACTION_HANDLERS.get(action)
    if handler is None:              # +1 (unico branch)
        raise ValueError(f"Unknown action: {action}")
    return handler(data)

# Riduzione: 87.5%!
```

### Pattern 2: Guard Clauses (elimina nesting)

```python
# PRIMA: Cognitive Complexity = 10
def process_order(order):
    if order:                           # +1
        if order.is_valid():            # +2 (nesting)
            if order.has_items():       # +3 (nesting)
                if order.payment_ok():  # +4 (nesting)
                    return fulfill(order)
    return OrderResult.failed()

# DOPO: Cognitive Complexity = 4
def process_order(order):
    if not order:                   # +1
        return OrderResult.failed()
    if not order.is_valid():        # +1
        return OrderResult.failed()
    if not order.has_items():       # +1
        return OrderResult.failed()
    if not order.payment_ok():      # +1
        return OrderResult.failed()
    return fulfill(order)

# Riduzione: 60%!
```

### Pattern 3: Extract + Compose (spezza funzioni monster)

```python
# PRIMA: Una funzione con Cognitive Complexity = 25
def process_user_registration(data):
    # 20 righe di validazione
    # 15 righe di normalizzazione
    # 10 righe di salvataggio
    # 10 righe di notifica
    # 15 righe di logging
    pass  # 70+ righe, CC=25

# DOPO: Composizione di funzioni semplici
def process_user_registration(data):
    validated = validate_registration(data)      # CC=4
    normalized = normalize_user_data(validated)  # CC=2
    user = save_user(normalized)                 # CC=3
    send_welcome_email(user)                     # CC=2
    log_registration(user)                       # CC=1
    return user
# Funzione principale: CC=0 (nessun branch!)
# Totale distribuito: 4+2+3+2+1 = 12 (ma mai >4 in una singola funzione)
```

---

## 📋 Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              COGNITIVE COMPLEXITY CHEAT SHEET               │
├─────────────────────────────────────────────────────────────┤
│ INCREMENTA (+1):                                            │
│   if, elif, else, for, while, except, and, or, recursion   │
│                                                             │
│ NESTING PENALTY (+1 per livello):                          │
│   Ogni struttura dentro un'altra aggiunge livello          │
│   4 if annidati = 1+2+3+4 = 10 (non 4!)                   │
│                                                             │
│ NON INCREMENTA:                                             │
│   try (solo except), finally, lambda semplici, switch/case │
│                                                             │
│ BOOLEAN SEQUENCES:                                          │
│   a and b and c = +1 (stesso operatore)                    │
│   a and b or c  = +2 (cambio operatore)                    │
├─────────────────────────────────────────────────────────────┤
│ PATTERN AD ALTO IMPATTO:                                    │
│   1. Guard clauses      → elimina nesting penalty          │
│   2. Extract method     → resetta nesting a 0              │
│   3. Dictionary dispatch → if-elif chain → lookup O(1)     │
│   4. match/switch       → n branch = +1 totale             │
├─────────────────────────────────────────────────────────────┤
│ THRESHOLD RACCOMANDATI:                                     │
│   Strict (nuovo codice):  ≤ 10                             │
│   Standard (SonarQube):   ≤ 15                             │
│   Legacy (iniziale):      ≤ 25                             │
└─────────────────────────────────────────────────────────────┘
```
