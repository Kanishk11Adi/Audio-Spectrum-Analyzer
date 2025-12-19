import numpy as np
import pyaudio
import pygame
import math
import random

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 800
FPS = 60
CHUNK = 1024 
RATE = 44100
BARS = 180                  # More bars = smoother line
RADIUS = 150                # Base size of the blob

# --- COLOR PALETTE ---
CYAN = (0, 255, 255)
PURPLE = (180, 50, 255)
DEEP_BLUE = (10, 10, 30)

# --- SETUP PYAUDIO ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

# --- SETUP PYGAME ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V3: Vortex Blob Reactor")
clock = pygame.time.Clock()

# --- PARTICLE SYSTEM ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # Start at random angle and random distance near center
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(10, 50) 
        self.size = random.uniform(2, 5)
        self.speed = random.uniform(0.02, 0.05)
        self.color = random.choice([CYAN, PURPLE, (255, 255, 255)])
        
    def update(self, bass_energy):
        # Spin around the center
        self.angle += self.speed
        
        # If bass hits, push particle outward
        push = bass_energy * 10 
        self.dist += push
        
        # Slowly drift back to center or reset if too far
        if self.dist > 250: # If it flies out of the blob, reset it
            self.reset()
        else:
            self.dist *= 0.95 # Gravity pulls it back in

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

# Create a swarm of 100 particles
particles = [Particle() for _ in range(100)]

# --- SMOOTHING ---
prev_heights = np.zeros(BARS)
global_rotation = 0 # To spin the whole blob

def get_audio_data():
    try:
        data = stream.read(CHUNK, exception_on_overflow=False)
        data_int = np.frombuffer(data, dtype=np.int16)
        window = np.hanning(len(data_int))
        data_int = data_int * window
        fft_data = np.abs(np.fft.rfft(data_int))
        fft_data = 20 * np.log10(fft_data + 1e-10)
        fft_data = fft_data[:BARS] 
        fft_data = np.clip((fft_data - 30) / 100, 0, 1) 
        return fft_data
    except:
        return np.zeros(BARS)

# --- MAIN LOOP ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Get Audio
    audio_levels = get_audio_data()
    # Smooth the movement
    prev_heights = prev_heights * 0.5 + audio_levels * 0.5
    
    # Calculate Bass Energy (for the particles)
    bass_energy = np.mean(prev_heights[:10]) # Average of low freqs

    # 2. Draw Background
    # Create a trailing effect (semi-transparent fill)
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.set_alpha(30) # 30/255 transparency -> creates "trails"
    fade_surface.fill(DEEP_BLUE)
    screen.blit(fade_surface, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Update & Draw Particles (The Vortex)
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    # 4. Draw The Shapeless Line (The Blob)
    points = []
    global_rotation += 0.01 + (bass_energy * 0.05) # Spin faster when loud
    
    for i in range(BARS):
        # Distribute points around the circle
        angle = (2 * math.pi * i) / BARS + global_rotation
        
        # Calculate dynamic radius
        # Base Radius + (Audio Volume * Scale)
        r = RADIUS + (prev_heights[i] * 150)
        
        # Polar to Cartesian conversion
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    # Connect the dots to form a closed loop
    if len(points) > 2:
        pygame.draw.lines(screen, CYAN, True, points, 3) # True = Closed loop
        
        # Optional: Draw a second mirrored line for "Neon" effect
        pygame.draw.lines(screen, PURPLE, True, [(x+5, y+5) for x,y in points], 1)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()