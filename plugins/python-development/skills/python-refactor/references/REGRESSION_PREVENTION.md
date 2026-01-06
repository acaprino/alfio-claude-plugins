# ⛔ REGRESSION PREVENTION GUIDE

> **PRINCIPIO FONDAMENTALE:** Il refactoring trasforma la STRUTTURA del codice, MAI il suo COMPORTAMENTO.
> Qualsiasi regressione tecnica, logica o funzionale è un FALLIMENTO TOTALE del refactoring.

---

## 🚨 MANDATORY PRE-REFACTORING CHECKLIST

**NON iniziare NESSUN refactoring finché TUTTI questi punti sono verificati:**

### 1. Test Coverage Assessment

```bash
# Verifica coverage attuale
pytest --cov=<module> --cov-report=term-missing

# Coverage minimo richiesto per procedere
# - >= 80%: Procedi con cautela normale
# - 60-80%: Procedi ma aggiungi test PRIMA di ogni modifica
# - < 60%: STOP! Scrivi test PRIMA di refactorare
```

- [ ] Coverage >= 80% sulle funzioni da modificare?
- [ ] Se NO → **PRIMA scrivi test, POI refactora**
- [ ] Test suite esistente passa al 100%?
- [ ] Esistono test per TUTTI gli edge cases critici?

### 2. Behavioral Baseline Capture

**PRIMA di toccare il codice, cattura il comportamento attuale:**

```python
# Salva output di riferimento per casi critici
import json

def capture_golden_outputs():
    """Esegui PRIMA del refactoring e salva i risultati."""
    test_cases = [
        # Casi normali
        {"input": normal_input_1, "description": "normal case 1"},
        {"input": normal_input_2, "description": "normal case 2"},
        # Edge cases CRITICI
        {"input": None, "description": "null input"},
        {"input": [], "description": "empty list"},
        {"input": "", "description": "empty string"},
        {"input": boundary_value, "description": "boundary condition"},
        # Casi di errore
        {"input": invalid_input, "description": "should raise ValueError"},
    ]
    
    results = []
    for case in test_cases:
        try:
            output = function_to_refactor(case["input"])
            results.append({
                "input": case["input"],
                "output": output,
                "exception": None,
                "description": case["description"]
            })
        except Exception as e:
            results.append({
                "input": case["input"],
                "output": None,
                "exception": {"type": type(e).__name__, "message": str(e)},
                "description": case["description"]
            })
    
    with open("golden_outputs_BEFORE_REFACTOR.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    return results
```

- [ ] Golden outputs salvati per funzioni critiche?
- [ ] Edge cases documentati e catturati?
- [ ] Comportamento con input invalidi documentato?

### 3. Edge Case Identification

**Per OGNI funzione da refactorare, identifica:**

```markdown
## Edge Cases per: function_name()

### Input Boundaries
- [ ] Input None/null
- [ ] Input vuoto ([], {}, "", 0)
- [ ] Input al limite (MAX_INT, stringa lunghissima)
- [ ] Input negativo (se applicabile)

### State Conditions  
- [ ] Prima chiamata (stato iniziale)
- [ ] Chiamate ripetute (stato accumulato)
- [ ] Stato corrotto/inconsistente

### Error Conditions
- [ ] Eccezioni attese (quali? quando?)
- [ ] Timeout/interruzioni
- [ ] Risorse non disponibili

### Concurrency (se applicabile)
- [ ] Race conditions note
- [ ] Deadlock potenziali
```

- [ ] Edge cases identificati per OGNI funzione?
- [ ] Comportamento attuale su edge cases DOCUMENTATO?

### 4. Static Analysis Baseline

```bash
# Cattura baseline PRIMA del refactoring
flake8 <file> --output-file=flake8_BEFORE.txt
python scripts/measure_complexity.py <file> --json > complexity_BEFORE.json
python scripts/check_documentation.py <file> --json > docs_BEFORE.json

# Per tracking storico (se disponibile)
wily build <src_dir>
wily report <file> > wily_BEFORE.txt
```

