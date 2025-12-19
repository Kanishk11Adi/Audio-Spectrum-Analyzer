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
RADIUS = 200                # Start FURTHER out so they can fall in

# --- COLORS ---
CYAN = (0, 255, 255)
NEON_GREEN = (50, 255, 50) # Radioactive look
WHITE = (255, 255, 255)
CORE_RED = (255, 50, 50)   # Color of the collision core

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V5: Atom Smasher (Implosion)")
clock = pygame.time.Clock()

# --- ATOM PARTICLE ---
class Particle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        # They start at the edge of the circle (The "Containment Ring")
        self.dist = random.uniform(RADIUS - 20, RADIUS + 20) 
        self.size = random.uniform(2, 4)
        self.color = NEON_GREEN
        self.speed = random.uniform(0.02, 0.05)
        
    def update(self, bass_energy):
        # 1. DEAD ZONE (Silence = Freeze)
        if bass_energy < 0.05:
            # If silent, do NOTHING. Just return.
            return
            
        # 2. ROTATION (Orbit)
        self.angle += self.speed
        
        # 3. IMPLOSION PHYSICS (The "Gravity" of the beat)
        # If bass is high, pull HARD to the center (0)
        # If bass is low, drift back to the ring (RADIUS)
        
        if bass_energy > 0.3: # If beat hits
            # Pull inward!
            pull_strength = bass_energy * 20
            self.dist -= pull_strength
            
            # Change color to heat up
            self.color = CORE_RED
        else:
            # Drift back to outer ring (Magnetic containment)
            self.dist += 2 # Slowly expand out
            self.color = NEON_GREEN # Cool down

        # 4. COLLISION (The Center)
        # If they hit the center (distance near 0), they "collide"
        if self.dist < 15:
            self.dist = 15 # Don't cross the center point
            # Violent Jitter (Atom Smash)
            self.angle += random.uniform(-0.5, 0.5) 
            self.color = WHITE # Flash white on impact
            
        # 5. LIMITS
        # Don't fly off screen
        if self.dist > RADIUS + 50:
            self.dist = RADIUS + 50

    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

# Create 200 Atoms
particles = [Particle() for _ in range(200)]
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
    bass_energy = np.mean(prev_audio[:15])

    # 2. Draw Background (Black Void)
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(60) # Higher alpha = less trails (cleaner look)
    fade.fill((0, 0, 0))
    screen.blit(fade, (0,0))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. Update Atoms
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    # 4. Draw The Containment Field (The outer line)
    # This line stays roughly circular but pulses
    points = []
    
    # Scale Rotation based on silence vs music
    # If silent (bass < 0.05), rotation stops.
    rot_speed = 0 if bass_energy < 0.05 else 0.01 + (bass_energy * 0.05)
    
    # We need a persistent rotation variable
    if 'global_rot' not in locals(): global_rot = 0
    global_rot += rot_speed
    
    for i in range(BARS):
        angle = (2 * math.pi * i) / BARS + global_rot
        
        # Audio deforms the ring
        # If silent, it's a perfect circle
        deformation = 0 if bass_energy < 0.05 else prev_audio[i] * 50
        
        r = RADIUS + deformation
        
        x = center_x + math.cos(angle) * r
        y = center_y + math.sin(angle) * r
        points.append((x, y))

    if len(points) > 2:
        pygame.draw.lines(screen, CYAN, True, points, 2)
        
        # Optional: Core Glow when crashing
        if bass_energy > 0.4:
            pygame.draw.circle(screen, (30, 0, 0), (center_x, center_y), 30) # Red core glow

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()