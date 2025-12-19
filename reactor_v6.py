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
RADIUS = 220                # Start even further out

# --- COLORS ---
# High Contrast Palette for visibility
NEON_CYAN = (0, 255, 255)
PURE_WHITE = (255, 255, 255)
ELECTRIC_BLUE = (50, 100, 255)
DEEP_VOID = (5, 5, 10)      # Almost black

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V6: HD Atom Collider")
clock = pygame.time.Clock()

# --- ATOM PARTICLE ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(RADIUS - 10, RADIUS + 10) 
        # TWEAK 1: Tiny Particles (1-2px) for sharp definition
        self.size = random.uniform(1, 2.5) 
        self.color = NEON_CYAN
        self.speed = random.uniform(0.02, 0.04)
        # Each particle has its own "nervousness"
        self.jitter_factor = random.uniform(0.5, 2.0)
        
    def update(self, bass_energy):
        # 1. DEAD ZONE (Silence = Freeze)
        if bass_energy < 0.05:
            return
            
        # 2. ROTATION
        # Spin faster when closer to center (Angular Momentum conservation effect)
        spin_boost = 1 + (200 / (self.dist + 1)) # Faster when dist is small
        self.angle += self.speed * spin_boost * 0.5
        
        # 3. IMPLOSION PHYSICS
        # Pull inward based on Bass
        if bass_energy > 0.3:
            pull_strength = bass_energy * 25
            self.dist -= pull_strength
            
            # Turn White when accelerating (Hot!)
            self.color = PURE_WHITE
        else:
            # Drift back out slowly
            self.dist += 3 
            self.color = NEON_CYAN

        # 4. ANTI-CLUMPING (The "Bounce")
        # Instead of distance < 0, we set a "Hard Core" at distance 10
        if self.dist < 10:
            self.dist = 10 
            # Violent Bounce!
            # It teleports slightly out to simulate a collision
            self.dist += random.uniform(5, 20) 
            self.color = ELECTRIC_BLUE # Spark color

        # 5. LIMITS
        if self.dist > RADIUS + 40:
            self.dist = RADIUS + 40

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

# Reduce particle count slightly for clarity (Quality > Quantity)
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

    # 1. Audio
    audio = get_audio_data()
    prev_audio = prev_audio * 0.7 + audio * 0.3 # Smooth
    bass_energy = np.mean(prev_audio[:10])

    # 2. Draw Background (Clean wipe for sharpness)
    # Instead of "trails", we fill with semi-transparent black to reduce blur
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) # High alpha = Faster fade = Sharper movement
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Draw The "Containment Ring" (The Shapeless Line)
    points = []
    
    # Rotation logic
    rot_speed = 0 if bass_energy < 0.05 else 0.005 + (bass_energy * 0.02)
    if 'global_rot' not in locals(): global_rot = 0
    global_rot += rot_speed
    
    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + global_rot
        
        # Audio deforms the ring
        deformation = 0 if bass_energy < 0.05 else prev_audio[i] * 60
        r = RADIUS + deformation
        
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        # Draw the ring
        pygame.draw.lines(screen, ELECTRIC_BLUE, True, points, 2)

    # 4. Update & Draw Atoms
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()