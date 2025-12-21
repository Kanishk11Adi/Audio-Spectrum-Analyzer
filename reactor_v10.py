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
C_DEEP_PURPLE = (50, 0, 100)
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
pygame.display.set_caption("V11: The Glitch Reactor")
clock = pygame.time.Clock()

# --- ATOM PARTICLE (Kept exactly as V9 - Perfection) ---
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
            self.color = C_DEEP_PURPLE

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
global_rot = 0 # Persistent rotation

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Audio
    audio = get_audio_data()
    # Less smoothing = More jagged spikes
    prev_audio = prev_audio * 0.6 + audio * 0.4 
    bass_energy = np.mean(prev_audio[:10])
    treble_energy = np.mean(prev_audio[100:])

    # 2. Draw Background
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.set_alpha(80) 
    fade.fill(DEEP_VOID)
    screen.blit(fade, (0,0))
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # 3. DRAW THE CHAOS LINE
    points = []
    
    # Dynamic Rotation: Spin normally, but JERK backward on Treble hits
    rot_speed = 0.005 + (bass_energy * 0.02)
    if treble_energy > 0.5: # Snare hit / High hat
        rot_speed = -0.05   # Sudden reverse twitch
        
    global_rot += rot_speed
    
    # Pick Color
    if bass_energy > 0.6: line_color = C_RED
    elif bass_energy > 0.4: line_color = C_CYAN
    else: line_color = (50, 50, 150)

    for i in range(BARS):
        # Base Angle
        angle = (2 * math.pi * i) / BARS + global_rot
        
        # CHAOS MATH:
        # Instead of just changing Radius (r), we also warp the Angle
        # This makes the line twist sideways
        
        # 1. Radius Distortion (Spikes)
        r_distortion = prev_audio[i] * 100
        
        # 2. Angle Distortion (The "Disfigured" Look)
        # If the volume at this frequency is high, twist the angle slightly
        angle_distortion = 0
        if prev_audio[i] > 0.5:
            angle_distortion = math.sin(i) * 0.2 # Arbitrary twist based on index
            
        final_angle = angle + angle_distortion
        final_r = RADIUS + r_distortion
        
        x = center_x + math.cos(final_angle) * final_r
        y = center_y + math.sin(final_angle) * final_r
        points.append((x, y))

    # Draw the Disfigured Line
    if len(points) > 2:
        # We draw it Open (False) instead of Closed so the ends can disconnect glitchily
        # or Closed (True) for a continuous loop. Let's try Closed first.
        pygame.draw.lines(screen, line_color, True, points, 3)
        
        # Glitch Echo (Draw a second faint line slightly offset)
        offset_points = [(x+5, y+5) for x,y in points]
        pygame.draw.lines(screen, (line_color[0]//2, line_color[1]//2, line_color[2]//2), True, offset_points, 1)

    # 4. Update Particles (V9 Standard)
    for p in particles:
        p.update(bass_energy)
        p.draw(screen, center_x, center_y)

    pygame.display.flip()
    clock.tick(FPS)

stream.stop_stream()
stream.close()
pygame.quit()