import time
import random
import glob
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

SSD1351_WIDTH = 128
SSD1351_HEIGHT = 128

RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

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
        """ Controller for Adafruit SSD1351 1.5" Color OLED: http://adafru.it/1431 """

	def __init__(self, width, height, rst, dc, spi=None, spi_port=None, spi_device=None, gpio=None):
		""" Initialize the SSD1351

                width: pixel width (128)
                height: pixel height (128)

                rst: reset pin
                dc: dc pin

                spi: SPI device
                        spi_port: if SPI object is not passed, then use this spi port
                        spi_device: if SPI object is not passed, use this spi device

                gpio: GPIO device. If GPIO is not passed, use the platform gpio

                """

		# Set screen dimensions
		self.width = width
		self.height = height

                # Set up GPIO
                if gpio is not None:
                        self._gpio = gpio
                else:
                        self._gpio = GPIO.get_platform_gpio()

                # Set up pins
                self._rst = rst
                self._dc = dc
                self._gpio.setup(self._rst, GPIO.OUT)
                self._gpio.setup(self._dc, GPIO.OUT)

                # Set up SPI
                if spi is not None:
                        self._spi = spi
                else:
                        if spi_port is None or spi_device is None:
                                raise ValueError("spi_port and spi_dev must be set if no spi object is passed")
                        self._spi = SPI.SpiDev(spi_port, spi_device, max_speed_hz=8000000)

                        self._spi.set_clock_hz(8000000)

                # Create buffer for images
                self._buffer = [0] * (self.width * self.height)
                self._current_row = 0

	def command(self, c):
		""" Send command byte to display """

		self._gpio.set_low(self._dc)
		self._spi.write([c])

	def data(self, c):
                """ Send data byte to display """

		self._gpio.set_high(self._dc)
		self._spi.write([c])

	def initialize(self):
		""" Initialize the display """

                # Sending 0x12 unlocks the OLED drive IC and the driver will respond
                # to command and memory access
		self.command(SSD1351_CMD_COMMANDLOCK)  # set command lock
		self.data(0x12)

		# Not sure of the purpose of sending 0xB1 (if any)
		self.command(SSD1351_CMD_COMMANDLOCK)  # set command lock
		self.data(0xB1)

                # Sleep mode on (that is, display is off)
		self.command(SSD1351_CMD_DISPLAYOFF)   # 0xAE

		# Set front clock divider and oscillator frequency
		self.command(SSD1351_CMD_CLOCKDIV)     # 0xB3
		self.command(0xF1) # 7:4 = Oscillator Frequency, 3:0 = CLK Div Ratio (A[3:0]+1 = 1..16)

                # Set the multiplex ratio.
		self.command(SSD1351_CMD_MUXRATIO)
		self.data(127)

		# Set the remapping
		self.command(SSD1351_CMD_SETREMAP)
		# 0x74 = 1110100
        	# A[0] = Address increment mode. 0 = horizontal address increment mode; 1 = vertical address increment mode
                # A[1] = Column address remap. 0 = RAM 0~127 maps to Col0~127; 1 = RAM 0~127 maps to Col127~0
                # A[2] = Color remap. 0 = (reset) color sequence A -> B -> C; 1 = color sequence C -> B -> A
                # A[4] = COM scan direction remap. 0 = scan from up to down, 1 = scan from bottom to up
                # A[5] = Odd even splits of COM pins. 0 = (reset) odd/even; 1 = ?
                # A[7:6] = Display color mode. Select either 262l, 65;, 265 color mode
		self.data(0x74)

		# Column selection
		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(0x00)
		self.data(0x7F) # 127 in decimal

		# Row selection
		self.command(SSD1351_CMD_SETROW)
		self.data(0x00)
		self.data(0x7F) # 127 in decimal

                # Set display start line. We like to start at the top (zero)
		self.command(SSD1351_CMD_STARTLINE)
		self.data(0) # This may be 96 for the 128x96 screen?

                # Set the display offset
		self.command(SSD1351_CMD_DISPLAYOFFSET)
		self.data(0x00)

		# Set the GPIO options
		self.command(SSD1351_CMD_SETGPIO)
		self.data(0x00)

		# Enable or disable the VDD register.
		self.command(SSD1351_CMD_FUNCTIONSELECT)
		self.data(0x01)

		# Set the phase length of the OLED
		self.command(SSD1351_CMD_PRECHARGE)
		self.command(0x32)

		# Set voltage
		self.command(SSD1351_CMD_VCOMH)
		self.command(0x05) # This is the reset value

		# Set the display on
		self.command(SSD1351_CMD_NORMALDISPLAY)

		# Set the contrast current for each color (0x00 to 0xFF)
		self.command(SSD1351_CMD_CONTRASTABC)
		self.data(0xC8)
		self.data(0x80)
		self.data(0xC8)

		# Master contrast current control. The smaller the master current, the dimmer the OLED.
		# 16 steps: 0000b to 1111b (default)
		self.command(SSD1351_CMD_CONTRASTMASTER)
		self.data(0x0F) # Max

		# Set the low voltage
		self.command(SSD1351_CMD_SETVSL)
		self.data(0xA0)
		self.data(0xB5)
		self.data(0x55)

		# Set the second precharge period
		self.command(SSD1351_CMD_PRECHARGE2)
		self.data(0x01) # Minimum: 1 DCLKS

		# Leave sleep mode
		self.command(SSD1351_CMD_DISPLAYON)

	def reset(self):
		""" Reset the display. When reset is pulled low, the chip is
                initialized with the following state:

                1. Display is OFF
                2. 128 MUX display mode
                3. Normal segment address mapping
                4. Display start line is set to RAM address 0
                5. Column address counter is set to 0
                6. Normal scan direction of the COM outputs
                7. Some commands locked
		"""

		# Set reset high for a millisecond
		self._gpio.set_high(self._rst)
		time.sleep(0.001)

		# Set reset low for 10 ms
		self._gpio.set_low(self._rst)
		time.sleep(0.010)

		# Set reset high again
		self._gpio.set_high(self._rst)

	def begin(self):
		""" Initialize the display """

		self.reset()
		self.initialize()

	def clear_buffer(self):
		""" Clear the display buffer """

		self._buffer = [0] * (self.width * self.height)

	def display(self):
		""" Write the complete buffer to the display """

		self.command(SSD1351_CMD_SETCOLUMN)
		self.data(0)
		self.data(self.width - 1) # Column end address

		self.command(SSD1351_CMD_SETROW)
		self.data(0)
		self.data(self.height - 1) # Row end

		# Write buffer data
		self._gpio.set_high(self._dc)
		self.command(SSD1351_CMD_WRITERAM)
		for i in xrange(len(self._buffer)):
                        self.data(self._buffer[i] >> 8)
                        self.data(self._buffer[i])

        def display_scroll(self, new_row):
                """ Add a new line to the bottom and scroll the current image up.
                new_row should be length self.width
                """
                assert len(new_row) == self.width

                # Increment the scrolling row
                self._current_row = self._current_row + 1
                if self._current_row >= self.height:
                        self._current_row = 0

                # Set scrolling to the current place
                self.command(SSD1351_CMD_STARTLINE)
                self.data(self._current_row)

                # Set up for writing this one row
                self.command(SSD1351_CMD_SETCOLUMN)
                self.data(0)
                self.data(self.width - 1) # Column end address

                self.command(SSD1351_CMD_SETROW)
                self.data(self._current_row - 1)
                self.data(self._current_row - 1)

                # Write buffer data
                self._gpio.set_high(self._dc)
                self.command(SSD1351_CMD_WRITERAM)
                for i in xrange(len(new_row)):
                        self.data(new_row[i] >> 8)
                        self.data(new_row[i])

                time.sleep(0.005)

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

	def load_image(self, image):
		""" Set buffer to PIL image """

                # Make sure it's an RGB with correct width and height
		image = image.resize((self.width, self.height), Image.ANTIALIAS)
		image = image.convert("RGB")

                # Extract the pixels
		pix = image.load()

		# Add each pixel to the buffer
		i = 0
		w, h = image.size
		for col in xrange(0, w):
			for row in xrange(0, h):
				r,g,b = pix[col, row]
				color = color565(r, g, b)
				self._buffer[i] = color
				i += 1



