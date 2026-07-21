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

from qiskit import QuantumCircuit, transpile
import matplotlib.pyplot as plt

from qiskit_quantuminspire.qi_provider import QIProvider

SHOTS = 4096


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


def run_benchmark(backend_name: str, sizes=(2, 3, 4, 5)) -> dict:
    provider = QIProvider()
    print("Available backends:", [b.name for b in provider.backends()])
    backend = provider.get_backend(backend_name)
    shots = min(SHOTS, backend.max_shots)

    results = {}
    for n in sizes:
        qc = transpile(ghz_circuit(n), backend)
        job = backend.run(qc, shots=shots)
        counts = job.result().get_counts()
        fid = ghz_fidelity(counts, n)
        results[n] = fid
        print(f"{backend_name} | {n} qubits | GHZ fidelity: {fid:.3f}")
    return results


def plot(all_results: dict):
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
    plt.savefig("ghz_fidelity.png", dpi=150)
    print("Saved ghz_fidelity.png")


if __name__ == "__main__":
    all_results = {}

    # 1. Start on the emulator (fast, ideal-ish)
    all_results["QX emulator"] = run_benchmark("QX emulator")

    # 2. Then uncomment for real hardware (queued jobs, be patient)
    # all_results["Tuna-5"] = run_benchmark("Tuna-5", sizes=(2, 3, 4, 5))
    # all_results["Tuna-17"] = run_benchmark("Tuna-17", sizes=(2, 3, 5, 8, 12))

    plot(all_results)
