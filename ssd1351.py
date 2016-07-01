import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

SSD1351_WIDTH = 128
SSD1351_HEIGHT = 128

# Timing Delays
SSD1351_DELAYS_HWFILL	=   3
SSD1351_DELAYS_HWLINE   =   1

# SSD1351 Commands
SSD1351_CMD_SETCOLUMN =		0x15
SSD1351_CMD_SETROW =   		0x75
SSD1351_CMD_WRITERAM = 		0x5C
SSD1351_CMD_READRAM =  		0x5D
SSD1351_CMD_SETREMAP =		0xA0
SSD1351_CMD_STARTLINE =		0xA1
SSD1351_CMD_DISPLAYOFFSET =	0xA2
SSD1351_CMD_DISPLAYALLOFF =	0xA4
SSD1351_CMD_DISPLAYALLON = 	0xA5
SSD1351_CMD_NORMALDISPLAY =	0xA6
SSD1351_CMD_INVERTDISPLAY =	0xA7
SSD1351_CMD_FUNCTIONSELECT =	0xAB
SSD1351_CMD_DISPLAYOFF =	0xAE
SSD1351_CMD_DISPLAYON =    	0xAF
SSD1351_CMD_PRECHARGE =		0xB1
SSD1351_CMD_DISPLAYENHANCE = 	0xB2
SSD1351_CMD_CLOCKDIV =		0xB3
SSD1351_CMD_SETVSL =		0xB4
SSD1351_CMD_SETGPIO =		0xB5
SSD1351_CMD_PRECHARGE2 =	0xB6
SSD1351_CMD_SETGRAY =		0xB8
SSD1351_CMD_USELUT =		0xB9
SSD1351_CMD_PRECHARGELEVEL =	0xBB
SSD1351_CMD_VCOMH =		0xBE
SSD1351_CMD_CONTRASTABC	=	0xC1
SSD1351_CMD_CONTRASTMASTER =	0xC7
SSD1351_CMD_MUXRATIO =          0xCA
SSD1351_CMD_COMMANDLOCK =       0xFD
SSD1351_CMD_HORIZSCROLL =       0x96
SSD1351_CMD_STOPSCROLL =        0x9E
SSD1351_CMD_STARTSCROLL =       0x9F

class Adafruit_SSD1351(object):
	def __init__(self, cs, rs, sid, sclk, rst):
		""" Initialize the SSD1351 """
		self._cs = cs
		self._rs = rs
		self._sid = sid
		self._sclk = sclk
		self._rst = rst

	# Drawing primitives 

	def draw_pixel(self, x, y, color):
		""" Draw a single pixel """
		pass

	def fill_rect(self, x0, y0, w, h, color):
		""" Draw a filled rectangle """
		pass

	def draw_fast_hline(self, x, y, w, color):
		""" Draw fast horizontal line? """
		pass

	def draw_fast_vline(self, x, y, h, color):
		""" Draw fast vertical line """
		pass

	def fill_screen(self, color):
		""" Fill the screen with color """
		pass

	# Commands
	def invert(self):
		pass

	def begin(self):
		pass

	def goto(self, x, y):
		pass

	# Low level

	def write_data(self, d):
		pass

	def write_command(self, c):
		pass

	def write_data_unsafe(self, d):
		pass

	def set_write_dir(self):
		pass

	def write8(self):
		pass

	def _spiwrite(self):
		pass

	def _raw_fill_rect(self, x, y, w, h, color):
		pass

	def _raw_fast_hline(self, x, y, w, color):
		pass

	def _raw_fast_vline(self, x, y, h, color):
		pass

def main():
	print "Start"

if __name__ == "__main__":
	main()
	