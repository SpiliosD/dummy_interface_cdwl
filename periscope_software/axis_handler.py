from lib_nanotec import *
import time
import threading
import re
import os
import sys

# CAUTION: Package this software to an executable file using the following command
# pyinstaller --onefile  --name "Wind Positioner" .\axis_handler.py --add-binary ".env/Lib/site-packages/nanotec_nanolib/_nanolib_python_3_12.pyd;nanotec_nanolib" --add-binary ".env/Lib/site-packages/nanotec_nanolib/*.dll;nanotec_nanolib"

UNITS_PER_DEGREE = 78.57142857 # Best so far - Calculated using gear ratio
DEGREES_PER_UNIT = 0.012727144178 #360.0 / 28300  # 0.0127

def get_base_dir():
	if getattr(sys, 'frozen', False):
		# When running as a PyInstaller executable
		return os.path.dirname(sys.executable)
	else:
		# When running as a script
		return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
CONFIG_FILE_PATH = os.path.join(BASE_DIR, "system_configuration.txt")

class AxisHandler:
	def __init__(self):
		self.nanolib_helper		= None
		self.device_handle		= None
		self.selected_bus_hw	= None
		self.identifier_name	= "No Name"	# Name of the axis - set by user
		self.home_offset_steps	= 0			# Keep track of how far the hardware home switch is from the system zero (real parallel to earch position)
		self.is_homed			= False		# Keep track if the axis is homed - no move should be executed before homing
		self.is_homing			= False
		self.absolute_mode		= False		# Keep track if the executed move will move relative to the current position or to the system zero position
		self.is_moving			= False
		self.target_angle		= 0			# Keep track of the requested position of the axis [DEGREES]

	def setup(self, ip_address, bus_name, bus_specifier):
		"""
		Connects to motor driver with requested IP address

		:params: ip_address - IP address to connect to
		"""
		self.nanolib_helper, self.device_handle, self.selected_bus_hw = connection(ip_address, bus_name, bus_specifier)