- [ ] Baseline flake8 catturata?
- [ ] Metriche di complessità salvate?
- [ ] Nessun errore critico pre-esistente nascosto?

---

## 🔄 MANDATORY POST-CHANGE CHECKLIST

**Dopo OGNI micro-cambiamento (non alla fine, OGNI SINGOLO!):**

### Immediate Verification (< 30 secondi)

```bash
# 1. Static analysis PRIMA dei test (cattura NameError immediati)
flake8 <file> --select=F821,F841,E999,E0602

# F821: undefined name (CRITICO - NameError garantito)
# F841: local variable assigned but never used (possibile bug)
# E999: syntax error (CRITICO - codice non eseguibile)
# E0602: undefined variable (CRITICO)

# 2. Se ZERO errori critici, esegui test
pytest <test_file> -x --tb=short

# -x = fail fast (stop al primo errore)
# --tb=short = traceback compatto
```

- [ ] `flake8 --select=F821,F841,E999` → ZERO errori?
- [ ] `pytest -x` → tutti i test passano?
- [ ] Se QUALSIASI fallimento → **REVERT IMMEDIATO**

### Per Ogni Guard Clause Aggiunta

Le guard clauses sono il pattern più comune ma anche il più insidioso per bug sottili:

```python
# PRIMA (nested)
def process(user):
    if user:
        if user.active:
            if user.verified:
                return do_work(user)
    return None

# DOPO (guard clauses) - VERIFICA EQUIVALENZA!
def process(user):
    if not user:           # Verifica: user=None → return None ✓
        return None
    if not user.active:    # Verifica: user.active=False → return None ✓
        return None
    if not user.verified:  # Verifica: user.verified=False → return None ✓
        return None
    return do_work(user)   # Verifica: tutti True → do_work() ✓
```

**Checklist per OGNI guard clause:**
- [ ] Input `None` → stesso comportamento di prima?
- [ ] Input con attributo `False` → stesso comportamento?
- [ ] Input valido → stesso risultato finale?
- [ ] Ordine delle condizioni preservato? (short-circuit evaluation!)

### Per Ogni Extract Method

```python
# PRIMA
def big_function(data):
    # ... 50 righe ...
    result = complex_calculation(x, y, z)
    # ... altre 30 righe ...

# DOPO
def big_function(data):
    # ... 
    result = _calculate_result(x, y, z)  # Estratto
    # ...

def _calculate_result(x, y, z):  # Nuova funzione
    return complex_calculation(x, y, z)
```

**Checklist per OGNI extract method:**
- [ ] TUTTI i parametri necessari passati?
- [ ] Variabili locali non più accessibili gestite?
- [ ] Return value correttamente propagato?
- [ ] Side effects preservati (se intenzionali)?
- [ ] Test specifico per la funzione estratta aggiunto?

---

## 🧪 EQUIVALENCE TESTING PATTERNS

### Pattern 1: Golden Master Testing

```python
import json
import pytest

class TestRefactoringEquivalence:
    """Verifica che il refactoring non cambi il comportamento."""
    
    @pytest.fixture
    def golden_outputs(self):
        with open("golden_outputs_BEFORE_REFACTOR.json") as f:
            return json.load(f)
    
    def test_all_golden_cases(self, golden_outputs):
        """Ogni output deve essere IDENTICO al golden master."""
        for case in golden_outputs:
            if case["exception"]:
                # Deve sollevare la STESSA eccezione
                with pytest.raises(eval(case["exception"]["type"])):
                    refactored_function(case["input"])
            else:
                # Deve produrre lo STESSO output
                result = refactored_function(case["input"])
                assert result == case["output"], \
                    f"Regression on {case['description']}: " \
                    f"expected {case['output']}, got {result}"
```

### Pattern 2: Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st, settings