class Slot_Reel(object):
        """ A simple slot machine reel """

        def __init__(self):
                """ Create the six symbols """

                self.symbols = []

                #names = ["Liberty Bell", "Heart", "Diamond", "Spade",
                #         "Horseshoe", "Star"
                #        ]

                #colors = [0x451F, 0x87F0, 0xFFF0, 0x2222, 0xFC10, 0x9659]

                #for i in range(len(names)):
                #        reel_im = self.create_symbol(names[i], colors[i])
                #        self.symbols.append(reel_im)

                #cherry = Image.open("cherry.png")
		#cherry = cherry.resize((128, 128), Image.ANTIALIAS)
		#cherry = cherry.convert("RGB")

                #self.symbols.append(cherry)

                files = glob.glob("./icons/*.png")

                for file in files:
                        im = Image.open(file)
                        imsize = im.size
                        if imsize != (128, 128):
                                print "resizing %s from %i, %i" % (file, imsize[0], imsize[1])
                                border_128 = (128-imsize[0], 128-imsize[1])
                                print border_128
                                im = ImageOps.expand(im, border=(16,16, 16, 16)) #border=border_128)
                                print "resized %s to %i, %i" % (file, im.size[0], im.size[1])
                        #im = im.resize((128, 128), Image.ANTIALIAS)
                        im = im.convert("RGB")
                        self.symbols.append(im)
                        
                oled = Adafruit_SSD1351(SSD1351_WIDTH,
                                        SSD1351_HEIGHT,
                                        rst=RST,
                                        dc=DC,
                                        spi_port=SPI_PORT,
                                        spi_device=SPI_DEVICE)

        def create_symbol(self, name, color):
                """ Use PIL to create a symbol """

		im = Image.new("RGB", (128, 128), color)
		draw = ImageDraw.Draw(im)

		draw.text((5, 60), name, fill = 0x0000)

		return im

	def get_row(self, symbol_index, row_number):
                """ Get the values for a single row """

                image = self.symbols[symbol_index]

                pix = image.load()

                w, h = image.size

                row = []

                for col in xrange(0, w):
                        r,g,b = pix[col, row_number]
			color = color565(r, g, b)
			row.append(color)

		return row

	def __iter__(self):
                """ Return an iterator """

                return Slot_Reel_Iterator(self, len(self.symbols), 128) # TODO: remove hardcoded number

