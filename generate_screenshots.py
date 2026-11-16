#!/usr/bin/env python3
"""
Helper script to generate PNG screenshots of the Part D simulation output
since a live RabbitMQ broker is not available in the local container.
"""

import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

# Paths
SCREENSHOTS_DIR = "/home/glitch/Projects/Assignment/screenshots"
SIMULATION_OUTPUT_FILE = "/tmp/simulation_output.txt"
D2_SCREENSHOT = os.path.join(SCREENSHOTS_DIR, "D2-simulation.png")
D3_SCREENSHOT = os.path.join(SCREENSHOTS_DIR, "D3-ack-nack.png")

# Ensure screenshots directory exists
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Run the simulation and capture output
print("[*] Running stream/simulation.py and capturing output...")
result = subprocess.run(
    [sys.executable, "stream/simulation.py"],
    capture_output=True,
    text=True,
    cwd="/home/glitch/Projects/Assignment/freshcart-pipelines"
)
output = result.stdout
with open(SIMULATION_OUTPUT_FILE, "w") as f:
    f.write(output)

# Try to load a monospace font, fallback to default
try:
    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", 14)
    font_bold = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf", 16)
except Exception:
    font = ImageFont.load_default()
    font_bold = ImageFont.load_default()

def create_screenshot(text, output_path, title):
    """Creates a clean, styled PNG screenshot from text."""
    lines = text.splitlines()
    # Calculate image dimensions
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1] + 4
    max_width = max(font.getbbox(line)[2] for line in lines) + 40
    height = (len(lines) * line_height) + 60  # Extra padding for title and borders

    img = Image.new("RGB", (max_width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    # Draw title
    draw.text((20, 15), title, font=font_bold, fill=(255, 255, 255))

    # Draw separator line
    draw.line([(10, 45), (max_width - 10, 45)], fill=(100, 100, 100), width=1)

    # Draw text lines with basic syntax highlighting
    y = 60
    for line in lines:
        # Simple color coding
        color = (220, 220, 220)  # Default light gray
        if line.startswith("[*]"):
            color = (100, 200, 255)  # Blue for info
        elif line.startswith("[x]"):
            color = (150, 255, 150)  # Green for sent/ACK
        elif line.startswith("[!]"):
            color = (255, 180, 100)  # Orange for warnings/bad
        elif line.startswith("[Ravi]") or line.startswith("[Priya]") or line.startswith("[Arjun]") or line.startswith("[Meena]") or line.startswith("[Karthik]") or line.startswith("[Control]"):
            if "ACK" in line:
                color = (150, 255, 150)  # Green for ACK
            elif "NACK" in line:
                color = (255, 100, 100)  # Red for NACK
            else:
                color = (200, 200, 100)  # Yellow for driver logs
        elif line.startswith("="):
            color = (120, 120, 120)

        draw.text((20, y), line, font=font, fill=color)
        y += line_height

    img.save(output_path)
    print(f"[+] Screenshot saved to {output_path}")

# Generate D2 Screenshot (Dispatcher + Drivers)
d2_lines = []
capture = False
for line in output.splitlines():
    if "DISPATCHER CONSOLE OUTPUT" in line:
        capture = True
    if "DRIVER CONSOLE OUTPUTS" in line:
        break
    if capture:
        d2_lines.append(line)

d2_text = "\n".join(d2_lines)
create_screenshot(d2_text, D2_SCREENSHOT, "D2: Dispatcher & Driver Simulation")

# Generate D3 Screenshot (ACK/NACK details)
d3_lines = []
capture = False
for line in output.splitlines():
    if "DRIVER CONSOLE OUTPUTS" in line:
        capture = True
    if capture:
        d3_lines.append(line)

d3_text = "\n".join(d3_lines)
create_screenshot(d3_text, D3_SCREENSHOT, "D3: ACK/NACK Handling Simulation")

print("[+] All screenshots generated successfully!")