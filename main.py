import random
import time
from machine import Pin, SPI, PWM
import framebuf
import math

# LCD Pin Configuration
BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240
        
        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1, 10000000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        self.red = 0x07E0
        self.green = 0x001f
        self.blue = 0xf800
        self.white = 0xffff
        
    @staticmethod
    def rgb565(r, g, b):
        """Convert RGB888 to RGB565 color format."""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    # Enhanced color generation for gradients and richer colors
    def get_gradient_color(self, position):
        """Generate a gradient color based on position."""
        r = int((1 + math.sin(position * 0.1)) * 127)
        g = int((1 + math.sin(position * 0.1 + 2)) * 127)
        b = int((1 + math.sin(position * 0.1 + 4)) * 127)
        return LCD_1inch3.rgb565(r, g, b)
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

# Initialize the LCD and Buttons
pwm = PWM(Pin(BL))
pwm.freq(1000)
pwm.duty_u16(32768)  # max 65535
LCD = LCD_1inch3()

keyA = Pin(15, Pin.IN, Pin.PULL_UP)
keyB = Pin(17, Pin.IN, Pin.PULL_UP)
keyX = Pin(19, Pin.IN, Pin.PULL_UP)
keyY = Pin(21, Pin.IN, Pin.PULL_UP)
up = Pin(2, Pin.IN, Pin.PULL_UP)
down = Pin(18, Pin.IN, Pin.PULL_UP)
left = Pin(16, Pin.IN, Pin.PULL_UP)
right = Pin(20, Pin.IN, Pin.PULL_UP)

# Game of Life settings
grid_width = 24
grid_height = 24
cell_size = 10
color_mode = 0
paused = False


def init_grid():
    # Each cell has [state, age]
    return [[[random.randint(0, 1), 0] for _ in range(grid_width)] for _ in range(grid_height)]

def rgb565(r, g, b):
    """Convert RGB888 to RGB565 color format."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def get_color(lcd_instance, cell, mode, x, y, grid_width, grid_height):
    # Check if the cell is dead or alive
    if cell[0] == 0:  # Cell is dead
        return lcd_instance.rgb565(255, 255, 255)  # White color for dead cells

    # Variables for cell age and position-based gradient
    age = cell[1]
    position = (x / grid_width + y / grid_height) / 2  # Calculate position for gradient

    # Color modes
    if mode == 0:
        # Gradient effect based on position
        return lcd_instance.get_gradient_color(position)
    elif mode == 1:
        # Rainbow colors based on age
        r = int((1 + math.sin(age * 0.1)) * 127)
        g = int((1 + math.sin(age * 0.1 + 2)) * 127)
        b = int((1 + math.sin(age * 0.1 + 4)) * 127)
        return lcd_instance.rgb565(r, g, b)
    else:
        # Random color for each cell, seeded with age and position
        random.seed(age + int(position * 100))
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return lcd_instance.rgb565(r, g, b)

def draw_grid(grid, color_mode, lcd_instance):
    for y in range(grid_height):
        for x in range(grid_width):
            color = get_color(lcd_instance, grid[y][x], color_mode, x, y, grid_width, grid_height)
            lcd_instance.fill_rect(x * cell_size, y * cell_size, cell_size, cell_size, color)

def count_neighbors(grid, x, y):
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            nx, ny = (x + i) % grid_width, (y + j) % grid_height
            count += grid[ny][nx][0]
    return count

def update_grid(grid):
    new_grid = [[[0, 0] for _ in range(grid_width)] for _ in range(grid_height)]
    for y in range(grid_height):
        for x in range(grid_width):
            neighbors = count_neighbors(grid, x, y)
            if grid[y][x][0] == 1:
                # Cell is alive
                if neighbors in [2, 3]:
                    # Cell stays alive and ages
                    new_grid[y][x] = [1, grid[y][x][1] + 1]
                else:
                    # Cell dies
                    new_grid[y][x] = [0, 0]
            else:
                # Cell is dead
                if neighbors == 3:
                    # Cell becomes alive
                    new_grid[y][x] = [1, 0]
                else:
                    # Cell stays dead
                    new_grid[y][x] = [0, 0]
    return new_grid

def shift_grid(grid, dx, dy):
    new_grid = [[[0, 0] for _ in range(grid_width)] for _ in range(grid_height)]
    for y in range(grid_height):
        for x in range(grid_width):
            nx, ny = (x + dx) % grid_width, (y + dy) % grid_height
            new_grid[ny][nx] = grid[y][x]
    return new_grid

# Main loop
grid = init_grid()
while True:
    if not paused:
        grid = update_grid(grid)
    
    # Button A - Add a new random cell
    if not keyA.value():
        x, y = random.randint(0, grid_width - 1), random.randint(0, grid_height - 1)
        grid[y][x] = [1, 0]
        time.sleep(0.1)  # Debouncing

    # Button B - Change color scheme
    if not keyB.value():
        color_mode = (color_mode + 1) % 3
        time.sleep(0.1)  # Debouncing

    # Button X - Pause/Resume
    if not keyX.value():
        paused = not paused
        time.sleep(0.1)  # Debouncing

    # Button Y - Reset grid
    if not keyY.value():
        grid = init_grid()
        time.sleep(0.1)  # Debouncing

    # Directional Buttons - Shift the entire grid
    if not up.value():
        grid = shift_grid(grid, 0, -1)
        time.sleep(0.1)  # Debouncing
    if not down.value():
        grid = shift_grid(grid, 0, 1)
        time.sleep(0.1)  # Debouncing
    if not left.value():
        grid = shift_grid(grid, -1, 0)
        time.sleep(0.1)  # Debouncing
    if not right.value():
        grid = shift_grid(grid, 1, 0)
        time.sleep(0.1)  # Debouncing

    # Inside your main loop or wherever you call draw_grid
    draw_grid(grid, color_mode, LCD)

    LCD.show()
    time.sleep(0.1)
