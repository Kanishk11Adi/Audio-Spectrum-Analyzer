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
BARS = 180                  
RADIUS = 150                

# --- COLORS ---
CYAN = (0, 255, 255)
PURPLE = (180, 50, 255)
WHITE = (255, 255, 255)
RED = (255, 50, 50)

# --- SETUP AUDIO & SCREEN ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V4: Reactive Chaos Vortex")
clock = pygame.time.Clock()

# --- PARTICLE CLASS ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(20, 80) # Start closer to center
        self.size = random.uniform(2, 6)
        self.color = random.choice([CYAN, PURPLE, WHITE])
        self.original_dist = self.dist # Remember where it belongs
        
    def update(self, bass, treble):
        # 1. ROTATION (Controlled by BASS)
        # If bass is low, spin slow. If bass is high, spin FAST.
        rotation_speed = 0.01 + (bass * 0.15) 
        self.angle += rotation_speed
        
        # 2. DISTANCE (Pulse outward)
        target_dist = self.original_dist + (bass * 150)
        # Smoothly move towards target (Linear Interpolation)
        self.dist = self.dist * 0.9 + target_dist * 0.1
        
        # 3. CHAOS/COLLISION (Controlled by TREBLE)
        # If high-pitch sounds (snares/vocals) happen, shake the particle!
        jitter_x = 0
        jitter_y = 0
        if treble > 0.4: # Threshold for chaos
            jitter_x = random.uniform(-10, 10) * treble
            jitter_y = random.uniform(-10, 10) * treble
            self.color = RED # Turn red when chaotic
        else:
            # Revert to normal color slowly could be complex, 
            # let's just pick a random cool color if not chaotic
            if random.random() > 0.95: 
                self.color = random.choice([CYAN, PURPLE, WHITE])

        return jitter_x, jitter_y

    def draw(self, surface, center_x, center_y, jx, jy):
        # Calculate base position
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        
        # Add the chaos offset
        final_x = x + jx
        final_y = y + jy
        
        pygame.draw.circle(surface, self.color, (int(final_x), int(final_y)), int(self.size))

# Create 150 particles
particles = [Particle() for _ in range(150)]
prev_audio = np.zeros(BARS)

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

    # 1. Analyze Audio
    audio = get_audio_data()
    # Smooth it out
    prev_audio = prev_audio * 0.7 + audio * 0.3
    
    # Extract Features
    bass_energy = np.mean(prev_audio[:10])   # Low frequencies (0-10)
    treble_energy = np.mean(prev_audio[80:]) # High frequencies (80+)

    # 2. Draw Background (Dark void)
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(40) 
    fade.fill((0, 0, 0)) # Pure black for high contrast
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Update Particles
    for p in particles:
        jx, jy = p.update(bass_energy, treble_energy)
        p.draw(screen, center_x, center_y, jx, jy)

    # 4. Draw The "Shapeless Line" (Blob)
    # The blob also rotates with the bass now
    points = []
    rotation_offset = pygame.time.get_ticks() / 1000 * (0.5 + bass_energy)
    
    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + rotation_offset
        
        # Radius reacts to audio + random wobble for "shapeless" look
        r = RADIUS + (prev_audio[i] * 120)
        
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        # Draw the main line
        pygame.draw.lines(screen, CYAN, True, points, 2)
        
        # Draw a "Glow" line (slightly larger, thinner)
        glow_points = [(center_x + (x-center_x)*1.05, center_y + (y-center_y)*1.05) for x,y in points]
        pygame.draw.lines(screen, (50, 50, 100), True, glow_points, 1)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()