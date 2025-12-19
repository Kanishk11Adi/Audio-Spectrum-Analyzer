import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# 1. Load the real audio file
# MAKE SURE 'test_audio.wav' is in the same folder as this script!
try:
    sample_rate, data = wavfile.read('test_audio.wav')
    print(f"File loaded. Sample Rate: {sample_rate} Hz")
except FileNotFoundError:
    print("ERROR: Could not find 'test_audio.wav'. Please check the filename.")
    exit()

# 2. Handle Stereo vs Mono
# Real audio often has 2 channels (Left/Right). 
# We need to mix them into 1 channel (Mono) for a simple FFT.
if len(data.shape) > 1:
    print(f"Stereo file detected. Channels: {data.shape[1]}")
    data = data.mean(axis=1) # Average L and R channels
else:
    print("Mono file detected.")

# 3. Focus on a small slice (Audio files are huge!)
# Let's take just the first 1 second of audio to analyze
num_samples_to_take = sample_rate * 1 
data_slice = data[:num_samples_to_take]

# 4. Compute FFT (Same logic as before)
n = len(data_slice)
freqs = np.fft.fftfreq(n, d=1/sample_rate)
fft_values = np.fft.fft(data_slice)

magnitude = np.abs(fft_values) / n
half_n = n // 2
freqs_pos = freqs[:half_n]
magnitude_pos = magnitude[:half_n] * 2

# 5. Plot the Real Spectrum
plt.figure(figsize=(12, 6))
plt.plot(freqs_pos, magnitude_pos, color='blue')
plt.title("Frequency Spectrum of Real Audio")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")

# Audio usually lives in 20Hz - 20,000Hz. 
# Logarithmic scale is better for audio visualization
plt.xscale('log') 
plt.xlim(20, 20000) 
plt.grid(True, which="both")
plt.show()