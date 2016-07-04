import time
import random
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

SSD1351_WIDTH = 128
SSD1351_HEIGHT = 128

RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

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
	def __init__(self):
		""" Initialize the SSD1351 """

		print "__init__"


		# Dimensions
		self.width = SSD1351_WIDTH
		self.height = SSD1351_HEIGHT

		self._pages = self.height / 8
		self._buffer = [0] * (self.width * self.height)

		self._gpio = GPIO.get_platform_gpio()

		# Set up reset pin
		self._rst = RST
		self._gpio.setup(self._rst, GPIO.OUT)

		# Set up hardware SPI
		self._spi = SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000)
		self._spi.set_clock_hz(8000000)

		# Set up DC pin
		self._dc = DC
		self._gpio.setup(self._dc, GPIO.OUT)

	def command(self, c):
		""" Send command byte to display """

		self._gpio.set_low(self._dc)
		self._spi.write([c])

	def data(self, c):

		self._gpio.set_high(self._dc)
		self._spi.write([c])

	def invert(self):
		self.command(SSD1351_CMD_NORMALDISPLAY)


	def initialize(self):
		""" Initialize the display """

		print "Initialize..."

		self.command(SSD1351_CMD_COMMANDLOCK)  # set command lock
		self.data(0x12)
		self.command(SSD1351_CMD_COMMANDLOCK)  # set command lock
		self.data(0xB1)
		self.command(SSD1351_CMD_DISPLAYOFF)   # 0xAE
		self.command(SSD1351_CMD_CLOCKDIV)     # 0xB3
		self.command(0xF1)  				   # 7:4 = Oscillator Frequency, 3:0 = CLK Div Ratio (A[3:0]+1 = 1..16)
		self.command(SSD1351_CMD_MUXRATIO)
		self.data(127)
		self.command(SSD1351_CMD_SETREMAP)
		self.data(0x74)
		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(0x00)
		self.data(0x7F)
		self.command(SSD1351_CMD_SETROW)
		self.data(0x00)
		self.data(0x7F)

		self.command(SSD1351_CMD_STARTLINE)  # 0xA1
		#self.data(96)
		self.data(0)

		self.command(SSD1351_CMD_DISPLAYOFFSET) 	# 0xA2
		self.data(0x0)
		self.command(SSD1351_CMD_SETGPIO)
		self.data(0x00)
		self.command(SSD1351_CMD_FUNCTIONSELECT)
		self.data(0x01)                         #internal (diode drop)
		self.command(SSD1351_CMD_PRECHARGE)  		# 0xB1
		self.command(0x32)
		self.command(SSD1351_CMD_VCOMH)  			# 0xBE
		self.command(0x05)
		self.command(SSD1351_CMD_NORMALDISPLAY)  	# 0xA6
		self.command(SSD1351_CMD_CONTRASTABC)
		self.data(0xC8)
		self.data(0x80)
		self.data(0xC8)
		self.command(SSD1351_CMD_CONTRASTMASTER)
		self.data(0x0F)
		self.command(SSD1351_CMD_SETVSL)
		self.data(0xA0)
		self.data(0xB5)
		self.data(0x55)
		self.command(SSD1351_CMD_PRECHARGE2)
		self.data(0x01)

		self.command(SSD1351_CMD_DISPLAYON)

	def begin(self):
		""" Initialize the display """

		print "Beginning..."

		self.reset()
		self.initialize()

	def reset(self):
		""" Reset the display
		This does not clear the display. What does it do?

		"""

		print "Resetting display..."

		# Set reset high for a millisecond
		self._gpio.set_high(self._rst)
		time.sleep(0.001)

		# Set reset low for 10 ms
		self._gpio.set_low(self._rst)
		time.sleep(0.010)

		# Set reset high again
		self._gpio.set_high(self._rst)

	def clear(self):
		""" Clear the display """

		print "Clear..."

		self._buffer = [0] * (self.width * self.height)

	def display(self):
		""" Write the buffer to the hardware """

		print "Display..."

		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(0)
		self.data(self.width - 1) # Column end address

		self.command(SSD1351_CMD_SETROW)
		self.data(0)
		self.data(self.height - 1) # Row end

		# Write buffer data
		self._gpio.set_high(self._dc)
		self.command(SSD1351_CMD_WRITERAM)
		self._spi.write(self._buffer)

	def rawfill(self, x, y, w, h, color):
		if (x >= self.width) or (y >= self.height):
			return

		if y+h > self.height:
			h = self.height-y-1

		if x+w > self.width:
			w = self.width-x-1

		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(x)
		self.data(x+w-1)

		self.command(SSD1351_CMD_SETROW)
		self.data(y)
		self.data(y+h-1)

		self.command(SSD1351_CMD_WRITERAM)
		for num in range(0, w*h):
			self.data(color >> 8)
			self.data(color)

	def color565(self, r, g, b):
                """ Define color in 16-bit RGB565. Red and blue
                have five bits each and green has 6 (since the
                eye is more sensitive to green).

                Format: 0bRRRR RGGG GGGB BBBB
                """

 		c = r >> 3
		c <<= 6
		c |= g >> 2
		c <<= 5
		c |= b >> 3
		return c

	def image(self, image):
		""" Set buffer to PIL image """

		#im = Image.new("RGB", (128, 128), "white")
		#draw = ImageDraw.Draw(im)
		#draw.line((0,0) + im.size, fill = 0x001F)


		#font = ImageFont.truetype("Casino.ttf", 10)
		#draw.text((10, 10), u"0068", fill = 0x0000, font=font)

		#im = Image.open("globe.png")
		im = image
		im = im.resize((self.width, self.height), Image.ANTIALIAS)
		im = im.convert("RGB")

		pix = im.load()

		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(0)
		self.data(self.width - 1) # Column end address

		self.command(SSD1351_CMD_SETROW)
		self.data(0)
		self.data(self.height - 1) # Row end

		self.command(SSD1351_CMD_WRITERAM)

		for row in xrange(0, self.height):
			for col in xrange(0, self.width):
				r,g,b = pix[col, row]
				color = self.color565(r,g,b)
				self.data(color >> 8)
				self.data(color)

	def scroll(self):
                """ Attempt to scroll """
                #self.command(SSD1351_CMD_STARTLINE)
                #self.data(28)
                #self.display()
                #this works

                for i in xrange(0, 127):
                        self.command(SSD1351_CMD_STARTLINE)
                        self.data(i)
                        #self.display()

                        #time.sleep(0.01)

                        self.command(SSD1351_CMD_SETCOLUMN)
                        self.data(0)
                        self.data(self.width - 1) # Column end address

                        self.command(SSD1351_CMD_SETROW)
                        self.data(i-1)
                        self.data(i-1) # Row end

                        # Write buffer data
                        self._gpio.set_high(self._dc)
                        self.command(SSD1351_CMD_WRITERAM)
                        for num in range(0, 127):
                                self.data(0xFFFF >> 8)
                                self.data(0xFFFF)

                        #time.sleep(0.0001)
                        #self.display()

	def scroll2(self, newrow):
                """ Attempt to scroll. Newrow is an array [127]"""
                #self.command(SSD1351_CMD_STARTLINE)
                #self.data(28)
                #self.display()
                #this works

                for i in xrange(0, 127):
                        self.command(SSD1351_CMD_STARTLINE)
                        self.data(i)
                        #self.display()

                        #time.sleep(0.01)

                        self.command(SSD1351_CMD_SETCOLUMN)
                        self.data(0)
                        self.data(self.width - 1) # Column end address

                        self.command(SSD1351_CMD_SETROW)
                        self.data(i-1)
                        self.data(i-1) # Row end

                        # Write buffer data
                        self._gpio.set_high(self._dc)
                        self.command(SSD1351_CMD_WRITERAM)
                        for num in xrange(len(newrow)):
                                self.data(newrow[num] >> 8)
                                self.data(newrow[num])

                        #time.sleep(0.0001)
                        #self.display()

        def scroll_reel(self, reel):
                """ Scroll a reel indefinitely """

                n_symbols = len(reel.symbols)

                # Show the current symbol
                self.image(reel.symbols[0])

                current_symbol = 1
                current_line = 0

                while True:
                        # Scroll image by one line
                        self.command(SSD1351_CMD_STARTLINE)
                        self.data(i)

                        # Get the next line
                        line = 1



                for i in range(n_symbols):
                        pass




