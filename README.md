# Quantum Inspire Bell/GHZ Benchmark

Benchmarks entanglement fidelity on [Quantum Inspire](https://www.quantum-inspire.com/)
(QuTech) by running Bell and GHZ circuits of increasing size on the QX emulator and
Tuna quantum chips, then charting how fidelity decays on real hardware versus the
ideal baseline.

## What it does

- Builds Bell (2-qubit) and GHZ (3+ qubit) circuits in Qiskit
- Runs them on a chosen backend (QX emulator, Tuna-5, Tuna-9, Tuna-17)
- Scores each run by GHZ fidelity: the fraction of shots landing in the two
  ideal outcomes (`00…0` / `11…1`)
- Plots fidelity vs GHZ size per backend (`ghz_fidelity.png`)
- Logs every run to `results.jsonl` and visualizes history in a Streamlit dashboard

On the emulator, fidelity stays ~1.0. On real hardware it droops as circuits grow —
limited qubit connectivity forces SWAP insertion during transpilation, and deeper
circuits accumulate more noise. That decay curve is the point of the project.

## Requirements

- Python 3.10+ (avoid brand-new Python releases — numpy/qiskit wheels lag behind;
  if `pip install` tries to compile from source, switch to an older interpreter)
- A free [Quantum Inspire account](https://www.quantum-inspire.com/)
- [pipx](https://pipx.pypa.io/stable/installation) (for installing the `qi` CLI)

````
py -m pip install qiskit qiskit-quantuminspire matplotlib streamlit plotly pandas pylatexenc
pipx install quantuminspire
````

`qiskit-quantuminspire` is the Qiskit provider library used by the script.
The `qi` CLI is a separate package (`quantuminspire` on PyPI) that only handles
login/auth — it isn't pulled in by the provider install above.

## Setup

Authenticate once (opens a browser):

````
qi login
````

No credentials are stored in this repo — tokens live in your user profile
via the `qi` CLI.

## Usage

````
py qi_bell_benchmark.py "QX emulator"
````

Pass one of `"QX emulator"`, `"Tuna-5"`, `"Ry emulator"`, `"Tuna-9"`, `"Tuna-17"`
as the backend argument (quote names containing spaces). GHZ sizes default to
2–5, except Tuna-17 which runs 2, 3, 5, 8, 12. Hardware jobs queue — expect a
wait; the script polls for up to 30 minutes per job and prints a progress
line every minute so it doesn't look hung. If a job still hasn't finished
after 30 minutes it's skipped (not the whole run) — check on it later with
`qi results get <job_id>` (the job ID is printed when this happens).

**Hardware note:** circuits must be transpiled to the chip's topology before
submission — `transpile(qc, backend)` handles qubit mapping and SWAP routing.
Submitting a raw linear-chain GHZ to Tuna fails with a qubit-interaction
mapping error.

## Output

- Per-backend fidelity printed to console
- `ghz_fidelity_<backend>.png` — fidelity decay chart for the selected backend
  (e.g. `ghz_fidelity_QX_emulator.png`)
- `results.jsonl` — one line per (backend, GHZ size) result, appended on every
  run: timestamp, backend, n_qubits, fidelity, shots. Not committed by default
  (see `.gitignore`) since it's a per-machine run history.

## Dashboard

````
py -3.12 -m streamlit run dashboard.py
````

Opens with a short explainer (GHZ circuit diagram, ideal outcome split, and
at-a-glance stats across the full run history), then reads `results.jsonl`
and shows, per backend: latest fidelity vs GHZ size, fidelity over time at
the largest size tested (useful for spotting hardware drift/decay across
days), and a raw results table. Filter backends from the sidebar. Run
`qi_bell_benchmark.py` at least once first — the dashboard shows a message
if the log is empty. `pylatexenc` (in the install line above) is what
qiskit's circuit drawer needs to render the explainer diagram.

## Roadmap

- [ ] Tuna-5 / Tuna-9 / Tuna-17 hardware comparison
- [ ] Circuit depth vs fidelity (transpilation cost per backend)