# Per funzioni pure: output deve essere IDENTICO
@given(st.integers(), st.booleans(), st.text())
@settings(max_examples=1000)
def test_refactored_equals_original(x, flag, text):
    """Il refactoring NON deve cambiare il comportamento."""
    # Mantieni la vecchia implementazione commentata o in file separato
    expected = original_function(x, flag, text)
    actual = refactored_function(x, flag, text)
    assert actual == expected

# Per funzioni con side effects: verifica stato finale
@given(st.lists(st.integers()))
def test_state_equivalence(items):
    """Lo stato finale deve essere identico."""
    # Setup identico
    state_original = OriginalClass()
    state_refactored = RefactoredClass()
    
    # Stesse operazioni
    for item in items:
        state_original.process(item)
        state_refactored.process(item)
    
    # Stato finale identico
    assert state_original.get_state() == state_refactored.get_state()
```

### Pattern 3: Parallel Execution (per refactoring ad alto rischio)

```python
import functools

def verify_equivalence(original_func):
    """Decorator che esegue ENTRAMBE le versioni e confronta."""
    def decorator(refactored_func):
        @functools.wraps(refactored_func)
        def wrapper(*args, **kwargs):
            # Esegui originale
            original_result = original_func(*args, **kwargs)
            # Esegui refactored
            refactored_result = refactored_func(*args, **kwargs)
            # Confronta
            assert original_result == refactored_result, \
                f"REGRESSION DETECTED!\n" \
                f"Input: {args}, {kwargs}\n" \
                f"Original: {original_result}\n" \
                f"Refactored: {refactored_result}"
            return refactored_result
        return wrapper
    return decorator

# Uso durante sviluppo (rimuovere in produzione)
@verify_equivalence(original_calculate_discount)
def calculate_discount(price, tier):
    # Nuova implementazione refactored
    ...
```

---

## 📊 METRICS THAT MUST NOT REGRESS

### Hard Limits (violazione = rollback immediato)

| Metrica | Limite | Azione se violato |
|---------|--------|-------------------|
| Test pass rate | 100% | REVERT |
| F821 errors (undefined name) | 0 | REVERT |
| E999 errors (syntax) | 0 | REVERT |
| Performance degradation | < 10% | REVERT o approval esplicita |
| Coverage decrease | 0% | Aggiungi test prima di merge |

### Soft Limits (violazione = review richiesta)

| Metrica | Target | Azione se violato |
|---------|--------|-------------------|
| Cognitive complexity | ≤ 15 per funzione | Refactor further |
| Cyclomatic complexity | ≤ 10 per funzione | Refactor further |
| Function length | ≤ 30 righe | Extract methods |
| Nesting depth | ≤ 3 livelli | Guard clauses |

### Metrics Comparison Script

```bash
#!/bin/bash
# compare_regression.sh - Esegui PRIMA e DOPO refactoring

echo "=== REGRESSION CHECK ==="

# 1. Test pass rate
echo "Running tests..."
pytest --tb=no -q
if [ $? -ne 0 ]; then
    echo "❌ REGRESSION: Tests failing!"
    exit 1
fi
echo "✅ Tests passing"

# 2. Static analysis
echo "Running static analysis..."
ERRORS=$(flake8 $1 --select=F821,E999 --count 2>/dev/null | tail -1)
if [ "$ERRORS" != "0" ] && [ -n "$ERRORS" ]; then
    echo "❌ REGRESSION: Critical static analysis errors!"
    flake8 $1 --select=F821,E999
    exit 1
fi
echo "✅ No critical errors"

# 3. Compare complexity
echo "Comparing complexity..."
python scripts/compare_metrics.py $1_before.py $1_after.py

