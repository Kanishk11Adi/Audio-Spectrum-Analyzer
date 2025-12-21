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
RADIUS = 200                

# --- COLORS ---
C_PURPLE = (100, 0, 150)
C_CYAN = (0, 255, 255)
C_RED = (255, 50, 0)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 255, 0)
DEEP_VOID = (5, 5, 10)

# --- SETUP ---
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("V13: The Shape Shifter")
clock = pygame.time.Clock()

# --- ATOM PARTICLE (Standard V9) ---
class Particle:
    def __init__(self):
        self.reset()
    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(RADIUS - 10, RADIUS + 10) 
        self.size = random.uniform(2, 4) 
        self.color = C_PURPLE
        self.speed = random.uniform(0.01, 0.03)
    def update(self, bass_energy):
        if bass_energy < 0.05: return
        spin_boost = 1 + (100 / (self.dist + 1)) 
        self.angle += self.speed * spin_boost
        if bass_energy > 0.3:
            pull_strength = bass_energy * 12 
            self.dist -= pull_strength
            if bass_energy > 0.8: self.color = C_WHITE
            elif bass_energy > 0.6: self.color = C_RED
            elif bass_energy > 0.4: self.color = C_YELLOW
            else: self.color = C_CYAN
        else:
            self.dist += 2 
            self.color = C_PURPLE
        inner_core_radius = 90
        if self.dist < inner_core_radius:
            self.dist = inner_core_radius
            self.dist += random.uniform(10, 50) 
            self.angle += random.uniform(-0.1, 0.1)
        if self.dist > RADIUS + 40: self.dist = RADIUS + 40
    def draw(self, surface, center_x, center_y):
        x = center_x + math.cos(self.angle) * self.dist
        y = center_y + math.sin(self.angle) * self.dist
        pygame.draw.circle(surface, self.color, (int(x), int(y)), int(self.size))

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
global_rot = 0 
current_lobes = 0 # Start as a circle

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Audio
    audio = get_audio_data()
    prev_audio = prev_audio * 0.7 + audio * 0.3 
    bass_energy = np.mean(prev_audio[:10])

    # 2. Background
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) 
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. LOGIC: DETERMINE TARGET SHAPE
    # Based on how loud the bass is, pick a geometry
    if bass_energy > 0.75:
        target_lobes = 5 # Star/Pentagon (High Energy)
    elif bass_energy > 0.5:
        target_lobes = 4 # Square (Medium Energy)
    elif bass_energy > 0.2:
        target_lobes = 3 # Triangle (Low Energy)
    else:
        target_lobes = 0 # Circle (Silence)

    # Smoothly morph into the new shape
    # We move 5% of the way to the target shape every frame
    current_lobes = current_lobes * 0.9 + target_lobes * 0.1

    # 4. DRAW THE MORPHING POLYGON
    points = []
    
    # Rotation Speed
    rot_speed = 0.005 + (bass_energy * 0.05)
    global_rot += rot_speed
    
    # Color Logic
    if bass_energy > 0.6: line_color = C_RED
    elif bass_energy > 0.4: line_color = C_CYAN
    else: line_color = (80, 80, 200)

    for i in range(BARS):
        # Angle around the circle
        angle = (2 * math.pi * i) / BARS
        
        # 1. Audio Distortion (Jagged edges)
        audio_spike = prev_audio[i] * 50
        
        # 2. Geometric Shape Math
        # We add 'global_rot' inside the sin() function to rotate the SHAPE itself
        # 'current_lobes' determines if it's a triangle, square, etc.
        shape_morph = math.sin((angle + global_rot) * current_lobes) * (bass_energy * 60)
        
        # Combine
        r = RADIUS + audio_spike + shape_morph
        
        # Convert to X,Y
        x = center_x + math.cos(angle + global_rot) * r
        y = center_y + math.sin(angle + global_rot) * r
        points.append((x, y))

    if len(points) > 2:
        # Main Line
        pygame.draw.lines(screen, line_color, True, points, 4)
        
        # Ghost Line (Visual Echo)
        ghost_points = []
        for x, y in points:
            gx = center_x + (x - center_x) * 1.05
            gy = center_y + (y - center_y) * 1.05
            ghost_points.append((gx, gy))
        
        pygame.draw.lines(screen, (line_color[0]//2, line_color[1]//2, line_color[2]//2), True, ghost_points, 2)

    # 5. Update Particles
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()