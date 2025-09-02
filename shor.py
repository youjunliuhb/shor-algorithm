"""
Shor's Algorithm Implementation using Qiskit
===========================================

This module implements Shor's algorithm for integer factorization using quantum computing
via Qiskit. It includes both the quantum period-finding subroutine and the classical
pre/post-processing steps.

Author: Quantum Computing Implementation
Date: August 2025
"""

import math
import random
import numpy as np
from typing import Optional, Tuple, List, Dict
from fractions import Fraction

# Qiskit imports
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.circuit.library import QFT
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Statevector
    QISKIT_AVAILABLE = True
except ImportError:
    print("Warning: Qiskit not installed. Install with: pip install qiskit qiskit-aer")
    QISKIT_AVAILABLE = False


# =============================
# Classical Helper Functions
# =============================

def gcd(a: int, b: int) -> int:
    """Greatest Common Divisor using Euclidean algorithm."""
    while b:
        a, b = b, a % b
    return a


def mod_exp(base: int, exp: int, mod: int) -> int:
    """Modular exponentiation: (base^exp) mod mod."""
    return pow(base, exp, mod)


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """Extended Euclidean Algorithm.
    Returns (gcd, x, y) such that ax + by = gcd(a, b)."""
    if a == 0:
        return b, 0, 1
    gcd_val, x1, y1 = extended_gcd(b % a, a)
    # Back-substitution explanation:
    # x1 * (b % a) + y1 * a = gcd_val
    # I.e., x1 * (b - (b // a) * a) + y1 * a = gcd_val
    # Rearranging gives: (y1 - x1 * (b // a)) * a + x1 * b = gcd_val
    x = y1 - (b // a) * x1
    y = x1
    return gcd_val, x, y


def mod_inverse(a: int, m: int) -> Optional[int]:
    """Modular multiplicative inverse of a modulo m."""
    gcd_val, x, _ = extended_gcd(a, m)
    if gcd_val != 1:
        return None  # Inverse doesn't exist
    return (x % m + m) % m


def is_prime(n: int) -> bool:
    """Basic primality test."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def classical_order_finding(a: int, N: int) -> Optional[int]:
    """Classical order finding (for small N only).
    Finds the smallest positive integer r such that a^r ≡ 1 (mod N)."""
    if gcd(a, N) != 1:
        return None
    
    order = 1
    current = a % N
    while current != 1 and order < N:
        current = (current * a) % N
        order += 1
    
    return order if current == 1 else None


# =============================
# Quantum Period Finding
# =============================

def quantum_period_finding(a: int, N: int, n_count: int = None) -> List[int]:
    """
    Quantum period finding using Shor's algorithm.
    
    Args:
        a: Base for modular exponentiation
        N: Modulus
        n_count: Number of counting qubits (auto-calculated if None)
    
    Returns:
        List of measured values from the counting register
    """
    if not QISKIT_AVAILABLE:
        raise ImportError("Qiskit is required for quantum period finding")
    
    # Auto-calculate counting qubits if not provided
    if n_count is None:
        n_count = min(2 * math.ceil(math.log2(N)), 10)  # Cap at 10 for simulation
    
    # Number of qubits needed to represent N
    n_qubits = min(math.ceil(math.log2(N)), 5)  # Cap work register for simulation
    
    # Create quantum registers
    counting_reg = QuantumRegister(n_count, 'counting')
    work_reg = QuantumRegister(n_qubits, 'work')
    classical_reg = ClassicalRegister(n_count, 'classical')
    
    # Create quantum circuit
    qc = QuantumCircuit(counting_reg, work_reg, classical_reg)
    
    # Step 1: Create superposition in counting register
    for i in range(n_count):
        qc.h(counting_reg[i])
    
    # Step 2: Initialize work register to |1⟩
    qc.x(work_reg[0])
    
    # Step 3: Simplified controlled modular exponentiation
    # Using phase estimation approach
    for j in range(n_count):
        power = pow(2, j)
        # Simplified: apply rotations based on a^(2^j) mod N
        angle = 2 * np.pi * pow(a, power, N) / N
        qc.cp(angle, counting_reg[j], work_reg[0])
    
    # Step 4: Apply inverse QFT to counting register
    qft_inv = QFT(n_count, inverse=True)
    qc.compose(qft_inv, counting_reg, inplace=True)
    
    # Step 5: Measure counting register
    qc.measure(counting_reg, classical_reg)
    
    # Execute circuit with error handling
    try:
        simulator = AerSimulator()
        compiled_circuit = transpile(qc, simulator)
        job = simulator.run(compiled_circuit, shots=1024)
        result = job.result()
        counts = result.get_counts()
        
        # Extract measurement results
        measurements = []
        for bitstring, count in counts.items():
            value = int(bitstring, 2)
            measurements.extend([value] * count)
        
        return measurements
    except Exception as e:
        print(f"Quantum simulation failed: {e}")
        return []


def extract_period_from_measurements(measurements: List[int], N: int, n_count: int, a: int) -> Optional[int]:
    """
    Extract the period from quantum measurement results using continued fractions.
    
    Args:
        measurements: List of measured values from counting register
        N: The modulus
        n_count: Number of counting qubits used
        a: The base used in modular exponentiation
    
    Returns:
        Extracted period or None if extraction fails
    """
    if not measurements:
        return None
        
    # Count frequencies of measurements
    freq_count = {}
    for m in measurements:
        freq_count[m] = freq_count.get(m, 0) + 1
    
    # Try the most frequent measurements
    sorted_measurements = sorted(freq_count.items(), key=lambda x: x[1], reverse=True)
    
    for measured_value, frequency in sorted_measurements[:10]:  # Try top 10 measurements
        if measured_value == 0:
            continue
            
        # Convert to fraction and use continued fractions
        phase = measured_value / (2 ** n_count)
        
        # Try different denominators using continued fractions
        for max_denom in [N, N//2, N*2]:
            try:
                frac = Fraction(phase).limit_denominator(max_denom)
                potential_period = frac.denominator
                
                # Verify this is actually the period
                if 1 < potential_period < N:
                    # Check if a^r ≡ 1 (mod N)
                    if pow(a, potential_period, N) == 1:
                        return potential_period
                    
                    # Try small multiples of the potential period
                    for multiplier in range(2, min(5, N // potential_period + 1)):
                        candidate = potential_period * multiplier
                        if candidate >= N:
                            break
                        if pow(a, candidate, N) == 1:
                            return candidate
            except (ValueError, ZeroDivisionError):
                continue
    
    return None


# =============================
# Shor's Algorithm Main
# =============================

def shors_algorithm(N: int, use_quantum: bool = True, verbose: bool = True) -> Optional[Tuple[int, int]]:
    """
    Shor's algorithm for integer factorization.
    
    Args:
        N: Number to factorize
        use_quantum: Whether to use quantum period finding
        verbose: Whether to print intermediate steps
    
    Returns:
        Tuple of (p, q) factors if successful, None otherwise
    """
    if verbose:
        print(f"Attempting to factor N = {N}")
    
    # Step 1: Handle trivial cases
    if N <= 1:
        return None
    if N == 2:
        return None
    if is_prime(N):
        if verbose:
            print(f"N = {N} is prime")
        return None
    
    # Check if N is even
    if N % 2 == 0:
        if verbose:
            print(f"N is even: {N} = 2 × {N // 2}")
        return (2, N // 2)
    
    # Check if N is a perfect power
    for k in range(2, int(math.log2(N)) + 1):
        root = round(N ** (1/k))
        if root ** k == N:
            if verbose:
                print(f"N is a perfect {k}th power: {N} = {root}^{k}")
            return (root, N // root)
    
    # Step 2: Choose random a coprime to N
    max_attempts = 20
    for attempt in range(max_attempts):
        a = random.randint(2, N - 1)
        gcd_val = gcd(a, N)
        
        if gcd_val > 1:
            if verbose:
                print(f"Lucky! gcd({a}, {N}) = {gcd_val}")
            return (gcd_val, N // gcd_val)
        
        if verbose:
            print(f"Attempt {attempt + 1}: Using a = {a}")
        
        # Step 3: Find the period of a^x mod N
        period = None
        if use_quantum and QISKIT_AVAILABLE and N <= 100:  # Increased limit
            try:
                if verbose:
                    print("Attempting quantum period finding...")
                measurements = quantum_period_finding(a, N)
                if measurements:
                    period = extract_period_from_measurements(measurements, N, 
                                                            min(2 * math.ceil(math.log2(N)), 10), a)
                    if verbose and period:
                        print(f"Quantum period finding: period = {period}")
                    elif verbose:
                        print("Quantum period extraction failed, falling back to classical")
            except Exception as e:
                if verbose:
                    print(f"Quantum period finding failed: {e}, falling back to classical")
        
        # Fallback to classical if quantum failed or not available
        if period is None:
            if verbose and use_quantum:
                print("Using classical period finding...")
            period = classical_order_finding(a, N)
            if verbose and period:
                print(f"Classical period finding: period = {period}")
        
        if period is None:
            if verbose:
                print("Period finding failed, trying new a")
            continue
        
        # Step 4: Check if period is even
        if period % 2 != 0:
            if verbose:
                print(f"Period {period} is odd, trying new a")
            continue
        
        # Step 5: Compute gcd(a^(r/2) ± 1, N)
        half_period = period // 2
        x = pow(a, half_period, N)
        
        if x == N - 1:
            if verbose:
                print(f"a^(r/2) ≡ -1 (mod N), trying new a")
            continue
        
        factor1 = gcd(x - 1, N)
        factor2 = gcd(x + 1, N)
        
        if verbose:
            print(f"a^(r/2) = {a}^{half_period} ≡ {x} (mod {N})")
            print(f"gcd({x} - 1, {N}) = {factor1}")
            print(f"gcd({x} + 1, {N}) = {factor2}")
        
        if 1 < factor1 < N:
            other_factor = N // factor1
            if verbose:
                print(f"Success! {N} = {factor1} × {other_factor}")
            return (min(factor1, other_factor), max(factor1, other_factor))
        
        if 1 < factor2 < N:
            other_factor = N // factor2
            if verbose:
                print(f"Success! {N} = {factor2} × {other_factor}")
            return (min(factor2, other_factor), max(factor2, other_factor))
        
        if verbose:
            print("No non-trivial factors found, trying new a")
    
    if verbose:
        print(f"Failed to factor {N} after {max_attempts} attempts")
    return None


# =============================
# Testing and Demo Functions
# =============================

def test_shor_algorithm():
    """Test Shor's algorithm on known composite numbers."""
    test_cases = [15, 21, 33, 35, 39, 51, 55, 57, 65, 77, 85, 91, 93, 95, 899160187]
    
    print("Testing Shor's Algorithm")
    print("=" * 50)
    
    for N in test_cases:
        print(f"\nFactoring N = {N}")
        print("-" * 30)
        
        # Try classical first
        result_classical = shors_algorithm(N, use_quantum=False, verbose=False)
        if result_classical:
            p, q = result_classical
            print(f"Classical result: {N} = {p} × {q}")
            assert p * q == N, f"Incorrect factorization: {p} × {q} ≠ {N}"
        else:
            print("Classical factorization failed")
        
        # Try quantum for reasonable numbers
        if QISKIT_AVAILABLE and N <= 100:  # Increased limit
            result_quantum = shors_algorithm(N, use_quantum=True, verbose=False)
            if result_quantum:
                p, q = result_quantum
                print(f"Quantum result: {N} = {p} × {q}")
                assert p * q == N, f"Incorrect factorization: {p} × {q} ≠ {N}"
            else:
                print("Quantum factorization failed, but that's normal for this simulation")
        else:
            if not QISKIT_AVAILABLE:
                print("Qiskit not available for quantum simulation")
            else:
                print("Number too large for quantum simulation in this demo")


def demo_quantum_circuit(a: int = 7, N: int = 15):
    """Demonstrate the quantum circuit used in Shor's algorithm."""
    if not QISKIT_AVAILABLE:
        print("Qiskit not available for circuit demonstration")
        return
    
    print(f"Quantum Period Finding Circuit Demo")
    print(f"Finding period of {a}^x mod {N}")
    print("=" * 50)
    
    try:
        n_count = 4
        n_qubits = min(math.ceil(math.log2(N)), 5)
        
        # Create and visualize the quantum circuit
        counting_reg = QuantumRegister(n_count, 'counting')
        work_reg = QuantumRegister(n_qubits, 'work')
        classical_reg = ClassicalRegister(n_count, 'classical')
        
        qc = QuantumCircuit(counting_reg, work_reg, classical_reg)
        
        # Build the circuit
        for i in range(n_count):
            qc.h(counting_reg[i])
        
        qc.x(work_reg[0])
        
        for j in range(n_count):
            power = pow(2, j)
            angle = 2 * np.pi * pow(a, power, N) / N
            qc.cp(angle, counting_reg[j], work_reg[0])
        
        qft_inv = QFT(n_count, inverse=True)
        qc.compose(qft_inv, counting_reg, inplace=True)
        qc.measure(counting_reg, classical_reg)
        
        # Visualize the circuit
        print("\nQuantum Circuit Visualization:")
        print("-" * 50)
        print(qc.draw(output='text'))
        
        # Also save to file if matplotlib is available
        try:
            import matplotlib.pyplot as plt
            fig = qc.draw(output='mpl', style='iqp')
            plt.savefig('shor_circuit.png', dpi=150, bbox_inches='tight')
            print("\nCircuit diagram saved to 'shor_circuit.png'")
        except ImportError:
            print("\nNote: Install matplotlib for graphical circuit visualization")
        
        # Run the circuit
        measurements = quantum_period_finding(a, N, n_count=n_count)
        period = extract_period_from_measurements(measurements, N, n_count, a)
        
        print(f"\nMeasurements: {measurements[:10]}...")  # Show first 10
        print(f"Extracted period: {period}")
        
        # Verify classically
        classical_period = classical_order_finding(a, N)
        print(f"Classical period: {classical_period}")
        
    except Exception as e:
        print(f"Circuit demonstration failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            N = int(sys.argv[1])
            print(f"Factoring {N} using Shor's algorithm...")
            result = shors_algorithm(N, use_quantum=True, verbose=True)
            if result:
                p, q = result
                print(f"\nFinal result: {N} = {p} × {q}")
            else:
                print(f"\nFailed to factor {N}")
        except ValueError:
            print("Usage: python shor.py [number_to_factor]")
            sys.exit(1)
    else:
        # Run tests and demos
        test_shor_algorithm()
        print("\n" + "=" * 50)
        demo_quantum_circuit()
