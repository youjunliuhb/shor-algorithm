# Shor's Algorithm: Quantum Integer Factorization

This repository contains a complete implementation of Shor's algorithm for integer factorization using Qiskit. The implementation includes both the quantum period-finding subroutine and classical pre/post-processing components.

## Table of Contents
- [Overview](#overview)
- [Quantum Mechanics Behind Shor's Algorithm](#quantum-mechanics-behind-shors-algorithm)
- [Implementation Details](#implementation-details)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Limitations](#limitations)
- [Educational Notes](#educational-notes)

## Overview

Shor's algorithm, developed by Peter Shor in 1994, is a quantum algorithm for efficiently factoring large integers. This represents one of the most significant applications of quantum computing, as it can break RSA encryption in polynomial time on a quantum computer.

### Key Components:
1. **Classical preprocessing**: Handle trivial cases and choose random base
2. **Quantum period finding**: Use quantum interference to find the period of modular exponentiation
3. **Classical postprocessing**: Extract factors using the found period

## Quantum Mechanics Behind Shor's Algorithm

### 1. The Mathematical Foundation

Shor's algorithm exploits the mathematical relationship between factoring and period finding:

- **Goal**: Factor N = p × q (where p, q are unknown primes)
- **Key insight**: If we can find the period r of the function f(x) = a^x mod N, we can extract factors
- **Method**: If r is even and a^(r/2) ≢ ±1 (mod N), then gcd(a^(r/2) ± 1, N) gives non-trivial factors

### 2. Quantum Period Finding Circuit

The quantum subroutine creates a superposition and uses quantum interference to find the period:

```
|0⟩^n ⊗ |1⟩^m  →  (1/√2^n) Σ|x⟩ ⊗ |1⟩  →  (1/√2^n) Σ|x⟩ ⊗ |a^x mod N⟩
```

**Step-by-step quantum process:**

#### Step 1: Superposition Creation
```python
# Create equal superposition in counting register
for i in range(n_count):
    qc.h(counting_reg[i])
```
This creates the state: `(1/√2^n) Σ|x⟩|0⟩`

#### Step 2: Quantum Modular Exponentiation
```python
# Apply controlled-U^(2^j) operations
for j in range(n_count):
    # U|y⟩ = |ay mod N⟩
    apply_controlled_modular_exp(counting_reg[j], work_reg, a, 2**j, N)
```
This entangles the registers: `(1/√2^n) Σ|x⟩|a^x mod N⟩`

#### Step 3: Quantum Fourier Transform (QFT)
```python
# Apply inverse QFT to extract period information
qft_inv = QFT(n_count, inverse=True)
qc.compose(qft_inv, counting_reg, inplace=True)
```

### 3. Why Quantum Interference Works

The quantum magic happens because:

1. **Periodicity**: The function f(x) = a^x mod N has period r
2. **Constructive interference**: States |x⟩ and |x+r⟩ produce the same output |a^x mod N⟩
3. **QFT amplification**: The inverse QFT amplifies frequencies that correspond to multiples of 1/r
4. **Measurement**: High probability of measuring values close to k⋅2^n/r for integer k

### 4. Continued Fractions and Period Extraction

After measurement, we use continued fractions to extract the period:

```python
def extract_period_from_measurements(measurements, N, n_count):
    for measured_value in most_frequent_measurements:
        phase = measured_value / (2 ** n_count)
        frac = Fraction(phase).limit_denominator(N)
        potential_period = frac.denominator
        # Verify: a^r ≡ 1 (mod N)
```

## Implementation Details

### Core Functions

1. **`quantum_period_finding(a, N, n_count)`**: 
   - Creates quantum circuit for period finding
   - Uses n_count qubits for precision
   - Returns measurement results

2. **`extract_period_from_measurements(measurements, N, n_count)`**:
   - Processes quantum measurements
   - Uses continued fractions algorithm
   - Verifies candidate periods

3. **`shors_algorithm(N, use_quantum=True, verbose=True)`**:
   - Main algorithm implementation
   - Handles classical preprocessing
   - Calls quantum subroutine when needed
   - Performs classical postprocessing

### Circuit Architecture

```
Counting Register:  |0⟩ ──[H]── ●^(2^0) ── ●^(2^1) ── ... ── [QFT†] ── [M]
                               │          │
Work Register:      |1⟩ ───────U^(2^0) ───U^(2^1) ── ... ──────────── 
```

Where U|y⟩ = |ay mod N⟩ is the modular multiplication operator.

## Installation

### Prerequisites
- Python 3.8 or higher
- Qiskit and Qiskit Aer for quantum simulation

### Setup Instructions

1. **Clone or download the repository**
2. **Install required packages**:

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Qiskit
pip install qiskit qiskit-aer

# Optional: Install additional packages for better performance
pip install numpy matplotlib
```

3. **Verify installation**:
```powershell
python -c "import qiskit; print('Qiskit version:', qiskit.__version__)"
```

## Usage

### Command Line Interface

**Run tests on multiple numbers:**
```powershell
python shor.py
```

**Factor a specific number:**
```powershell
python shor.py 15
python shor.py 21
python shor.py 35
```

### Programmatic Usage

```python
from shor import shors_algorithm, quantum_period_finding

# Factor a number using Shor's algorithm
result = shors_algorithm(15, use_quantum=True, verbose=True)
if result:
    p, q = result
    print(f"15 = {p} × {q}")

# Use just the quantum period finding
measurements = quantum_period_finding(a=7, N=15, n_count=6)
print(f"Quantum measurements: {measurements}")
```

### Configuration Options

- **`use_quantum`**: Enable/disable quantum period finding
- **`verbose`**: Control output verbosity
- **`n_count`**: Number of counting qubits (affects precision)

## Examples

### Example 1: Factoring 15

```powershell
> python shor.py 15
Attempting to factor N = 15
Attempt 1: Using a = 7
Quantum period finding: period = 4
a^(r/2) = 7^2 ≡ 4 (mod 15)
gcd(4 - 1, 15) = 3
gcd(4 + 1, 15) = 5
Success! 15 = 3 × 5

Final result: 15 = 3 × 5
```

### Example 2: Understanding the Quantum Circuit

```python
# Demonstrate quantum circuit for specific case
demo_quantum_circuit(a=7, N=15)
```

Output shows:
- Quantum measurements from the counting register
- Period extraction using continued fractions
- Comparison with classical period finding

## Limitations

### Current Implementation
1. **Simulation constraints**: Limited to small numbers (N ≤ 21) due to simulator memory
2. **Simplified modular arithmetic**: Uses approximations for educational purposes
3. **Classical fallback**: Automatically switches to classical methods for larger numbers

### Theoretical Limitations
1. **Quantum hardware**: Real quantum computers have noise and limited connectivity
2. **Error correction**: Current implementation doesn't include quantum error correction
3. **Scalability**: Requires thousands of logical qubits for cryptographically relevant numbers

### Practical Considerations
1. **Number size**: RSA-2048 would require ~4000 logical qubits
2. **Gate count**: Millions of quantum gates needed for large factorizations
3. **Coherence time**: Quantum states must remain stable throughout computation

## Educational Notes

### Why Shor's Algorithm is Revolutionary

1. **Exponential speedup**: Classical algorithms are sub-exponential, Shor's is polynomial
2. **Cryptographic impact**: Breaks RSA, elliptic curve, and discrete log cryptography
3. **Quantum advantage**: Clear example where quantum computers outperform classical

### Key Quantum Concepts Demonstrated

1. **Superposition**: Creating equal probability amplitudes for all computational basis states
2. **Entanglement**: Correlating counting and work registers through controlled operations
3. **Interference**: Using QFT to amplify correct answers through constructive interference
4. **Measurement**: Extracting classical information from quantum states

### Learning Path

1. **Start with small examples**: 15, 21, 33, 35
2. **Understand classical components**: GCD, modular arithmetic, continued fractions
3. **Explore quantum circuit**: Study QFT and controlled operations
4. **Experiment with parameters**: Try different values of n_count and see effects

### Mathematical Deep Dive

The period finding works because:
- The state before QFT is: `Σ_{k=0}^{r-1} |kr_0/r⟩|a^{kr_0} mod N⟩`
- QFT creates constructive interference at multiples of 2^n/r
- Measurement gives values j ≈ k⋅2^n/r with high probability
- Continued fractions recovers r from the fraction j/2^n

### Performance Analysis

| N | Qubits Needed | Classical Time | Quantum Time* |
|---|---------------|----------------|---------------|
| 15 | ~8 | Instant | ~1000 gates |
| 2048-bit RSA | ~4000 | Age of universe | Hours** |

*On ideal quantum computer  
**With error correction

## Troubleshooting

### Common Issues

1. **Qiskit import errors**: Install with `pip install qiskit qiskit-aer`
2. **Memory errors**: Reduce n_count parameter or use smaller N
3. **No factors found**: Try running multiple times (probabilistic algorithm)

### Debug Mode

Enable verbose output to see intermediate steps:
```python
result = shors_algorithm(N, use_quantum=True, verbose=True)
```

### Performance Tips

1. **Use appropriate n_count**: More qubits = better precision but slower simulation
2. **Classical fallback**: For learning, classical period finding is often sufficient
3. **Batch testing**: Run multiple attempts for probabilistic success

---

## References

1. Shor, P. W. (1994). "Algorithms for quantum computation: discrete logarithms and factoring"
2. Nielsen, M. A., & Chuang, I. L. (2010). "Quantum Computation and Quantum Information"
3. Qiskit Documentation: https://qiskit.org/documentation/
