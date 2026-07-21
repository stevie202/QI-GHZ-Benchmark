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

On the emulator, fidelity stays ~1.0. On real hardware it droops as circuits grow —
limited qubit connectivity forces SWAP insertion during transpilation, and deeper
circuits accumulate more noise. That decay curve is the point of the project.

## Requirements

- Python 3.10+
- A free [Quantum Inspire account](https://www.quantum-inspire.com/)

````
py -m pip install qiskit qiskit-quantuminspire matplotlib
````

## Setup

Authenticate once (opens a browser):

````
qi login
````

No credentials are stored in this repo — tokens live in your user profile
via the `qi` CLI.

## Usage

````
py qi_bell_benchmark.py
````

Runs GHZ sizes 2–5 on the QX emulator by default. Uncomment the Tuna lines in
`__main__` for real hardware (jobs queue, expect a wait).

**Hardware note:** circuits must be transpiled to the chip's topology before
submission — `transpile(qc, backend)` handles qubit mapping and SWAP routing.
Submitting a raw linear-chain GHZ to Tuna fails with a qubit-interaction
mapping error.

## Output

- Per-backend fidelity printed to console
- `ghz_fidelity.png` — fidelity decay chart

## Roadmap

- [ ] Tuna-5 / Tuna-9 / Tuna-17 hardware comparison
- [ ] Circuit depth vs fidelity (transpilation cost per backend)
- [ ] Web dashboard for results
````
````

And the matching `.gitignore`:

````
__pycache__/
.venv/
.env
*.png
qi-config*.json
````

The Roadmap section doubles as your project plan — tick items off as commits land. Suggested repo name: `qi-ghz-benchmark`.