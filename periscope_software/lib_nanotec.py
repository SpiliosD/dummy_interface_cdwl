from nanotec_nanolib import Nanolib
from ipaddress import IPv4Address
from nanolib_helper import *
import time

# DEFINITIONS
CONTROLWORD_BIT_SWITCHED_ON = 0
CONTROLWORD_BIT_ENABLE_VOLTAGE = 1
CONTROLWORD_BIT_QUICK_STOP = 2
CONTROLWORD_BIT_ENABLE_OPERATION = 3
CONTROLWORD_BIT_START_TRAVEL = 4
CONTROLWORD_BIT_TRAVEL_IMEDIATELY = 5
CONTROLWORD_BIT_POSITION_RELATIVE = 6
CONTROLWORD_BIT_FAULT_RESET = 7
CONTROLWORD_BIT_HALT = 8
CONTROLWORD_BIT_CHANGE_ON_SETPOINT = 9


speed_steps_slow = 50
speed_steps_normal = 200
speed_steps_fast = 400
speed_homing_slow = 50
speed_homing_normal = 100
speed_homing_fast = 200
speed_homing_search_switch = 10
current_requested_steps = 0	#The current requested position in steps


def connection(ip, bus_hw_name, bus_hw_specifier):
#____________________________connect____________________________
	# Initialize the NanoLib accessor and configure IP address for connection
	nanolib_accessor: Nanolib.NanoLibAccessor = Nanolib.getNanoLibAccessor()
	ip_address = IPv4Address(ip)
	nanolib_helper = NanolibHelper()
	# Set up access to NanoLib
	nanolib_helper.setup()
	
	# Define bus hardware settings (Ethernet/Wireless interfaces)
	# Development network adapter
	# bus_hw_specifier = '{F4AB1853-05BD-4705-BE23-68BF2E876E83}'
	# bus_hw_name = 'Ethernet (Intel(R) Ethernet Connection (11) I219-V)'

	# Lidar network adapter
	# bus_hw_specifier = '{31D84C2F-F494-4392-B46A-1915891AD3F9}'
	# bus_hw_name = 'Ethernet 2 (Intel(R) Ethernet Controller (3) I225-LM)'


	# Initialize bus hardware ID with specified settings
	selected_bus_hw: Nanolib.BusHardwareId = Nanolib.BusHardwareId(
		Nanolib.BUS_HARDWARE_ID_NETWORK,
		Nanolib.BUS_HARDWARE_ID_PROTOCOL_RESTFULL_API,
		bus_hw_specifier,
		bus_hw_name
	)
	
	# Open the bus hardware using REST API protocol
	nanolib_accessor.openBusHardwareWithProtocol(selected_bus_hw, Nanolib.BusHardwareOptions())
	
	# Establish a device connection using the specified IP address
	device_id = Nanolib.DeviceId(selected_bus_hw, int(ip_address), '')
	device_handle = nanolib_accessor.addDevice(device_id).getResult()
	result = nanolib_accessor.connectDevice(device_handle)
	print("Nanotec: Connect")
	#_______________________________________________________________
	#____________________________beginning__________________________
	# Stop any currently running NanoJ program
	nanoj_control = nanolib_helper.write_number(device_handle, 0, Nanolib.OdIndex(0x2300, 0x00), 32)  

	# Set speed
	nanolib_helper.write_number(device_handle, speed_homing_slow, Nanolib.OdIndex(0x6081, 0x00), 32)

	#____________________________init__________________________
	# Configure digital input settings - Read and print sensor values for debugging
	nanolib_helper.write_number(device_handle, 3, Nanolib.OdIndex(0x3240, 0x06), 32)
	sensor1 = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x3240, 0x06))
	print("sensor: 0x3240:6 --> ", sensor1)
	
	nanolib_helper.write_number(device_handle, 1, Nanolib.OdIndex(0x3240, 0x01), 32)
	sensor2 = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x3240, 0x01))
	print("sensor: 0x3240:1 --> ", sensor2)
	
	nanolib_helper.write_number(device_handle, 256, Nanolib.OdIndex(0x2057, 0x00), 32)
	microsteps = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x2057, 0x00))
	print("microsteps", microsteps)
	
	reg2058 = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x2058, 0x00))
	print("2058", reg2058)

	# Read and display the status to verify connection and device state
	status = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6041, 0x00))
	status = bin(status)
	print("status ", status)
	
	# Read error register for troubleshooting if necessary
	reg1003 = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x1003, 0x01))
	reg1003 = bin(reg1003)
	print("1003: ", reg1003)
	
	reg2010 = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x2010, 0x00))
	reg2010 = bin(reg2010)
	print("2010: ", reg2010)

	digital_input = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x60FD, 0x00))
	print(ip, "digital_input: ", digital_input)
	
	return nanolib_helper, device_handle, selected_bus_hw

