"""
Quantum Inspire Bell/GHZ benchmark starter.

Runs Bell and GHZ circuits on a chosen backend (emulator or Tuna hardware),
compares measured histograms to the ideal 50/50 |00...0> / |11...1> split,
and reports a simple fidelity score per backend.

Setup (once):
    py -m pip install qiskit qiskit-quantuminspire matplotlib
    qi login          # opens browser to authenticate with your QI account

Note: Zscaler may require adding your corp CA bundle via REQUESTS_CA_BUNDLE
if SSL errors appear.
"""

import argparse
import json
import time
from datetime import datetime, timezone

from qiskit import QuantumCircuit, transpile
from qiskit.providers.exceptions import JobTimeoutError
from qiskit.providers.jobstatus import JOB_FINAL_STATES
import matplotlib.pyplot as plt

from qiskit_quantuminspire.qi_provider import QIProvider

SHOTS = 4096
BACKENDS = ["QX emulator", "Tuna-5", "Ry emulator", "Tuna-9", "Tuna-17"]
DEFAULT_SIZES = {
    "Tuna-17": (2, 3, 5, 8, 12),
}
RESULTS_LOG = "results.jsonl"

# job.result()'s own default timeout is a mere 60s — too short once a job queues
# behind other users on real hardware. Poll ourselves instead, with progress
# printed so a multi-minute wait doesn't look hung.
JOB_TIMEOUT = 1800  # seconds
POLL_EVERY = 15  # seconds between status checks
PRINT_EVERY = 60  # seconds between progress lines


def wait_for_job(job, timeout=JOB_TIMEOUT):
    start = time.time()
    last_print = start
    status = job.status()
    while status not in JOB_FINAL_STATES:
        elapsed = time.time() - start
        if elapsed >= timeout:
            raise JobTimeoutError(f"Timed out after {timeout}s waiting for job {job.job_id()} ({status.name})")
        if time.time() - last_print >= PRINT_EVERY:
            print(f"  ...still {status.name.lower()} ({int(elapsed)}s elapsed)")
            last_print = time.time()
        time.sleep(POLL_EVERY)
        status = job.status()
    return status


def ghz_circuit(n: int) -> QuantumCircuit:
    """Bell state for n=2, GHZ for n>=3."""
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n), range(n))
    return qc


def ghz_fidelity(counts: dict, n: int) -> float:
    """Fraction of shots landing in the two ideal GHZ outcomes."""
    zeros = "0" * n
    ones = "1" * n
    good = counts.get(zeros, 0) + counts.get(ones, 0)
    return good / sum(counts.values())


def log_result(backend_name: str, n: int, fidelity: float, shots: int, run_timestamp: str):
    entry = {
        "timestamp": run_timestamp,
        "backend": backend_name,
        "n_qubits": n,
        "fidelity": fidelity,
        "shots": shots,
    }
    with open(RESULTS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_benchmark(backend_name: str, sizes=(2, 3, 4, 5)) -> dict:
    provider = QIProvider()
    print("Available backends:", [b.name for b in provider.backends()])
    backend = provider.get_backend(backend_name)
    shots = min(SHOTS, backend.max_shots)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    results = {}
    for n in sizes:
        qc = transpile(ghz_circuit(n), backend)
        job = backend.run(qc, shots=shots)
        try:
            wait_for_job(job)
        except JobTimeoutError as e:
            print(f"{backend_name} | {n} qubits | {e} — skipping (check later with `qi results get {job.job_id()}`)")
            continue
        counts = job.result().get_counts()
        fid = ghz_fidelity(counts, n)
        results[n] = fid
        print(f"{backend_name} | {n} qubits | GHZ fidelity: {fid:.3f}")
        log_result(backend_name, n, fid, shots, run_timestamp)
    return results


def plot(all_results: dict, backend_name: str):
    """all_results: {backend_name: {n_qubits: fidelity}}"""
    for name, res in all_results.items():
        ns = sorted(res)
        plt.plot(ns, [res[n] for n in ns], marker="o", label=name)
    plt.axhline(1.0, color="grey", ls="--", lw=0.8)
    plt.xlabel("GHZ state size (qubits)")
    plt.ylabel("Fidelity (fraction in ideal outcomes)")
    plt.title("Ideal vs real hardware: GHZ fidelity decay")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    filename = f"ghz_fidelity_{backend_name.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the GHZ fidelity benchmark on a Quantum Inspire backend.")
    parser.add_argument("backend", choices=BACKENDS, help="Backend to benchmark")
    args = parser.parse_args()

    sizes = DEFAULT_SIZES.get(args.backend, (2, 3, 4, 5))
    results = {args.backend: run_benchmark(args.backend, sizes=sizes)}
    plot(results, args.backend)
