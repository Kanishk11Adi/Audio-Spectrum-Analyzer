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
RADIUS = 220                

# --- COLORS ---
NEON_CYAN = (0, 200, 255)
DEEP_BLUE = (0, 50, 150)
PURE_WHITE = (255, 255, 255)
HOT_YELLOW = (255, 255, 0) # Flash color for collision
DEEP_VOID = (10, 10, 15)

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V7: Macro Atom Smasher")
clock = pygame.time.Clock()

# --- ORB PARTICLE ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(RADIUS - 10, RADIUS + 10) 
        # TWEAK 1: MUCH BIGGER (4px to 9px)
        self.size = random.uniform(4, 9) 
        self.color = NEON_CYAN
        self.speed = random.uniform(0.01, 0.03)
        self.hit_center = False # Flag to track if we just crashed
        
    def update(self, bass_energy):
        if bass_energy < 0.05:
            return
            
        # 1. ORBIT
        # Spin faster when closer
        spin_boost = 1 + (150 / (self.dist + 1)) 
        self.angle += self.speed * spin_boost
        
        # 2. IMPLOSION
        if bass_energy > 0.3:
            pull_strength = bass_energy * 20
            self.dist -= pull_strength
        else:
            # Drift back out
            self.dist += 2.5
            self.hit_center = False # Reset crash flag
            self.color = NEON_CYAN  # Cool down color

        # 3. THE SMASH (Collision)
        # We increase the 'bounce zone' to 20 since particles are bigger
        if self.dist < 20:
            self.dist = 20
            # Violent Bounce with randomness
            self.dist += random.uniform(10, 30) 
            
            # FLASH COLOR!
            self.color = HOT_YELLOW
            self.hit_center = True

        # 4. LIMITS
        if self.dist > RADIUS + 40:
            self.dist = RADIUS + 40

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        
        # DRAW GLOW (The big colored circle)
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))
        
        # DRAW CORE (The white shiny center)
        # This makes it look like a sphere, not a flat dot
        core_size = max(1, int(self.size * 0.4))
        pygame.draw.circle(surface, PURE_WHITE, (int(x), int(y)), core_size)

# Reduce count to 100 so big orbs don't clutter
particles = [Particle() for _ in range(100)]
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
    prev_audio = prev_audio * 0.7 + audio * 0.3
    bass_energy = np.mean(prev_audio[:10])

    # 2. Draw Background
    # Less fade = sharper movement for the big orbs
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(90) 
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Draw The Ring (Thicker line now)
    points = []
    rot_speed = 0 if bass_energy < 0.05 else 0.005 + (bass_energy * 0.02)
    if 'global_rot' not in locals(): global_rot = 0
    global_rot += rot_speed
    
    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + global_rot
        deformation = 0 if bass_energy < 0.05 else prev_audio[i] * 60
        r = RADIUS + deformation
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        pygame.draw.lines(screen, DEEP_BLUE, True, points, 5) # Thicker darker backing
        pygame.draw.lines(screen, NEON_CYAN, True, points, 2) # Thin bright top

    # 4. Update Orbs
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()