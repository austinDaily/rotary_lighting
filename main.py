import time
import board
import digitalio
import neopixel

# === NeoPixel Setup ===
# Three rings: 8, 16, 24 pixels
RING_PINS = [board.D5, board.D6, board.D7] # pick 3 GPIO pins on Scorpio 
RING_SIZES = [8, 16, 24]

rings = []
for pin, num in zip(RING_PINS, RING_SIZES):
    rings.append(neopixel.NeoPixel(pin, num, brightness=0.5, auto_write=False))

# === Rotary Switch Selector Setup (digital method) ===
# Connect each of the 8 switch positions to GPIO pins
SELECTOR_PINS = [board.D2, board.D3, board.D4, board.D8, board.D9, board.D10, board.D11, board.D12]

selectors = []
for pin in SELECTOR_PINS:
    d = digitalio.DigitalInOut(pin)
    d.direction = digitalio.Direction.INPUT
    d.pull = digitalio.Pull.UP # assuming grounded when active
    selectors.append(d)

# === State ===
current_pattern = 0
previous_position = None

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)
    
# === Pattern Functions ===
def all_off():
    for ring in rings:
        ring.fill((0, 0, 0))
        ring.show()

def solid_color(color):
    for ring in rings:
        ring.fill(color)
        ring.show()

def chase(color, delay=0.05):
    for ring in rings:
        ring.fill((0, 0, 0))
    for i in range(max(RING_SIZES)):
        for ring in rings:
            ring[i % len(ring)] = color
            ring.show()
        time.sleep(delay)
        for ring in rings:
            ring[i % len(ring)] = (0, 0, 0)

def rainbow_cycle(wait=0.02):
    for j in range(255):
        for ring in rings:
            for i in range(len(ring)):
                idx = (i * 256 // len(ring)) + j
                ring[i] = wheel(idx & 255)
            ring.show()
        time.sleep(wait)

def theater_chase(color, wait=0.1):
    for q in range(3):
        for i in range(0, max(RING_SIZES), 3):
            for ring in rings:
                if i < len(ring):
                    ring[i] = color
            for ring in rings:
                ring.show()
            time.sleep(wait)
            for ring in rings:
                if i < len(ring):
                    ring[i] = (0, 0, 0)

def pulse(color, steps=50, delay=0.02):
    r, g, b = color
    for level in list(range(steps)) + list(range(steps, -1, -1)):
        scaled = (int(r*level/steps), int(g*level/steps), int(b*level/steps))
        for ring in rings:
            ring.fill(scaled)
            ring.show()
        time.sleep(delay)

def sparkle(color, count=10, delay=0.1):
    import random
    for _ in range(count):
        for ring in rings:
            idx = random.randint(0, len(ring)-1)
            ring[idx] = color
        for ring in rings:
            ring.show()
        time.sleep(delay)
        for ring in rings:
            ring.fill((0,0,0))

def rainbow_pulse(wait=0.02):
    for j in range(255):
        color = wheel(j)
        for ring in rings:
            ring.fill(color)
            ring.show()
        time.sleep(wait)

# List of patterns
patterns = [
    lambda: all_off(),                # 0
    lambda: solid_color((255, 0, 0)), # 1 - red
    lambda: solid_color((0, 255, 0)), # 2 - green
    lambda: solid_color((0, 0, 255)), # 3 - blue
    lambda: chase((255, 255, 0)),     # 4 - chase yellow
    lambda: rainbow_cycle(),          # 5 - rainbow cycle
    lambda: pulse((0, 255, 255)),     # 6 - cyan pulse
    lambda: sparkle((255, 0, 255))    # 7 - magenta sparkle
]

# === Main Loop ===
while True:
    # Read rotary switch position
    pos = None
    for idx, d in enumerate(selectors):
        if not d.value:  # active low
            pos = idx
            break
    if pos is None:
        pos = 0  # default to position 0 if none active

    # If switch position changed, update pattern
    if pos != previous_position:
        previous_position = pos
        current_pattern = pos % len(patterns)
        print(f"Switch to pattern {current_pattern}")
        
        patterns[current_pattern]()  # Execute selected pattern