# Configuration and Status
	def setStaticIp(self, ip_address):
		"""
		Reconfigures IP address to the requested one

		:params: ip_address - new IP address to set
		"""
		# Enable static IP
		self.nanolib_helper.write_number(self.device_handle, 1, Nanolib.OdIndex(0x2010, 0x00), 32)

		# Convert IP address to hexadecimal format
		ip_hex = ''.join([format(int(octet), '02X') for octet in ip_address.split('.')])
		ip_hex_value = int(ip_hex, 16)
		print("ip_hex:", ip_hex_value)
		print("ip_hex_value:", ip_hex_value)
		# Set the static IP address
		self.nanolib_helper.write_number(self.device_handle, ip_hex_value, Nanolib.OdIndex(0x2011, 0x00), 32)

		# Save the changes
		self.nanolib_helper.write_number(self.device_handle, 0x65766173, Nanolib.OdIndex(0x1010, 0x0C), 32)

		print('Static IP {} set successfully.'.format(ip_address))

		# Reset driver
		print("Resetting controller...")
		self.nanolib_helper.write_number(self.device_handle, 0x0000012C, Nanolib.OdIndex(0x2800, 0x01), 32)
		self.nanolib_helper.write_number(self.device_handle, 0x746F6F62, Nanolib.OdIndex(0x2800, 0x02), 32)

		# Reconnect to driver with new ip
		self.setup(ip_address)

	def setDHCP(self):
		"""
		Reconfigures IP address to DHCP
		"""
		# Enable DHCP [Factory Default]
		self.nanolib_helper.write_number(self.device_handle, 0x64, Nanolib.OdIndex(0x2010, 0x00), 32)

		# Save the changes
		self.nanolib_helper.write_number(self.device_handle, 0x65766173, Nanolib.OdIndex(0x1010, 0x0C), 32)

		# Reset driver
		print("Resetting controller...")
		self.nanolib_helper.write_number(self.device_handle, 0x0000012C, Nanolib.OdIndex(0x2800, 0x01), 32)
		self.nanolib_helper.write_number(self.device_handle, 0x746F6F62, Nanolib.OdIndex(0x2800, 0x02), 32)

	def getStatus(self):
		status_word = self.nanolib_helper.read_number(self.device_handle, Nanolib.OdIndex(0x6041, 0x00))

		if (status_word & 0b100000000000) == 0b100000000000:return "Not ready to switch on"
		elif (status_word & 0b100000000000) == 0b100000000001:return "Ready to switch on"
		elif (status_word & 0b100000000000) == 0b100000000011:return "Switched on"
		elif (status_word & 0b100000000000) == 0b100000000111:return "Operation enabled"
		elif (status_word & 0b100000000000) == 0b100000001000:return "Quick stop active"
		elif (status_word & 0b100000000000) == 0b100000001100:return "Fault reaction active"
		elif (status_word & 0b100000000000) == 0b100000001000:return "Fault"
		else: return "Switch on disabled"

	def getVelocity(self):
		return getVelocity(self.nanolib_helper, self.device_handle)

	def getError(self):
		error_word = self.nanolib_helper.read_number(self.device_handle, Nanolib.OdIndex(0x603F, 0x00))
		if error_word == 0x1000: return "General error"
		elif error_word == 0x2300: return  "Current at the controller output too large"
		elif error_word == 0x3100: return  "Overvoltage/undervoltage at controller input"
		elif error_word == 0x4200: return  "Temperature error within the controller"
		elif error_word == 0x5440: return  "Interlock error: Bit 3 in 60FDh is set to `0`, the motor may not start (see the section Interlock function in the chapter Digital inputs)"
		elif error_word == 0x6010: return  "Software reset (watchdog)"
		elif error_word == 0x6100: return  "Internal software error, generic"
		elif error_word == 0x6320: return  "Rated current must be set (203Bh:01h/6075h)"
		elif error_word == 0x7113: return  "Warning: Ballast resistor thermally overloaded"
		elif error_word == 0x7121: return  "Motor blocked"
		elif error_word == 0x7200: return  "Internal error: Correction factor for reference voltage missing in the OTP"
		elif error_word == 0x7305: return  "Sensor 1 (see 3204h) faulty"
		elif error_word == 0x7306: return  "Sensor 2 (see 3204h) faulty"
		elif error_word == 0x7307: return  "Sensor n (see 3204h), where n is greater than 2"
		elif error_word == 0x7600: return  "Warning: Nonvolatile memory full or corrupt; restart the controller for cleanup work"
		elif error_word == 0x8100: return  "Error during fieldbus monitoring"
		elif error_word == 0x8130: return  "CANopen only: `Life Guard` error or `Heartbeat` error"
		elif error_word == 0x8200: return  "CANopen only: Slave took too long to send PDO messages."
		elif error_word == 0x8210: return  "CANopen only: PDO was not processed due to a length error"
		elif error_word == 0x8220: return  "CANopen only: PDO length exceeded"
		elif error_word == 0x8240: return  "CANopen only: unexpected sync length"
		elif error_word == 0x8400: return  "Error in speed monitoring: slippage error too large"
		elif error_word == 0x8611: return  "Position monitoring error: Following error too large"
		elif error_word == 0x8612: return  "Position monitoring error: Limit switch exceeded"
	
	def isHomed(self): return self.is_homed
	
	def isHoming(self): return self.is_homing

	def isMoving(self): return self.is_moving
	
	def isAbsoluteMode(self): return self.absolute_mode

	def setName(self, new_name): self.identifier_name = new_name
	def getName(self): return self.identifier_name

	def setMode(self, absolute):
		"""Set the relativity of the next moves
		
		:params: absolute - True for absolute move, False for relative move"""
		self.absolute_mode = absolute
	def getMode(self): return self.absolute_mode

	def setHomePosition(self):
		"""Sets the home position of the axis to the current position
		
		"""
		setZero(self.nanolib_helper, self.device_handle)

	def getLocalPosition(self):
		"""Returns a local position relative to the machine zero, in degrees.
		
		:retrun: [Degrees]
		"""
		absolute_steps = getPosition(self.nanolib_helper, self.device_handle)	#Get position from motor driver
		absolute_angle = self.unitsToAngle(absolute_steps)					#Convert to angle in degrees
		return absolute_angle % 360												#Return relative to one rotation
	
	def getAbsolutePosition(self):
		"""Returns the absolute position of the axis in degrees
		
		:retrun: [Degrees]"""
		absolute_steps = getPosition(self.nanolib_helper, self.device_handle)	#Get position from motor driver
		return self.unitsToAngle(absolute_steps)	#Convert to angle in degrees

	def getEncoderPosition(self):
		return getEncoderValue(self.nanolib_helper, self.device_handle)

	def getTargetPosition(self):
		"""Returns the target position. The position the driver is ment to achieve.
		
		:return: [Degrees]"""
		return self.target_angle