echo "=== REGRESSION CHECK COMPLETE ==="
```

---

## 🔙 ROLLBACK PROTOCOL

### When to Rollback Immediately

1. **ANY test failure** after a change
2. **ANY F821/E999 flake8 error**
3. **Performance degradation > 10%** without approval
4. **Behavioral change detected** (golden master mismatch)

### How to Rollback

```bash
# Se usando git (raccomandato: commit atomici per ogni micro-change)
git checkout -- <file>           # Discard uncommitted changes
git revert HEAD                   # Revert last commit
git reset --hard HEAD~1           # Nuclear option: discard last commit entirely

# Se non usando git: mantieni SEMPRE backup
cp <file> <file>.backup_YYYYMMDD_HHMM  # Prima di ogni sessione
```

### Post-Rollback Analysis

```markdown
## Rollback Report

**File:** <filename>
**Change attempted:** <description>
**Failure type:** Test failure / Static error / Performance / Behavioral

**Root cause analysis:**
- What was the specific error?
- Why wasn't it caught before commit?
- What check was missing?

**Prevention for future:**
- [ ] Add specific test case for this scenario
- [ ] Add to pre-change checklist
- [ ] Update golden master if needed
```

---

## 📋 QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────────┐
│                 REFACTORING SAFETY CHECKLIST                │
├─────────────────────────────────────────────────────────────┤
│ BEFORE ANY CHANGE:                                          │
│ □ Tests passing 100%?                                       │
│ □ Coverage >= 80% on target code?                           │
│ □ Golden outputs captured?                                  │
│ □ Edge cases identified?                                    │
├─────────────────────────────────────────────────────────────┤
│ AFTER EACH MICRO-CHANGE:                                    │
│ □ flake8 --select=F821,E999 → 0 errors?                    │
│ □ pytest -x → all passing?                                  │
│ □ Behavior unchanged? (spot check 1 edge case)             │
├─────────────────────────────────────────────────────────────┤
│ BEFORE COMMIT:                                              │
│ □ All tests passing?                                        │
│ □ Golden master comparison passed?                          │
│ □ No performance regression?                                │
│ □ Metrics improved or unchanged?                            │
├─────────────────────────────────────────────────────────────┤
│ IF ANY CHECK FAILS:                                         │
│ → STOP → REVERT → ANALYZE → FIX APPROACH → RETRY           │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ COMMON REGRESSION TRAPS

### Trap 1: Short-Circuit Evaluation Changes

```python
# PRIMA: second_check() MAI chiamata se first_check() è False
if first_check() and second_check():
    ...

# DOPO (SBAGLIATO!): second_check() SEMPRE chiamata
if all([first_check(), second_check()]):  # ❌ Cambia comportamento!
    ...

# DOPO (CORRETTO): preserva short-circuit
if first_check() and second_check():  # ✓ Identico
    ...
```

### Trap 2: Exception Handling Scope

```python
# PRIMA: gestisce SOLO ValueError
try:
    risky_operation()
except ValueError:
    handle_error()

# DOPO (SBAGLIATO!): gestisce TUTTE le eccezioni
try:
    risky_operation()
except Exception:  # ❌ Troppo ampio!
    handle_error()
```

### Trap 3: Mutable Default Arguments

```python
# PRIMA (bug, ma comportamento "atteso" dal sistema)
def append_to(item, lst=[]):
    lst.append(item)
    return lst

# DOPO (corretto, ma CAMBIA COMPORTAMENTO!)
def append_to(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# ⚠️ Se il sistema DIPENDEVA dal bug, questo è breaking change!
```

### Trap 4: Return Value Changes

```python
# PRIMA: ritorna None implicitamente se condizione falsa
def get_user(user_id):
    if user_id in cache:
        return cache[user_id]
    # Implicit return None

# DOPO (SBAGLIATO se caller controlla "if result:")
def get_user(user_id):
    if user_id not in cache:
        return User.empty()  # ❌ Ora ritorna oggetto truthy!
    return cache[user_id]
```

---

**REMEMBER:** Un refactoring che introduce regressioni non è un refactoring. È un bug.
