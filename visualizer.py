 import numpy as np # type: ignore
import matplotlib.pyplot as plt # type: ignore

# 1. Setup the "Digital" Environment
sample_rate = 44100  # Standard audio sampling rate (Hz)
duration = 0.1       # Duration in seconds (short, for zooming in)
t = np.linspace(0, duration, int(sample_rate * duration))

# 2. Create two distinct signals
# Low frequency (Bass) - 50 Hz
f1 = 50 
signal_low = np.sin(2 * np.pi * f1 * t)

# High frequency (Treble) - 1000 Hz
f2 = 1000
signal_high = 0.5 * np.sin(2 * np.pi * f2 * t) # 0.5 amplitude (quieter)

# 3. Mix them together (Superposition)
mixed_signal = signal_low + signal_high

# 4. Visualize the result
plt.figure(figsize=(10, 4))
plt.plot(t, mixed_signal)
plt.title(f"Composite Digital Signal ({f1}Hz + {f2}Hz)")
plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()

# ... (Keep all your previous code from Phase 1) ...

# 5. Compute the FFT (The DSP Magic)
n = len(mixed_signal)                 # Total number of samples
freqs = np.fft.fftfreq(n, d=1/sample_rate) # Get the frequency axis
fft_values = np.fft.fft(mixed_signal)      # Compute the transform

# 6. Clean up the data
# FFT returns complex numbers; we only want the Magnitude (absolute value)
magnitude = np.abs(fft_values) / n 

# FFT returns both positive and negative frequencies (mirror image).
# We only need the positive half.
half_n = n // 2
freqs_pos = freqs[:half_n]
magnitude_pos = magnitude[:half_n] * 2 # *2 to conserve total energy

# 7. Plot the Frequency Spectrum
plt.figure(figsize=(10, 4))
plt.plot(freqs_pos, magnitude_pos, color='red')
plt.title("Frequency Spectrum (FFT Analysis)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.xlim(0, 1200) # Limit x-axis to 1200Hz so we can see our signals clearly
plt.grid(True)
plt.show()

