import numpy as np
import matplotlib.pyplot as plt
import pyaudio

# --- CONFIGURATION ---
CHUNK = 1024 * 2             
FORMAT = pyaudio.paInt16     
CHANNELS = 1                 
RATE = 44100                 

# --- SETUP PYAUDIO ---
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# --- SETUP GEOMETRIC PLOT (POLAR) ---
# We use a Polar projection to make it circular
fig = plt.figure(figsize=(8, 8), facecolor='black') # Dark Mode Background
ax = plt.subplot(111, polar=True)
ax.set_facecolor('black')

# Create the angles (0 to 2pi) for the circle
# We need to map our frequency bins to these angles
n_bins = CHUNK // 2  # FFT returns half the chunk size
theta = np.linspace(0, 2 * np.pi, n_bins)

# Initialize the bars (visualizer spikes)
# We start with all zeros
bars = ax.bar(theta, np.zeros(n_bins), width=(2*np.pi/n_bins), bottom=0.0, color='cyan')

# Hide the ugly grid lines/labels to look like a reactor
ax.set_xticks([])
ax.set_yticks([])
ax.spines['polar'].set_visible(False) # Hide the outer circle line

print("Geometric Reactor Started... Make some noise!")

# --- THE REACTIVE LOOP ---
try:
    while True:
        # 1. Read & Process Data
        data = stream.read(CHUNK, exception_on_overflow=False)
        data_int = np.frombuffer(data, dtype=np.int16)
        
        # 2. FFT
        # Simple Hanning window
        windowed_data = data_int * np.hanning(len(data_int))
        fft_data = np.abs(np.fft.rfft(windowed_data)) 

        # 3. Log Scale & Threshold (Noise Gate)
        fft_data_log = 20 * np.log10(fft_data + 1e-10)
        threshold = 50
        fft_data_log[fft_data_log < threshold] = 0
        
        # 4. Normalize for the graph
        # We want the bars to bounce between 0 and 1
        # Assumes max volume is around 150dB
        heights = fft_data_log / 150 
        
        # 5. Update the Geometry
        # We only update the height of the existing bars
        for bar, height in zip(bars, heights):
            bar.set_height(height)
            
            # OPTIONAL: Color Reaction
            # Change color based on height (Loud = Red, Quiet = Cyan)
            if height > 0.7:
                bar.set_color('red')
            elif height > 0.4:
                bar.set_color('yellow')
            else:
                bar.set_color('cyan')

        # Slight pause to let Matplotlib breathe
        plt.pause(0.001)

except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()

    