# Movement
	def setHomeOffset(self, new_offset):
		"""
		Sets the home offset from the real position of the HOME switch

		:params: new_offset - new home offset [STEPS]
		"""
		self.home_offset_steps = new_offset

	def home(self):
		self.is_homing = True
		self.is_homed = False
		self.is_moving = True
		brake_engage(self.nanolib_helper, self.device_handle, False)
		set_move_homing(self.nanolib_helper, self.device_handle, self.home_offset_steps)
		print(self.identifier_name, " Homing")
		if start_move(self.nanolib_helper, self.device_handle):							# Go to Home Switch
			self.is_homed = True
			set_move(self.nanolib_helper, self.device_handle, 0, 50)
			print(self.identifier_name, " Zeroing")
			self.is_homed = start_move(self.nanolib_helper, self.device_handle)	# Go to Zero Position
		brake_engage(self.nanolib_helper, self.device_handle, True)
		self.is_moving = False
		self.is_homing = False

	def setupMove(self, angle, speed = speed_steps_normal):
		"""
		Configure parameters for next move execution.

		If the system is already moving, the method will only update the move parameters of the current move.

		:params: relative - True for relative move, False for absolute move
		:params: angle - requested position [DEGREES]
		:params: speed - speed in steps per second [Optional]
		"""
		if angle is not None: self.target_angle = angle # Update target angle
		elif angle is None: angle = self.target_angle

		print(self.identifier_name, " Moving to: ", angle, "°, Speed: ", speed, "RPM, Relative to ", "zero" if self.absolute_mode else "current", " position")

		if not self.is_moving:
			set_move(self.nanolib_helper, self.device_handle, self.angleToUnits(angle), speed)
		else:
			move_update(self.nanolib_helper, self.device_handle, self.angleToUnits(angle), speed)

	def initiateMove(self):
		"""
		Wrapper to start the move

		Better use `Trheading` to run parallel with other axes "start_move" since its a blocking method
		"""
		self.is_moving = True
		move_outcome = start_move(self.nanolib_helper, self.device_handle)
		self.is_moving = False
		if move_outcome:
			print(self.identifier_name, " Position Reached")
			brake_engage(self.nanolib_helper, self.device_handle, True)
		return move_outcome

	def updateSpeedOnly(self, speed):
		"""Update only motor speed without touching target position."""
		move_update(self.nanolib_helper, self.device_handle, None, speed)

	def stopMove(self, imediately = False):
		self.is_moving = False
		halt_move(self.nanolib_helper, self.device_handle, imediately)

	def disableMotor(self):
		disable_motor(self.nanolib_helper, self.device_handle)
# Helpers
	def angleToUnits(self, angle_deg):
		"""Convert angle in degrees to motor units (steps)."""
		if angle_deg is None: return None
		return int(round(angle_deg * UNITS_PER_DEGREE))

	def unitsToAngle(self, units):
		"""Convert motor units (steps) to angle in degrees."""
		if units is None: return None
		return units * DEGREES_PER_UNIT