# def getPosition(nanonlib_helper, device_handle):
# 	return nanonlib_helper.read_number(device_handle, Nanolib.OdIndex(0x6064, 0x00))

def getPosition(nanolib_helper, device_handle):
	"""
	Returns the current position of the motor in steps
	"""	
	position = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6064, 0x00))
	position = position & 0xffffffff
	position = (position ^ 0x80000000) - 0x80000000
	return position

def setZero(nanolib_helper, device_handle):
	# Copied directly from Plag n Drive 3
	nanolib_helper.write_number(device_handle, 0x06, Nanolib.OdIndex(0x6060, 0x00), 8) # Set mode of operation to homing
	nanolib_helper.write_number(device_handle, 0x00, Nanolib.OdIndex(0x2291, 0x01), 32) # PDI Command NOP
	nanolib_helper.write_number(device_handle, 0x11, Nanolib.OdIndex(0x2291, 0x04), 8) # PDI Command Homming on current position
	nanolib_helper.write_number(device_handle, 0x01, Nanolib.OdIndex(0x2291, 0x04), 8) # PDI Command Switch off motor
	nanolib_helper.write_number(device_handle, 0x00, Nanolib.OdIndex(0x6040, 0x00), 16) # Reset controlword

def getEncoderValue(nanolib_helper, device_handle):
	return nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6063, 0x00))

def getVelocity(nanolib_helper, device_handle):
	velocity =nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x606C, 0x00))
	velocity = velocity & 0xffffffff
	velocity = (velocity ^ 0x80000000) - 0x80000000
	return velocity

def set_move(nanolib_helper, device_handle, steps, speed = speed_steps_normal):
	"""
	Move to position

	:params: steps - number of steps to move or position
	:params: speed - speed in steps per second

	:return: 1 if successful, 0 if not
	"""
	# Save requested position for use by live correction
	current_requested_steps = steps
	# Setup move
	try:
		# Set NanoJ variables [Optional] (0x01 - From Plug&Drive)
		nanolib_helper.write_number(device_handle, 0x1, Nanolib.OdIndex(0x2500, 0x20), 32)
		# Set mode of operation
		nanolib_helper.write_number(device_handle, 0x1, Nanolib.OdIndex(0x6060, 0x00), 8)
		# Following are the "Quick Stop" and "Switch On" commands - This helps to start the move after change of mode or emergency stop
		# Enable motor movement by setting control word to "Quick Stop + Enable Voltage" (0x06 - From Plug&Drive)
		nanolib_helper.write_number(device_handle, 0x06, Nanolib.OdIndex(0x6040, 0x00), 16)
		# Enable motor movement by setting control word to "Switched ON" (0x07 - From Plug&Drive)
		nanolib_helper.write_number(device_handle, 0x07, Nanolib.OdIndex(0x6040, 0x00), 16)
		# Enable motor movement by setting control word to "Enable Operation" (0x0F - From Plug&Drive)
		nanolib_helper.write_number(device_handle, 0x0F, Nanolib.OdIndex(0x6040, 0x00), 16)
		# Set the desired target position in steps (positive or negative for direction control)
		nanolib_helper.write_number(device_handle, int(steps), Nanolib.OdIndex(0x607A, 0x00), 32) # For reverse direction, use steps * (-1)
		# Set the speed of the motor
		nanolib_helper.write_number(device_handle, speed, Nanolib.OdIndex(0x6081, 0x00), 32) # Set velocity magnitude
		# Set profile acceleration units[steps]
		nanolib_helper.write_number(device_handle, 200, Nanolib.OdIndex(0x6083, 0x00), 32)
		# Set profile deceleration units[steps]
		nanolib_helper.write_number(device_handle, 50, Nanolib.OdIndex(0x6084, 0x00), 32)
		# Set NanoJ variables [Optional] (0x0 - From Plug&Drive)
		nanolib_helper.write_number(device_handle, 0x0, Nanolib.OdIndex(0x2500, 0x20), 32)
	except Exception as e:
		print(f'Error11: {e}')
		if "Invalid device handle" in str(e):  # Stop execution if the error is critical
			print("Motor error detected! Stopping function execution...")
			return 0	
	return 1

