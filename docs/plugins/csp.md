# CSP Plugin

> Solve complex scheduling, routing, and assignment problems that would take days to model from scratch. Expert constraint programming with Google OR-Tools CP-SAT.

## Agents

### `or-tools-expert`

Master constraint programmer specializing in modeling and solving complex optimization problems using Google OR-Tools CP-SAT.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | Constraint programming, scheduling, optimization, routing, assignment problems |

**Core capabilities:**
- **CSP Modeling** - Variables, domains, linear and global constraints
- **Scheduling** - Job shop, flow shop, nurse scheduling, resource allocation
- **Optimization** - Minimize/maximize objectives, multi-objective problems
- **Performance** - Parallel solving, hints, domain tightening, symmetry breaking
- **Debugging** - Infeasibility analysis, assumptions, solution enumeration

**Problem types:**
| Problem Type | Examples |
|--------------|----------|
| Scheduling | Job shop, nurse shifts, project scheduling (RCPSP) |
| Assignment | Task allocation, load balancing, bin packing |
| Routing | TSP, VRP, circuit problems |
| Classic CSP | N-Queens, Sudoku, graph coloring |
| Planning | Production planning, workforce optimization |

**Prerequisites:**
```bash
pip install ortools
# or with uv
uv add ortools
```

**Resources:**
- [OR-Tools Documentation](https://developers.google.com/optimization/cp)
- [CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/) - comprehensive guide
- [CP-SAT Log Analyzer](https://cpsat-log-analyzer.streamlit.app/)

---

**Related:** [python-development](python-development.md) (Python implementation patterns for constraint models)