#Command definitions
COMMAND_MOVE_TO_POSITION	= "GO"
COMMAND_POSITION_ABSOLUTE	= "A"
COMMAND_POSITION_RELATIVE	= "R"
COMMAND_HOME				= "HOME"
COMMAND_SET_HOME_PARAMETERS = "OFFSETS"
COMMAND_HOME_TO_CLOSER_ZERO = "ZERO"
COMMAND_STOP_IMEDIATELY		= "STOP"
COMMAND_BREAK_SLOWDOWN		= "BRAKE"
COMMAND_GET_POSITION		= "POSITION"
COMMAND_GET_STATUS			= "STATUS"
COMMAND_GET_ERROR			= "ERROR"
COMMAND_TERMINATE_PROGRAM	= "EXIT"
COMMAND_SCAN_NETWORK		= "NETWORK"
class CommandsHandler:
	"""
	Class to hanlde user commands from the terminal.
	The class expects the two axes objects on initialization so it can use their functionality.

	Its possible to use method `execute()` with a command string as argument, but take note that user input is not blocked, so all commands from all sources will be executed as they arrive.
	
	:params: elevation_axis - elevation axis object
	:params: azimuth_axis - azimuth axis object
	"""
	def __init__(self, elevation_axis, azimuth_axis):
		self.current_command = None
		self.elevation_axis = elevation_axis
		self.azimuth_axis = azimuth_axis
		self.last_move_print = time.time()
		live_position_thread = threading.Thread(target=self.printLivePosition, daemon=True, name="PositionThread")
		live_position_thread.start()

	def loop(self):
		"""Listen for user input on the terminal.
		
		**Use with threading to avoid blocking**
		"""
		while True:
			self.current_command = None
			self.current_command = input()
			self.execute(self.current_command)

	def execute(self, command):
		"""Execute the requested command.
		
		:params: command - command string
		"""	
		if COMMAND_MOVE_TO_POSITION in command.upper():
			pattern = re.escape(COMMAND_MOVE_TO_POSITION) + r",(-?\d+),(-?\d+),(\w+)"
			try:
				match = re.match(pattern, command.upper())
				if match is not None:
					azimuth_angle = int(match.group(1))
					elevation_angle = int(match.group(2))
					if match.group(3) == "A":
						# Check if axes are homed - so we are sure that zero is at the proper position relative to the machine
						if not self.elevation_axis.isHomed() and not self.azimuth_axis.isHomed():
							print("Axes are not homed - Only relative moves can be executed.")
							return 0
						self.elevation_axis.setMode(True)
						self.azimuth_axis.setMode(True)
					elif match.group(3) == "R":

						# Check if system is moving
						if self.elevation_axis.isMoving() or self.azimuth_axis.isMoving():
							print("Axes are moving - Wait for move completion before applying local coordinates.")
							return 0
						
						# Relative move: azimuth_angle and elevation_angle are deltas
						self.elevation_axis.setMode(False)
						self.azimuth_axis.setMode(False)

						# Read current absolute motor positions (degrees)
						azimuth_curr = self.azimuth_axis.getAbsolutePosition()
						elevation_curr = self.elevation_axis.getAbsolutePosition()

						# Compute new motor targets by applying deltas
						# Azimuth target is simply current azimuth + delta
						azimuth_angle = azimuth_curr + azimuth_angle

						# Elevation motor target derived so local elevation behaves correctly:
						# E_motor_target = E_motor_current + delta_elevation - delta_azimuth
						elevation_angle = elevation_curr + elevation_angle
					elif match.group(3) == "L":
						# L = Local positioning (0–360 domain for each axis)

						# Check if axes are homed - so we are sure that zero is at the proper position relative to the machine
						if not self.elevation_axis.isHomed() and not self.azimuth_axis.isHomed():
							print("Axes are not homed - Only relative moves can be executed.")
							return 0
						
						# Check if system is moving
						if self.elevation_axis.isMoving() or self.azimuth_axis.isMoving():
							print("Axes are moving - Wait for move completion before applying local coordinates.")
							return 0
						
						# Move to the requested local angles without unwinding absolute angles
						self.elevation_axis.setMode(True)
						self.azimuth_axis.setMode(True)
						# --- Read current local positions ---
						# Local azimuth is simply the wrapped physical angle
						local_az = self.azimuth_axis.getLocalPosition()

						A_abs = self.azimuth_axis.getAbsolutePosition()

						# --- Requested local targets (0–360 domain) ---
						target_local_az = azimuth_angle % 360

						# --- Find minimal angular travel (shortest path) ---
						delta_az = angle_diff(target_local_az, local_az)

						# --- Convert deltas into absolute motor targets ---
						# Azimuth motor: simple
						azimuth_angle = A_abs + delta_az
							
					else:
						print("Invalid move mode", match.group(3))
						return 0
				else:
					print("Invalid arguments for command", command)
					return 0
				
				# Setup moves
				self.elevation_axis.setupMove(elevation_angle - azimuth_angle, 24)
				self.azimuth_axis.setupMove(azimuth_angle, 24)

				# Start moves if the any of the axes is not moving - this avoids creating duplicate threads
				if not self.elevation_axis.isMoving(): elevation_tread = threading.Thread(target=lambda:self.elevation_axis.initiateMove(), name="ElevationThread")
				if not self.azimuth_axis.isMoving(): azimuth_tread = threading.Thread(target=lambda:self.azimuth_axis.initiateMove(), name="AzimuthThread")

				# Start threads if needed - this avoids starting a thread that is already running
				if not elevation_tread.is_alive(): elevation_tread.start()
				if not azimuth_tread.is_alive(): azimuth_tread.start()

				self.last_move_print = time.time()
			except:
				print("Invalid command.")

		if COMMAND_HOME == command.upper():
			self.azimuth_axis.home()
			self.azimuth_axis.setupMove(0, 200) #Locks azimuth motor to zero position
			self.azimuth_axis.initiateMove()
			time.sleep(0.2)
			self.elevation_axis.home()
			time.sleep(0.2)

			while self.elevation_axis.isMoving() or self.azimuth_axis.isMoving(): time.sleep(0.1)
			print("Axes at home")

		if COMMAND_HOME_TO_CLOSER_ZERO == command.upper():
			if not self.elevation_axis.isMoving() and not self.azimuth_axis.isMoving():
				print("Homing to local zero...")
				# Goto closest local zero
				self.execute("GO,0,0,L")
				while self.elevation_axis.isMoving() or self.azimuth_axis.isMoving(): time.sleep(0.1)
				self.elevation_axis.setHomePosition()
				self.azimuth_axis.setHomePosition()
				print("Axes at zero")
			else: print("Cannot zero while moving")

		if COMMAND_SET_HOME_PARAMETERS in command.upper():
			pattern = re.escape(COMMAND_SET_HOME_PARAMETERS) + r",(\d+),(\d+)"
			try:
				match = re.match(pattern, command.upper())
				if match is not None:
					print("Setting elevation home offset to: ", match.group(1))
					self.elevation_axis.setHomeOffset(int(match.group(1)))
					print("Setting azimuth home offset to: ", match.group(2))
					self.azimuth_axis.setHomeOffset(int(match.group(2)))

					# --- NEW: Update config and save file ---
					config["HOMING_OFFSET_STEPS_ELEVATION"] = str(match.group(1))
					config["HOMING_OFFSET_STEPS_AZIMUTH"] = str(match.group(2))
					write_configuration(config)
				else:
					print("Invalid arguments for command", command)
			except:
				print("Invalid command")

		if COMMAND_GET_STATUS == command.upper():
			print("Elevation axis status: ", self.elevation_axis.getStatus())
			print("Azimuth axis status: ", self.azimuth_axis.getStatus())

		if COMMAND_GET_ERROR == command.upper():
			print("Elevation axis error: ", self.elevation_axis.getError())
			print("Azimuth axis error: ", self.azimuth_axis.getError())

		if COMMAND_STOP_IMEDIATELY == command.upper():
			self.elevation_axis.stopMove(True)
			self.azimuth_axis.stopMove(True)

		if COMMAND_BREAK_SLOWDOWN == command.upper():
			self.elevation_axis.stopMove(False)
			self.azimuth_axis.stopMove(False)

		if COMMAND_GET_POSITION == command.upper():
			# Compute elevation position in correlation to azimuth position
			local_azimuth_pos = self.azimuth_axis.getLocalPosition()
			global_azimuth_pos = self.azimuth_axis.getAbsolutePosition()
			local_elevation_pos = (-self.elevation_axis.getLocalPosition() - local_azimuth_pos) % 360
			global_elevation_pos = -self.elevation_axis.getAbsolutePosition() - global_azimuth_pos
			print("Elevation position. Local:%.2f" % -local_elevation_pos, "Absolute:%.4f" % -global_elevation_pos)
			print("Azimuth position. Local:%.2f" % local_azimuth_pos, "Absolute:%.4f" % global_azimuth_pos)

		if COMMAND_TERMINATE_PROGRAM == command.upper():
			exit()

		if COMMAND_SCAN_NETWORK == command.upper():
			scan_for_nanotec_devices()

		return 1

	def printLivePosition(self):
		"""Prints live position of both axes every 100ms while moving.

		**Use with threading to avoid blocking**
		"""
		while True:
			if self.elevation_axis.isHoming() or self.azimuth_axis.isHoming(): continue
			if self.elevation_axis.isMoving() or self.azimuth_axis.isMoving():
				# Compute elevation position in correlation to azimuth position
				local_azimuth_pos = self.azimuth_axis.getLocalPosition()
				global_azimuth_pos = self.azimuth_axis.getAbsolutePosition()
				local_elevation_pos = (-self.elevation_axis.getLocalPosition() - local_azimuth_pos) % 360
				global_elevation_pos = -self.elevation_axis.getAbsolutePosition() - global_azimuth_pos
				print("Local Elevation:%.2f," % -local_elevation_pos, "Local Azimuth:%.2f" % local_azimuth_pos)
				time.sleep(0.1)


