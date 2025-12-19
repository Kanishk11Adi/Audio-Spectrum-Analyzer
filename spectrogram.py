import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# 1. Load the File
filename = 'test_audio.wav' 
sample_rate, data = wavfile.read(filename)

# 2. Convert to Mono (if stereo)
if len(data.shape) > 1:
    data = data.mean(axis=1)

# 3. Create the Spectrogram
# We don't slice the data this time; we want to see the whole file!
plt.figure(figsize=(12, 6))

# NFFT = Block size (256, 512, 1024, etc). Smaller = better time resolution, worse freq resolution.
# Fs = Sampling rate
# noverlap = How much the blocks overlap (smoothes the image)
Pxx, freqs, bins, im = plt.specgram(data, NFFT=1024, Fs=sample_rate, noverlap=512, cmap='inferno')

plt.title(f"Spectrogram Analysis of {filename}")
plt.xlabel("Time (seconds)")
plt.ylabel("Frequency (Hz)")

# Audio is mostly below 10kHz, so let's zoom in on the useful part
plt.ylim(0, 10000) 

plt.colorbar(label="Intensity (dB)")
plt.show()