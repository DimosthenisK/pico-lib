from ssd1306 import SSD1306

screen = SSD1306(sda=4, scl=5, width=128, height=64)
screen.text("Hello, world!")
