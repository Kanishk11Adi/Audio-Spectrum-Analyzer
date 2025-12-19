import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import struct

# --- CONFIGURATION ---
CHUNK = 1024 * 2             # How many audio samples to read at a time (Buffer size)
FORMAT = pyaudio.paInt16     # Audio format (16-bit)
CHANNELS = 1                 # Mono audio
RATE = 44100                 # Sampling rate (Hz)

# --- SETUP PYAUDIO ---
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# --- SETUP PLOT ---
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(0, 2 * CHUNK, 2)       # Frequency axis (approx)
line, = ax.plot(x, np.random.rand(CHUNK), '-', lw=2)

# Styling
ax.set_title('Real-Time Audio Spectrum (Press Ctrl+C in Terminal to Stop)')
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Volume')
ax.set_ylim(0, 255)         # Fixed Volume Scale
ax.set_xlim(20, 4000)       # Focus on 20Hz - 4000Hz (Where most music is)
plt.grid(True)

print("Stream started... Play some music!")

# --- THE MAIN LOOP ---
try:
    while True:
        # 1. Read binary data
        data = stream.read(CHUNK, exception_on_overflow=False)
        data_int = np.frombuffer(data, dtype=np.int16)
        
        # 2. Compute FFT
        windowed_data = data_int * np.hanning(len(data_int))
        fft_data = np.abs(np.fft.rfft(windowed_data)) 

        # 3. Convert to dB
        fft_data_log = 20 * np.log10(fft_data + 1e-10)

        # --- THE NOISE GATE (NEW) ---
        # Adjust this number! If the "dancing" is still there, make this 60 or 70.
        threshold = 60 
        
        # This is a "Vectorized Operation" (very fast)
        # It says: "Wherever the data is less than threshold, set it to 0"
        fft_data_log[fft_data_log < threshold] = 0
        # -----------------------------

        # 4. Update the plot
        line.set_ydata(fft_data_log)
        line.set_xdata(np.linspace(0, RATE/2, len(fft_data_log)))
        
        # Make sure the graph floor matches our gate (so 0 looks like 0)
        ax.set_ylim(0, 150) 
        
        plt.pause(0.001)

except KeyboardInterrupt:
    print("\nStopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()