# Connect to axes
# elevation_nanolib_helper, elevation_device_handle, elevation_selected_bus_hw = connection('192.168.1.98')  # Elevation axis
# azimuth_nanolib_helper, azimuth_device_handle, azimuth_selected_bus_hw = connection('192.168.1.99')		# Azimuth axis


def main():
	elevation_axis = AxisHandler()
	azimuth_axis = AxisHandler()

	# Setup configuration from file
	global config 
	config = read_configuration()
	# Parse needed parameters (with defaults in case something is missing)
	ip_elev = config.get("IP_ADDRESS_ELEVATION", "192.168.1.98")
	ip_azim = config.get("IP_ADDRESS_AZIMUTH", "192.168.1.99")
	home_offset_elev = int(config.get("HOMING_OFFSET_STEPS_ELEVATION", 0))
	home_offset_azim = int(config.get("HOMING_OFFSET_STEPS_AZIMUTH", 0))
	network_adapter_hw_specifier = config.get("NETWORK_ADAPTER_SPECIFIER") # Variables of `lib_nanotec.py`
	network_adapter_hw_name = config.get("NETWORK_ADAPTER_NAME") # Variables of `lib_nanotec.py`
	
	try:	# Setup axes
		elevation_axis.setup(ip_elev, network_adapter_hw_name, network_adapter_hw_specifier)
		azimuth_axis.setup(ip_azim, network_adapter_hw_name, network_adapter_hw_specifier)
		
		try:	# Apply home offsets from configuration
			elevation_axis.setHomeOffset(home_offset_elev)
			azimuth_axis.setHomeOffset(home_offset_azim)
		except:
			print("Failed to set home offsets")
	except:
		print("Failed to connect to axis")

	# Set names
	elevation_axis.setName("ELEVATION")
	azimuth_axis.setName("AZIMUTH")

	# Start Idlers - This is just to stop holding of the motors after sometime to help with thermal contol.
	azimuth_idler_thread = threading.Thread(target=lambda:disableMotorsOnIdle(20, elevation_axis, azimuth_axis), daemon=True, name="AzimuthIdlerThread")
	azimuth_idler_thread.start()

	# Start the monitoring thread
	global elevation_correction_thread
	elevation_correction_thread = threading.Thread(target=lambda:elevationProportionalControler(elevation_axis, azimuth_axis), daemon=True, name="ElevationCorrectorThread")
	elevation_correction_thread.start()
	
	# Setup the commands handler
	command_handler = CommandsHandler(elevation_axis, azimuth_axis)
	commands_thread = threading.Thread(target=lambda:command_handler.loop(), daemon=True, name="CommandsThread")
	commands_thread.start()

	# In-software commands
	# time.sleep(1) # Wait for the threads to start
	# while not command_handler.execute("home"): continue
	# command_handler.execute("go,3600,-90,a") # Non blocking command
	# time.sleep(10)# No internal way of knowing when the position is reached so delay is mandatory.
	# command_handler.execute("go,108000,-90,a") # Non blocking command

	commands_thread.join()


