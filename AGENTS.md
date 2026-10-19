# Brayton Simulator — instructions for Codex

These instructions apply to the entire repository and all future tasks performed here. Read this file and the relevant sections of `CODE_WALKTHROUGH.md` before making technical changes. Follow the user's explicit task scope; this policy does not authorize additional features or development phases.

## General principles

- This is an educational project for a fourth-year Aerospace Engineering student with basic Python knowledge.
- Explain why an implementation is used, not only what its code does.
- Keep physical assumptions, units, sign conventions, numerical tolerances and model limitations explicit.
- Do not present the simulator as a high-fidelity real-engine model.
- Distinguish code verification (checking implementation, equations and internal consistency) from validation against external physical or experimental data. Do not claim external validation from internal checks alone.
- Do not make commits unless the user explicitly requests them.

## Educational documentation requirement

`CODE_WALKTHROUGH.md` is the canonical educational explanation of this repository. Maintain it in Spanish, preserving a clear distinction between **PYTHON** and **INTERPRETACIÓN FÍSICA / INGENIERÍA**.

Whenever a task changes any of the following:

- Python source code;
- functions or function signatures;
- program flow;
- thermodynamic equations;
- physical assumptions;
- input parameters;
- validation rules;
- numerical methods;
- optimization methods;
- plots or generated outputs;
- file or module structure;
- dependencies;
- execution procedure;

the same task **MUST also update `CODE_WALKTHROUGH.md`** so that the document accurately describes the final state of the repository. This is part of completing the task and does not require a separate reminder from the user.

The educational document must never describe obsolete code as if it were current. Its main body must always explain the **CURRENT** version of the code. Do not turn it into a raw changelog or describe planned features as implemented.

Updates must explain both:

1. **PYTHON:** syntax, control flow, functions, data structures and relevant programming concepts.
2. **PHYSICS / ENGINEERING:** equations, assumptions, physical interpretation and meaning of the results. For infrastructure-only changes, explain their role and state when they do not change the physical model.

Explain new Python syntax at the level of a student with basic Python knowledge. Use short fragments of the actual code and small examples where helpful; do not invent functionality.

### Functions

For every new function, document:

- its complete signature;
- arguments and expected types;
- returned values and their structure;
- units;
- purpose;
- physical meaning and relevant equations, or its supporting role if it performs no physical calculation;
- relevant Python syntax;
- validation rules and possible errors;
- functions it calls;
- functions that call it, including the execution entry point where relevant;
- a small usage example.

When an existing function changes, update its existing explanation rather than creating a duplicate explanation. Remove or revise descriptions and call relationships for deleted or renamed functions.

### Synchronization without repetition

- Preserve the walkthrough's educational organization. Edit the existing authoritative explanation for each topic and use cross-references for detail already explained elsewhere.
- When files are added, removed, renamed or reorganized, update repository structure, execution flow and function/module relationships.
- When equations or physical assumptions change, update equation explanations, variable tables, code-to-equation mapping and model limitations.
- Review affected block descriptions, imports, dependencies, syntax explanations, parameters, numerical examples, plot descriptions, paths, execution instructions, exercises and solutions. Update affected content rather than rewriting unrelated sections.
- Recheck line references, file/function counts, signatures, callers and returned structures after code changes. Update or remove stale references.
- Recompute affected example results using the final implementation; distinguish verification performed in the current task from earlier verification. Report any checks that could not be completed honestly.

### Evolution of the project

Maintain a concise section at the end of `CODE_WALKTHROUGH.md` with this exact heading:

```markdown
## Evolution of the project
```

Record only important educational milestones that are actually implemented. Each entry must briefly explain the engineering and Python concepts introduced. Examples, only when implemented, include the initial ideal model, non-ideal component efficiencies, combustor pressure losses, design-domain analysis, non-ideal optimization and sensitivity analysis.

Do not record trivial formatting changes, invent historical dates or duplicate full explanations from the main body. Keep historical milestones clearly distinct from the description of current behavior.

### Workflow for future technical tasks