def brake_engage(nanolib_helper, device_handle, enable):
	"""Engages the electromecanical brake"""
	if enable:
		nanolib_helper.write_number(device_handle, 0x1, Nanolib.OdIndex(0x60FE, 0x01), 32)
	else:
		nanolib_helper.write_number(device_handle, 0x0, Nanolib.OdIndex(0x60FE, 0x01), 32)
	time.sleep(0.2)

def start_move(nanolib_helper, device_handle):
	"""
	Initiate the move command

	:return: 1 if successful, 0 if not
	"""
	# Check brakes
	brake_status = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x60FE, 0x01)) & 0x01
	if brake_status: brake_engage(nanolib_helper, device_handle, False)

	# Start absolute move to the target position with control word (0x3F)
	nanolib_helper.write_number(device_handle, 0x3F, Nanolib.OdIndex(0x6040, 0x00), 16)

	loop_time = time.time()
	home_passes = 0

	#Definitions to help with home pulse state machine
	HOME_PULSE_LOW = 0
	HOME_PULSE_HIGH = 1
	HOME_PULSE_RETURN_LOW = 2
	start_move.home_pulse_state = HOME_PULSE_LOW
	# Monitor movement status in a loop until target position is reached	
	while(True):
		# Icrement home switch passes counter Use state machine to determine full pulse cycle [LOW -> HIGH -> LOW]
		try:				
			home_switch_state = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x60FD, 0x00)) & 0x04
			if start_move.home_pulse_state == HOME_PULSE_LOW and home_switch_state:
				start_move.home_pulse_state = HOME_PULSE_HIGH
			elif start_move.home_pulse_state == HOME_PULSE_HIGH and not home_switch_state:
				start_move.home_pulse_state = HOME_PULSE_RETURN_LOW
			elif start_move.home_pulse_state == HOME_PULSE_RETURN_LOW:
				start_move.home_pulse_state = HOME_PULSE_LOW
				home_passes += 1

		except Exception as e:
			print(f'Error getting home switch status: {e}')
			if "Invalid device handle" in str(e):  # Stop execution if the error is critical
				print("Motor error detected! Stopping function execution...")
				return 0
			
		# Read the status word to check motor state
		try:				
			status_word = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6041, 0x00))
			# Check if the motor has reached the target position using bits in status word
			if ((status_word & 0x1400) == 0x1400):
				return 1
		except Exception as e:
			print(f'Error12: {e}')
			if "Invalid device handle" in str(e):  # Stop execution if the error is critical
				print("Motor error detected! Stopping function execution...")
				return 0
		
		time.sleep(0.01)

def halt_move(nanolib_helper, device_handle, imediately = False):
	current_control_word = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6040, 0x00)) # Get current profile
	current_control_word |= 1 << CONTROLWORD_BIT_HALT # Set halt bit active 

	# Halt the move
	if imediately:
		nanolib_helper.write_number(device_handle, 0x2, Nanolib.OdIndex(0x605D, 0x00), 16)	# Halt option code [Quick Stop]
		nanolib_helper.write_number(device_handle, current_control_word, Nanolib.OdIndex(0x6040, 0x00), 16)
		brake_engage(nanolib_helper, device_handle, True)
	else:
		nanolib_helper.write_number(device_handle, 0x1, Nanolib.OdIndex(0x605D, 0x00), 16)	# Halt option code [Slow Down Ramp]
		nanolib_helper.write_number(device_handle, current_control_word, Nanolib.OdIndex(0x6040, 0x00), 16)

