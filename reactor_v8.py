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
RADIUS = 220                # Outer ring size

# --- COLORS ---
# V6 Palette (High Contrast)
NEON_CYAN = (0, 255, 255)
PURE_WHITE = (255, 255, 255)
ELECTRIC_BLUE = (50, 100, 255)
DEEP_VOID = (5, 5, 10)

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V8: Controlled Fusion (Smoother)")
clock = pygame.time.Clock()

# --- ATOM PARTICLE ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(RADIUS - 10, RADIUS + 10) 
        # BACK TO V6 SIZE (Small and sharp)
        self.size = random.uniform(1.5, 3.5) 
        self.color = NEON_CYAN
        self.speed = random.uniform(0.01, 0.03) # Slightly slower natural rotation
        
    def update(self, bass_energy):
        if bass_energy < 0.05:
            return
            
        # 1. ORBIT
        # Reduced spin boost so they don't get too dizzy
        spin_boost = 1 + (100 / (self.dist + 1)) 
        self.angle += self.speed * spin_boost
        
        # 2. IMPLOSION (DAMPENED SENSITIVITY)
        if bass_energy > 0.3:
            # TWEAK: Reduced multiplier from 25 to 12
            # This makes the pull "heavier" and less twitchy
            pull_strength = bass_energy * 12 
            self.dist -= pull_strength
            
            # Turn White only on hard hits
            if bass_energy > 0.6:
                self.color = PURE_WHITE
        else:
            # Drift back out smoothly
            self.dist += 2 
            self.color = NEON_CYAN

        # 3. THE COLLISION CORE (BIGGER NOW)
        # TWEAK: Collision happens at Distance 50 (was 10)
        # This creates the "Bigger Orb Circle" in the middle
        inner_core_radius = 50
        
        if self.dist < inner_core_radius:
            self.dist = inner_core_radius
            
            # Bounce back slightly
            self.dist += random.uniform(2, 10) 
            self.color = ELECTRIC_BLUE 

        # 4. LIMITS
        if self.dist > RADIUS + 40:
            self.dist = RADIUS + 40

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

particles = [Particle() for _ in range(180)] # Increased count slightly since they are small again
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
    # TWEAK: Increased smoothing from 0.7 to 0.85
    # This ignores sudden "twitches" in the music
    prev_audio = prev_audio * 0.85 + audio * 0.15
    bass_energy = np.mean(prev_audio[:10])

    # 2. Draw Background
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) 
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Draw Outer Ring
    points = []
    rot_speed = 0 if bass_energy < 0.05 else 0.005 + (bass_energy * 0.01)
    if 'global_rot' not in locals(): global_rot = 0
    global_rot += rot_speed
    
    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + global_rot
        deformation = 0 if bass_energy < 0.05 else prev_audio[i] * 50 # Reduced deformation
        r = RADIUS + deformation
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        pygame.draw.lines(screen, ELECTRIC_BLUE, True, points, 2)

    # 4. Update Particles
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    # OPTIONAL: Visual Guide for the Core (Comment out if you prefer invisible wall)
    # pygame.draw.circle(screen, (20, 20, 30), (center_x, center_y), 50, 1) 

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()