class Slot_Reel(object):
        """ A simple slot machine reel """

        def __init__(self):
                """ Create the six symbols """

                self.symbols = []

                names = ["Liberty Bell", "Heart", "Diamond", "Spade",
                         "Horseshoe", "Star"
                        ]

                colors = [0x451F, 0x87F0, 0xFFF0, 0x2222, 0xFC10, 0x9659]

                for i in range(len(names)):
                        reel_im = self.create_symbol(names[i], colors[i])
                        self.symbols.append(reel_im)

                # Pixelate the images



        def create_symbol(self, name, color):
                """ Use PIL to create a symbol """

		im = Image.new("RGB", (128, 128), color)
		draw = ImageDraw.Draw(im)

		draw.text((5, 60), name, fill = 0x0000)

		return im




def main():
	print "Start"
	oled = Adafruit_SSD1351()

	print "Created oled"
	oled.begin()
	oled.clear()
	oled.display()
	#oled.invert()

	#oled.rawfill(10, 10, 40, 40, 0xFFFF)

	#for i in xrange(2): #xrange(0x0000, 0xFFFF):
	#	j = random.randint(0x0000, 0xFFFF)
	#	oled.rawfill(0, 0, 128, 128, j)
	#	time.sleep(0.001)


	#oled.scroll()

	reel = Slot_Reel()
        im = reel.symbols[0]
        oled.image(im)

        while True:
                r = random.randint(0x0000, 0xFFFF)
                g = random.randint(0x0000, 0xFFFF)
                b = random.randint(0x0000, 0xFFFF)
                color = oled.color565(r, g, b)
                oled.scroll2([color] * 128)

	#for i in range(len(reel.symbols)):
        #        im = reel.symbols[i]
        #        oled.image(im)
        #        time.sleep(0.01)

        #while True:


	print "End."

if __name__ == "__main__":
	main()