def angle_diff(a, b):
	"""return smallest signed difference a - b, wrapped to [-180, 180]"""
	return (a - b + 180) % 360 - 180

def elevationProportionalControler(elevation_axis, azimuth_axis):
	"""Proportional controller to correct the Elevation drift in real time
		
	**Use with threading to avoid blocking**
	"""
	BASE_SPEED = 24
	MAX_SPEED = 100
	MIN_SPEED = 0
	KP = 0.8 # Proportional gain - limits the mid move change in degrees

	while True:
		if elevation_axis.isHoming() or azimuth_axis.isHoming():
			time.sleep(0.02)
			continue
		
		if not azimuth_axis.isMoving() or not elevation_axis.isMoving():
			time.sleep(0.02)
			continue
		
		# ----- determine azimuth direction -----
		azimuth_direction = 1 if azimuth_axis.getVelocity() > 0 else -1

		# ----- compute true elevation -----
		# elevation_local_pos = (-elevation_axis.getAbsolutePosition() - azimuth_axis.getAbsolutePosition()) % 360
		# elevation_local_target = (-elevation_axis.getTargetPosition() - azimuth_axis.getTargetPosition()) % 360
		elevation_local_pos = (-elevation_axis.getAbsolutePosition() - azimuth_axis.getAbsolutePosition())
		elevation_local_target = (-elevation_axis.getTargetPosition() - azimuth_axis.getTargetPosition())

		error_deg = angle_diff(elevation_local_target, elevation_local_pos)

		# PD correction term (start with P only)
		correction = KP * error_deg

		# Reverse correction if azimuth moves backward
		correction *= azimuth_direction

		azimuth_current_speed = abs(azimuth_axis.getVelocity())
		if azimuth_current_speed < BASE_SPEED:
			time.sleep(0.02)
			continue
		
		corrected_speed = azimuth_current_speed + correction
		corrected_speed = int(max(MIN_SPEED, min(MAX_SPEED, abs(corrected_speed))))

		elevation_axis.updateSpeedOnly(corrected_speed)

		# print(f"[CORR] dir:{azimuth_direction:+d} desired:{elevation_local_target:.2f}"
		# 		f" real:{elevation_local_pos:.2f} err:{error_deg:.2f}"
		# 		f" az_spd:{azimuth_current_speed} spd:{corrected_speed}")

		time.sleep(0.02)

