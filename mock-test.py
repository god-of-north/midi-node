from MockLCD import CharLCD
import time

display = CharLCD()

display.clear()

display.cursor_pos = (2, 0)
display.write_string("Hello")

time.sleep(1)

display.cursor_pos = (2, 2)
display.write_string("World!")

time.sleep(1)

display.cursor_pos = (0, 4)
display.write_string("Done.")

time.sleep(1)
display.cursor_pos = (2, 1)
display.write_string("Hi\rYo\nTest")
time.sleep(1)
display.write_string(display.cursor_pos.__str__())
