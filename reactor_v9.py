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

# --- COLOR PALETTE (The Heat Map) ---
# We will mix these dynamically based on volume
C_DEEP_PURPLE = (50, 0, 100)
C_BLUE = (0, 0, 255)
C_CYAN = (0, 255, 255)
C_GREEN = (0, 255, 100)
C_YELLOW = (255, 255, 0)
C_RED = (255, 50, 0)
C_WHITE = (255, 255, 255)
DEEP_VOID = (5, 5, 10)

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V9: Final Spectrum Reactor")
clock = pygame.time.Clock()

# --- ATOM PARTICLE ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(RADIUS - 10, RADIUS + 10) 
        self.size = random.uniform(2, 4) 
        self.color = C_DEEP_PURPLE
        self.speed = random.uniform(0.01, 0.03)
        
    def update(self, bass_energy):
        if bass_energy < 0.05:
            return
            
        # 1. ORBIT
        spin_boost = 1 + (100 / (self.dist + 1)) 
        self.angle += self.speed * spin_boost
        
        # 2. IMPLOSION
        if bass_energy > 0.3:
            pull_strength = bass_energy * 12 
            self.dist -= pull_strength
            
            # --- DYNAMIC COLOR LOGIC ---
            # Map energy to color (Heat Up)
            if bass_energy > 0.8:     # Super Loud
                self.color = C_WHITE
            elif bass_energy > 0.6:   # Loud
                self.color = C_RED
            elif bass_energy > 0.4:   # Medium
                self.color = C_YELLOW
            else:
                self.color = C_CYAN
        else:
            # Drift back out
            self.dist += 2 
            self.color = C_DEEP_PURPLE # Cool down

        # 3. THE THICK COLLISION CORE (TWEAKED!)
        # Increased radius to 90 (Bigger Hole)
        inner_core_radius = 90
        
        if self.dist < inner_core_radius:
            self.dist = inner_core_radius
            
            # TWEAK: Thicker bounce! 
            # Bounces out 10-50 pixels to create a thick "Band" of matter
            self.dist += random.uniform(10, 50) 
            
            # Add randomness to angle for "Chaos" effect
            self.angle += random.uniform(-0.1, 0.1)

        # 4. LIMITS
        if self.dist > RADIUS + 40:
            self.dist = RADIUS + 40

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

# Increased particle count slightly to fill the thick layer
particles = [Particle() for _ in range(220)] 
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
    prev_audio = prev_audio * 0.85 + audio * 0.15
    bass_energy = np.mean(prev_audio[:10])

    # 2. Draw Background
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) 
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Draw Outer Ring (Dynamic Color too!)
    points = []
    rot_speed = 0 if bass_energy < 0.05 else 0.005 + (bass_energy * 0.01)
    if 'global_rot' not in locals(): global_rot = 0
    global_rot += rot_speed
    
    # Ring Color Logic
    if bass_energy > 0.6: ring_color = C_RED
    elif bass_energy > 0.4: ring_color = C_CYAN
    else: ring_color = (50, 50, 100) # Dark Blue

    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + global_rot
        deformation = 0 if bass_energy < 0.05 else prev_audio[i] * 60
        r = RADIUS + deformation
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        pygame.draw.lines(screen, ring_color, True, points, 3)

    # 4. Update Particles
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()