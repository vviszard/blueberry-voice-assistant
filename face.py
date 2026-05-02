import time
import threading
import random
import textwrap
import traceback
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

class RobotFace(threading.Thread):
    def __init__(self):
        super().__init__()
        try:
            self.serial = i2c(port=1, address=0x3C)
            self.device = ssd1306(self.serial, rotate=2)
            self.width = self.device.width
            self.height = self.device.height
            print("[DISPLAY] OLED Connected.")
        except Exception as e:
            print(f"[DISPLAY] Error: {e}")
            self.device = None

        self.daemon = True
        self.state = "IDLE"
        self.running = True
        self.text_buffer = ""
        
        # Eye Properties
        self.eye_width = 40
        self.eye_height = 50
        self.eye_gap = 10
        
        # Physics State
        self.blink_state = 0.0
        self.pupil_x = 0.0
        self.pupil_y = 0.0
        self.target_pupil_x = 0.0
        self.target_pupil_y = 0.0
        self.next_blink = time.time() + 1

    def update_physics(self):
        # Smooth movement
        self.pupil_x += (self.target_pupil_x - self.pupil_x) * 0.2
        self.pupil_y += (self.target_pupil_y - self.pupil_y) * 0.2

        if self.state == "IDLE":
            # Blink logic
            if time.time() > self.next_blink:
                self.blink_state = 1.0
                if time.time() > self.next_blink + 0.15:
                    self.blink_state = 0.0
                    self.next_blink = time.time() + random.uniform(1, 4)
            # Look around logic
            if random.random() < 0.1:
                self.target_pupil_x = random.uniform(-0.7, 0.7)
                self.target_pupil_y = random.uniform(-0.3, 0.3)
        
        elif self.state == "LISTENING":
            self.blink_state = 0.0
            self.target_pupil_x = 0
            self.target_pupil_y = 0

    def run(self):
        if not self.device: return
        
        while self.running:
            try:
                self.update_physics()
                
                with canvas(self.device) as draw:
                    
                    # --- MODE 1: EYES (Idle / Listening) ---
                    if self.state in ["IDLE", "LISTENING"]:
                        cx = self.width / 2
                        cy = self.height / 2
                        
                        lx = cx - self.eye_width - (self.eye_gap / 2)
                        ly = cy - (self.eye_height / 2)
                        rx = cx + (self.eye_gap / 2)
                        ry = cy - (self.eye_height / 2)

                        # Blink Math
                        current_h = max(1, self.eye_height * (1.0 - self.blink_state))
                        offset_y = (self.eye_height - current_h) / 2
                        
                        # Draw Whites
                        draw.rectangle((lx, ly + offset_y, lx + self.eye_width, ly + offset_y + current_h), fill="white")
                        draw.rectangle((rx, ry + offset_y, rx + self.eye_width, ry + offset_y + current_h), fill="white")

                        # Draw Pupils
                        if self.blink_state < 0.8:
                            pupil_size = 14
                            px = self.pupil_x * 12
                            py = self.pupil_y * 8
                            
                            draw.rectangle((lx + 13 + px, ly + 18 + offset_y + py, 
                                            lx + 13 + px + pupil_size, ly + 18 + offset_y + py + pupil_size), fill="black")
                            draw.rectangle((rx + 13 + px, ry + 18 + offset_y + py, 
                                            rx + 13 + px + pupil_size, ry + 18 + offset_y + py + pupil_size), fill="black")

                    # --- MODE 2: CENTERED TEXT ---
                    else:
                        # 1. Wrap the text
                        # "18" is roughly the max chars that fit on one line for default font
                        lines = textwrap.wrap(self.text_buffer, width=18)
                        
                        # 2. Calculate Vertical Center
                        line_height = 10  # Pixels per line
                        total_text_height = len(lines) * line_height
                        
                        # Start Y = (Screen Height - Text Height) / 2
                        current_y = (self.height - total_text_height) / 2
                        
                        # 3. Draw each line Centered Horizontally
                        for line in lines:
                            # Measure text width (approximate 6 pixels per char for default font)
                            text_width = draw.textlength(line) if hasattr(draw, "textlength") else len(line) * 6
                            
                            # Start X = (Screen Width - Text Width) / 2
                            centered_x = (self.width - text_width) / 2
                            
                            draw.text((centered_x, current_y), line, fill="white")
                            current_y += line_height

                time.sleep(0.03)
                
            except Exception as e:
                print(f"[FACE ERROR] {e}")
                time.sleep(1)

    def set_state(self, new_state):
        self.state = new_state
    
    def set_text(self, text):
        self.text_buffer = text

    def stop(self):
        self.running = False