def move_update(nanolib_helper, device_handle, position = None, speed = None):
	if speed is not None:
		# Set the speed of the motor
		nanolib_helper.write_number(device_handle, speed, Nanolib.OdIndex(0x6081, 0x00), 32)
	
	if position is not None:
		# Set the desired target position in steps (positive or negative for direction control)
		nanolib_helper.write_number(device_handle, int(position), Nanolib.OdIndex(0x607A, 0x00), 32) # For reverse direction, use steps * (-1)

	current_control_word = nanolib_helper.read_number(device_handle, Nanolib.OdIndex(0x6040, 0x00))
	# Switch control word to Complete ongoing move - this helps to start a "new" move without stopping the current one
	nanolib_helper.write_number(device_handle, 0x0F, Nanolib.OdIndex(0x6040, 0x00), 16)
	current_control_word &= ~(1 << CONTROLWORD_BIT_POSITION_RELATIVE) # Set absolute mode	
	# Switch control word to Skip to next move - this continues the move using the new parameters
	nanolib_helper.write_number(device_handle, current_control_word, Nanolib.OdIndex(0x6040, 0x00), 16)

def set_move_homing(nanolib_helper, device_handle, offset_steps):
	# Initialize homing process and set default status to 0 (not completed)
	status = 0
	_homing_speed = speed_homing_normal

	# Set Homing offset
	nanolib_helper.write_number(device_handle, offset_steps, Nanolib.OdIndex(0x607C, 0x00), 32)
	# Set Homing method
	nanolib_helper.write_number(device_handle, 29, Nanolib.OdIndex(0x6098, 0x00), 8)
	# Set Homing Speed During Search For Switch
	nanolib_helper.write_number(device_handle, _homing_speed, Nanolib.OdIndex(0x6099, 0x01), 32)
	# Set Homing Speed During Search For Zero):
	nanolib_helper.write_number(device_handle, speed_homing_search_switch, Nanolib.OdIndex(0x6099, 0x02), 32)
	# Set Max motor speed
	nanolib_helper.write_number(device_handle, speed_steps_normal, Nanolib.OdIndex(0x6080, 0x00), 32)
	# Set Acceleration and Deceleration speed
	nanolib_helper.write_number(device_handle, 200, Nanolib.OdIndex(0x609A, 0x00), 32)
	# Set Minimum Current For Block Detection - Skipped
	# nanolib_helper.write_number(device_handle, 0x9C4, Nanolib.OdIndex(0x203A, 0x01), 32) # Default
	# Set Period Of Blocking - Skipped
	# nanolib_helper.write_number(device_handle, 0xC8, Nanolib.OdIndex(0x203A, 0x02), 32)	# Default

	# Set Digital Input special function for HOME switch
	nanolib_helper.write_number(device_handle, 4, Nanolib.OdIndex(0x3240, 0x01), 32)
	
	# Set "Homing" as the mode of operation (code 6)
	nanolib_helper.write_number(device_handle, 6, Nanolib.OdIndex(0x6060, 0x00), 8)

	# Set the device control word to switch to the "Shutdown" state
	# nanolib_helper.write_number(device_handle, 0x6, Nanolib.OdIndex(0x6040, 0x00), 16)

	# Enable motor movement by setting control word to "Quick Stop + Enable Voltage" (0x06 - From Plug&Drive)
	nanolib_helper.write_number(device_handle, 0x06, Nanolib.OdIndex(0x6040, 0x00), 16)
	# Enable motor movement by setting control word to "Switched ON" (0x07 - From Plug&Drive)
	nanolib_helper.write_number(device_handle, 0x07, Nanolib.OdIndex(0x6040, 0x00), 16)
	# Enable motor movement by setting control word to "Enable Operation" (0x0F - From Plug&Drive)
	nanolib_helper.write_number(device_handle, 0x0F, Nanolib.OdIndex(0x6040, 0x00), 16)

def disable_motor(nanolib_helper, device_handle):
	nanolib_helper.write_number(device_handle, 0x00, Nanolib.OdIndex(0x6040, 0x00), 16)

