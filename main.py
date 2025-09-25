import board
import digitalio
import neopixel
import time
import random

# === NeoPixel setup ===
# Total pixels = sum of all rings
RING_SIZES = [8, 16, 24]
NUM_PIXELS = sum(RING_SIZES)
PIXEL_PIN = board.D5  # your data pin

pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.5, auto_write=False)

# === 8-way Rotary Selector ===
SELECTOR_PINS = [
    board.D2, board.D3, board.D4, board.D8,
    board.D9, board.D10, board.D11, board.D12
]

selectors = []
for pin in SELECTOR_PINS:
    d = digitalio.DigitalInOut(pin)
    d.direction = digitalio.Direction.INPUT
    d.pull = digitalio.Pull.UP  # active LOW
    selectors.append(d)

# === State ===
current_pattern = 0
previous_position = None

# === Helper ===
def wheel(pos):
    if pos < 85:
        return (pos*3, 255-pos*3, 0)
    elif pos < 170:
        pos -= 85
        return (255-pos*3, 0, pos*3)
    else:
        pos -= 170
        return (0, pos*3, 255-pos*3)

# === Non-blocking pattern generator functions ===

def pattern_off(state):
    pixels.fill((0,0,0))
    pixels.show()

def pattern_solid(state, color=(255,0,0)):
    pixels.fill(color)
    pixels.show()

def pattern_rainbow_cycle(state):
    # state['index'] stores animation position
    for i in range(NUM_PIXELS):
        idx = (i * 256 // NUM_PIXELS) + state['index']
        pixels[i] = wheel(idx & 255)
    pixels.show()
    state['index'] = (state['index'] + 1) % 256

def pattern_chase(state, color=(255,255,0)):
    for i in range(NUM_PIXELS):
        pixels[i] = (0,0,0)
    pixels[state['index'] % NUM_PIXELS] = color
    pixels.show()
    state['index'] = (state['index'] + 1) % NUM_PIXELS

def pattern_pulse(state, color=(0,255,255)):
    # smoothly scale brightness
    level = state.get('level', 0)
    step = state.get('step', 1)
    r,g,b = color
    scaled = (int(r*level/100), int(g*level/100), int(b*level/100))
    pixels.fill(scaled)
    pixels.show()
    level += step
    if level >= 100 or level <= 0:
        step *= -1
    state['level'] = level
    state['step'] = step

def pattern_sparkle(state, color=(255,0,255)):
    # turn off previous sparkle
    for idx in state.get('prev', []):
        pixels[idx] = (0,0,0)
    # pick new random pixels
    new_idx = [random.randint(0, NUM_PIXELS-1) for _ in range(3)]
    for idx in new_idx:
        pixels[idx] = color
    pixels.show()
    state['prev'] = new_idx

# === Map patterns to rotary switch positions ===
patterns = [
    ('Off', pattern_off, {}),                     # 0
    ('Red', pattern_solid, {'color':(255,0,0)}), # 1
    ('Green', pattern_solid, {'color':(0,255,0)}), # 2
    ('Blue', pattern_solid, {'color':(0,0,255)}),  # 3
    ('Chase', pattern_chase, {'color':(255,255,0), 'index':0}), # 4
    ('Rainbow', pattern_rainbow_cycle, {'index':0}),             # 5
    ('Pulse', pattern_pulse, {'level':0, 'step':1, 'color':(0,255,255)}), #6
    ('Sparkle', pattern_sparkle, {'prev':[],'color':(255,0,255)})          #7
]

# === Main Loop ===
while True:
    # read rotary switch position
    pos = None
    for idx, d in enumerate(selectors):
        if not d.value:  # active LOW
            pos = idx
            break
    if pos is None:
        pos = 0

    if pos != previous_position:
        previous_position = pos
        current_pattern = pos
        print("Switched to pattern", current_pattern, patterns[current_pattern][0])

    # call the pattern function
    func = patterns[current_pattern][1]
    state = patterns[current_pattern][2]
    func(state)

    # small delay to allow fast switch reading
    time.sleep(0.02)

