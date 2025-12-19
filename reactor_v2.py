import numpy as np
import pyaudio
import pygame
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 800    # Window Size
FPS = 60                    # 60 Frames Per Second (Smooth!)
CHUNK = 1024                # Buffer Size
RATE = 44100
BARS = 120                  # Number of "Spikes"
RADIUS = 120                # Size of the center circle

# --- SETUP PYAUDIO ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

# --- SETUP PYGAME ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometric Reactor V2 (High Performance)")
clock = pygame.time.Clock()

# --- SMOOTHING VARIABLES ---
# This array remembers how tall every bar was in the LAST frame
prev_heights = np.zeros(BARS) 

def get_audio_data():
    """Captures audio and returns frequency magnitude."""
    try:
        data = stream.read(CHUNK, exception_on_overflow=False)
        data_int = np.frombuffer(data, dtype=np.int16)
        
        # Window function prevents "spectral leakage" (cleanup)
        window = np.hanning(len(data_int))
        data_int = data_int * window
        
        # FFT (The math you already know)
        fft_data = np.abs(np.fft.rfft(data_int))
        
        # Convert to Decibels
        fft_data = 20 * np.log10(fft_data + 1e-10)
        
        # Focus on the music frequencies (Bass/Mids), ignore high hiss
        fft_data = fft_data[:BARS] 
        
        # Normalization (Scale roughly 0 to 1)
        fft_data = np.clip((fft_data - 30) / 100, 0, 1) 
        
        return fft_data
    except:
        return np.zeros(BARS)

# --- MAIN LOOP ---
running = True
while running:
    # 1. Handle Window Closing
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Get Audio Data
    audio_levels = get_audio_data()
    
    # 3. PHYSICS ENGINE (Gravity)
    # This is what fixes the "childish" jerky movement.
    # We don't jump straight to the new height. We ease into it.
    # 0.6 = Decay speed (Lower is smoother/slower, Higher is snappier)
    prev_heights = prev_heights * 0.6 + audio_levels * 0.4
    
    # 4. Draw Everything
    screen.fill((10, 10, 15)) # Dark background
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    for i in range(BARS):
        # Calculate angle for this bar
        angle = (2 * math.pi * i) / BARS
        
        # Get smoothed height
        h = prev_heights[i] * 250 # Scale up
        
        # Calculate Start point (On the circle ring)
        start_x = center_x + math.cos(angle) * RADIUS
        start_y = center_y + math.sin(angle) * RADIUS
        
        # Calculate End point (Projecting outwards)
        end_x = center_x + math.cos(angle) * (RADIUS + h)
        end_y = center_y + math.sin(angle) * (RADIUS + h)
        
        # Dynamic Color Logic
        # Quiet = Blue, Loud = Pink/Purple
        intensity = min(255, int(prev_heights[i] * 255))
        color = (intensity, 50, 255 - intensity)
        
        # Draw the line
        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 4)

    # 5. The "Thumping" Bass Circle
    # We take the average of the first 5 bars (Deep Bass) to pulse the center
    bass_energy = np.mean(prev_heights[:5]) 
    pulse_size = RADIUS + (bass_energy * 30)
    
    # Draw the center circle
    pygame.draw.circle(screen, (20, 20, 40), (center_x, center_y), int(pulse_size))
    # Draw a thin glowing ring around it
    pygame.draw.circle(screen, (50, 50, 255), (center_x, center_y), int(pulse_size), 2)
    
    # Update Display
    pygame.display.flip()
    clock.tick(FPS)

# Quit properly
stream.stop_stream()
stream.close()
p.terminate()
pygame.quit()