def disableMotorsOnIdle(timeout, elevation_axis, azimuth_axis):
	"""Use in separate thread to monitor the idling of the system. The timer resets whenever a move is executed
	
	:params: timeout - time in seconds to wait before disabling motors
	"""
	timestamp = time.time()
	motor_enabled = True
	while True:
		if elevation_axis.is_moving or azimuth_axis.is_moving:
			timestamp = time.time()
			motor_enabled = True

		if time.time() - timestamp > timeout and motor_enabled:
			print("Motors Released")
			elevation_axis.disableMotor()
			azimuth_axis.disableMotor()
			motor_enabled = False

		time.sleep(timeout / 10)

def read_configuration(file_path=CONFIG_FILE_PATH):
    """
    Reads configuration parameters from a simple key=value text file.
    Returns a dictionary of settings.
    """
    config = {}
    if not os.path.exists(file_path):
        print(f"Configuration file '{file_path}' not found.")
        return config

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):  # Skip comments or empty lines
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

def write_configuration(config, file_path=CONFIG_FILE_PATH):
    """Writes dictionary data back to the configuration file."""
    with open(file_path, "w") as f:
        for key, value in config.items():
            f.write(f"{key} = {value}\n")
    print(f"Configuration saved to {file_path}.")


# Placeholder imports for required network scanning functionalities
from menu_utils import *
from bus_functions_example import *
from device_functions_example import *

def scan_for_nanotec_devices():
	"""
	Scans for available RESTfull API network adapters and searches for Nanotec devices in all of them
	"""
	# Get the NanoLib accessor
	accessor = Nanolib.getNanoLibAccessor()
	
	# Step 1: List available bus hardware
	result_bus = accessor.listAvailableBusHardware()
	if result_bus.hasError():
		print("Error listing bus hardware")
		exit(1)
	
	# Step 2: Find all RESTful API bus hardware
	bus_hw_list = result_bus.getResult()
	rest_buses = [bus for bus in bus_hw_list if bus.getProtocol() == "RESTful API"]
	
	if not rest_buses:
		print("No RESTful API buses found!")
		exit(1)
	
	# Step 3: Loop over all RESTful API buses
	for rest_bus in rest_buses:
		print(f"\nConnecting to bus: {rest_bus.getName()} ({rest_bus.getProtocol()}), id: {rest_bus.getHardwareSpecifier()}")
		
		# Prepare bus hardware options (usually empty for REST)
		bus_hw_options = Nanolib.BusHardwareOptions()
		open_result = accessor.openBusHardwareWithProtocol(rest_bus, bus_hw_options)
		
		if open_result.hasError():
			print(f"Error opening bus hardware {rest_bus.getName()}")
			continue  # skip to next bus
		
		print("Bus opened successfully!")
		
		# Step 4: Scan for devices on this bus
		scan_result = accessor.scanDevices(rest_bus, None)  # None = no callback
		if scan_result.hasError():
			print(f"Error scanning devices on {rest_bus.getName()}")
			continue
		
		device_list = scan_result.getResult()
		print(f"Devices found: {len(device_list)}")
		for device in device_list:
			print(f"- {device.getDescription()} [id: {device.getDeviceId()}]")

		# Optional: close bus after scanning to free resources
		# accessor.closeBusHardware(rest_bus)


main()