class Slot_Reel_Iterator(object):
        """ Iterate through the slot reel and get the rows """

        def __init__(self, slot_reel, nbr_symbols, max_rows):
                """ Initalize the iterator """

                self.slot_reel = slot_reel
                self.nbr_symbols = nbr_symbols
                self.max_rows = max_rows

                self.current_symbol = 0
                self.current_row = 0

        def __iter__(self):
                """ Return self as an iterator """
                return self

        def next(self):
                """ Return the next item in the iteration """

                self.current_row = self.current_row + 1
                
                if self.current_row >= self.max_rows:
                        # Reached the end of the current symbol
                        self.current_symbol = self.current_symbol + 1
                        self.current_row = 0

                if self.current_symbol >= self.nbr_symbols:
                        self.current_symbol = 0

                # Return the details for the current row
                return self.slot_reel.get_row(self.current_symbol, self.current_row)
                        
                




def main():
	print "Start"
	oled = Adafruit_SSD1351(SSD1351_WIDTH, SSD1351_HEIGHT, rst=RST, dc=DC, spi_port=SPI_PORT, spi_device=SPI_DEVICE)

	print "Created oled"
	oled.begin()
	oled.clear_buffer()
	oled.display()
	#oled.invert()

	oled.load_image(Image.open("globe.png"))
	oled.display()
	#oled.display_area(10, 10, 60, 60)

        #while True:
        #       r = random.randint(0x0000, 0xFFFF)
        #       g = random.randint(0x0000, 0xFFFF)
        #       b = random.randint(0x0000, 0xFFFF)
        #       color = color565(r, g, b)
        #       for i in range(128):
        #               oled.display_scroll([color] * 128)


        time.sleep(0.5)

        slot_reel = Slot_Reel()

        for symbol in slot_reel:
                oled.display_scroll(symbol)

        

	print "End."

def color565(red, green=None, blue=None):
        """ Define color in 16-bit RGB565. Red and blue
        have five bits each and green has 6 (since the
        eye is more sensitive to green).

        Bit Format: RRRR RGGG GGGB BBBB

        Usage:
        color565(red=[0,255], green=[0,255], blue=[0,255)
        color565(0xFFE92)
        """

        if green is None and blue is None:
                # We were passed the full value in the first argument
                hexcolor = red
                red = (hexcolor >> 16) & 0xFF
                green = (hexcolor >> 8) & 0xFF
                blue = hexcolor & 0xFF

        # We have 8 bits coming in 0-255
        # So we truncate the least significant bits
        # until there's 5 bits for red and blue
        # and six for green
        red >>= 3
        green >>= 2
        blue >>= 3

        # Now move them to the correct locations
        red <<= 11
        green <<= 5

        # Then "or" them together
        result = red | green | blue

        return result

if __name__ == "__main__":
	main()