1. Read `AGENTS.md`.
2. Consult the relevant sections of `CODE_WALKTHROUGH.md`.
3. Perform exclusively the requested task.
4. Verify that the final code works with checks appropriate to the change; avoid unnecessarily overwriting generated outputs during verification.
5. Update the affected sections of `CODE_WALKTHROUGH.md` within the same task.
6. If the task represents a major academic milestone, create or update its document according to the milestone policy below.
7. Compare the documentation with the actual final code, equations, structure and results. Check references and examples for obsolete or contradictory explanations.
8. In the final response, identify the walkthrough sections and milestone documents updated; summarize verification performed and any remaining limitations.
9. Only if the user requests a commit, verify and include the code and its synchronized educational documentation in that same commit, following the Git policy below.

If a task does **not** modify the program or its technical interpretation, do not modify `CODE_WALKTHROUGH.md` unnecessarily.

If the user explicitly requests a temporary experiment that should not become part of the project, ask before documenting it as permanent functionality. Do not present that experiment as an implemented permanent feature while awaiting clarification.

## Git and educational history synchronization

Every commit that changes program behavior, structure, physical modeling, numerical methods or functionality must also contain the version of `CODE_WALKTHROUGH.md` that accurately explains the code in **that same commit**:

```text
Commit N   = code version N   + walkthrough explaining version N
Commit N+1 = code version N+1 + walkthrough explaining version N+1
```

- Update the walkthrough before making a functional commit and include the corresponding code and educational documentation together. Do not defer the walkthrough update to a later commit; a standalone correction of an existing documentation error is allowed.
- When the user requests a commit after technical changes, check the exact content to be committed, including staged files and partial staging. Verify that the walkthrough describes that snapshot, not merely the working tree. Resolve mismatches before committing; do not include unrelated changes without authorization.
- This policy does not authorize automatic commits. The existing requirement for an explicit user request still applies.
- Git preserves the complete historical versions of the code and walkthrough. Keep a single current `CODE_WALKTHROUGH.md`; do not create numbered copies such as `CODE_WALKTHROUGH_v1.md`, `CODE_WALKTHROUGH_v2.md` or equivalent version archives.

## Academic milestone documents

Use three complementary documentation layers:

- `CODE_WALKTHROUGH.md`: the detailed educational explanation of the current project.
- Git: the complete recorded history of code and its corresponding walkthrough for each committed version.
- `docs/milestones/`: brief educational summaries of major academic advances, not copies of the walkthrough.

Keep `docs/milestones/` available; create the directory only if it does not exist. Start milestone documents with the next major academic advance. Do not retrospectively reconstruct earlier stages unless the user requests it and the available evidence supports the account; do not invent historical states or dates.

For an implemented advance that introduces substantial engineering or programming learning, a task may create or update `docs/milestones/XX_nombre.md`. Choose a sequential number and descriptive name based on actual milestone documents, without reserving numbers for hypothetical features. Design-domain analysis, non-ideal optimization, sensitivity analysis, variable properties, fuel models and turbojet models are possible future examples, not implemented capabilities or authorization to develop them.

Do not create milestones for minor corrections, formatting, trivial renaming, small cleanups or changes without relevant academic learning. Keep each milestone concise and in Spanish, with the following structure:

```markdown
# Nombre del milestone

## Estado anterior
Qué podía hacer el simulador antes de este cambio.

## Qué se ha añadido
Nuevas capacidades introducidas.

## Nuevos conceptos de ingeniería
Conceptos de Termodinámica, Propulsión o análisis de diseño incorporados.

## Nuevos conceptos de Python
Sintaxis, estructuras de datos, métodos numéricos o técnicas de programación introducidas.

## Qué hemos aprendido
Principales conclusiones educativas.

## Limitaciones que siguen existiendo
Qué continúa sin modelarse o qué hipótesis permanecen.

## Commit asociado
Hash y mensaje del commit correspondiente cuando exista; pendiente si todavía no existe.
```

Record only verified commit hashes and messages. A file cannot contain the hash of its own enclosing commit in advance: leave the association pending until known and fill it in during a later authorized documentation update. Do not create or amend commits automatically just to fill in that field.

Keep the brief `Evolution of the project` section in the walkthrough synchronized with implemented major milestones, using references to milestone documents where useful instead of repeating their contents.
