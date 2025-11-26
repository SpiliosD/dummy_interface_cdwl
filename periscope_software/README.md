# software-wlp
The "Wind Lidar Positioner" is a python project for controling the position of the Wind Lidar periscope. It handles communication between the software interface [to be decided] and Nanotec N5-1-3 Motor drivers.

## Software Functionalities
- Execute movement of one or both axes to the requested position in angles.
- Home both axes to hardware home switch, with certain offset if desired.
- Print status of both axes.
- Print errors of both axes.
- Print positional information every 100ms
- Execute change of elevation or azimuth position while moving, with active correction on elevation angle.

## Software Requirements
Always keep the "system_configuration.txt" alongside the executable file, otherwise the default setting might not work well with your system.

## Commands
- GO		- Move to specified position relative to last position or to system zero
- HOME		- Home axes to hardware home switch - then go to zero for each axis (if specified beforehand)
- ZERO		- Move to local zero coordinates and set this position as HOME.
- OFFSETS	- Set zero offsets to the home switch position [elevation_offset, azimuth_offset]
- STOP		- Stop any move immediately and engage brakes
- BRAKE		- Stop move with slow down
- POSITION	- Print the current local and absolute coordinates
- STATUS	- Print status of the motor drivers
- ERROR		- Print errors of the motor drivers
- NETWORK	- Scan the network for Nanotec Motor Drivers devices
- EXIT		- Terminate program
**NOTE:** Commmands are NOT case sensitive

## Commands detailed description
### Overview of the command "GO"
Using the "GO" command (GO,x,y,z) you can move the positioner to the specified position. Using the first two arguments to request the final position of the axes and the third argument to specify if the change in position is relative to the current position or to the global zero position.
- x - azimuth angle [DEGREES]
- y - elevation angle [DEGREES]
- z - relativity [A, R, L] - Operation mode

_**GO command operation modes.**_
- A: This mode will move the axes to the requested position in absolute terms, this means the positioning will be done relative to the initial home position.
- R: This mode will move the axes to the requested position in relative terms, this means the positioning will be done relative to the current position.
- L: This mode will move the axes to the requested position in local terms, this means the positioning will be done inside the local 360° circle in relation to the system zero.

The "GO" command in _absolute mode_ can also be issued during a move, in this case the final requested position for each axis is updated. The positioner will start moving to the new position without stoping its current motion. If the requested elevational position is changed, the elevation axis will correct its local position as fast as posible. In case the requested position is to the opposite direction, the positioners will decelerate to 0 RPM and then start accelerating to the proper direction.

>**Example: Absolute Mode**		
>->Position *get current position*		
>Elevation position. Local:0.00 Absolute:00.0000		
>Azimuth position. Local:0.00 Absolute:00.0000		
>->GO,360,-90,A *move to 360 azimuthial position and -90 elevational position relative to system's zero*		
>ELEVATION Moving to: -90 °, speed: 150 RPM, relative to current position: False		
>AZIMUTH Moving to: 360 °, speed: 150 RPM, relative to current position: False		
>Local Elevation:0.00, Local Azimuth:0.00		
>Local Elevation:2.35, Local Azimuth:1.72		
>.		
>. *repeats every 100ms until the position is reached*		
>.		
>Local Elevation:-89.58, Local Azimuth:359.80		
>Local Elevation:-90.00, Local Azimuth:360.00		
>ELEVATION Position Reached		
>AZIMUTH Position Reached		

>**Example: Relative Mode**		
>->POSITION *ask current position*		
>Elevation position. Local:-0.00 Absolute:0.0000		
>Azimuth position. Local:0.00 Absolute:0.0000		
>->GO,180,-90,R *request new position*		
>ELEVATION  Moving to:  -270.0 °, Speed:  24 RPM, Relative to  current  position		
>AZIMUTH  Moving to:  180.0 °, Speed:  24 RPM, Relative to  current  position		
>Local Elevation:-0.00, Local Azimuth:0.00		
>.		
>. *repeats every 100ms until the position is reached*		
>.		
>Local Elevation:-89.93, Local Azimuth:180.00		
>AZIMUTH  Position Reached		
>ELEVATION  Position Reached	

>**Example: Local Mode**		
>POSITION		
>Elevation position. Local:-89.99 Absolute:-89.9936		
>Azimuth position. Local:359.99 Absolute:1799.9873		
>GO,90,-45,L		
>ELEVATION  Moving to:  -1935.0 °, Speed:  24 RPM, Relative to  zero  position		
>AZIMUTH  Moving to:  1890.0 °, Speed:  24 RPM, Relative to  zero  position		
>Local Elevation:-89.99, Local Azimuth:359.99		
>.		
>. *repeats every 100ms until the position is reached*			
>.		
>Local Elevation:-46.15, Local Azimuth:88.75		
>ELEVATION  Position Reached		
>.		
>Local Elevation:-45.04, Local Azimuth:89.94		
>AZIMUTH  Position Reached		

### Overview of the command "HOME"
Using the "HOME" command (HOME) you can home the positioner to the hardware home switch. This will initially move the axes to the home switch position, this is caled "homing". If prior to this move an offset of more than 0 steps is configured, the respective axis will move to this offset after homing, this is called "zeroing". When the offset position is reached the axis will set this position as the system zero.

**NOTE:** The system has default configured offsets in its configuration file.

>**Example:**		
>->HOME *request homing*		
>AZIMUTH  Homing		
>AZIMUTH  Zeroing		
>AZIMUTH  Moving to:  0 °, Speed:  200 RPM, Relative to  current  position *disregard info*		
>Local Elevation:-0.00, Local Azimuth:0.00 *disregard info*		
>Local Elevation:-0.00, Local Azimuth:0.00 *disregard info*		
>Local Elevation:-0.00, Local Azimuth:0.00 *disregard info*		
>AZIMUTH  Position Reached		
>Local Elevation:-0.00, Local Azimuth:0.00 *disregard info*		
>ELEVATION  Homing		
>ELEVATION  Zeroing		
>Axes at home		

### Overview of the command "ZERO"
With the zero command (ZERO) you can home the machine faster but with less accuracy since this mode does not use the home switch position. This will move the axes to the local zero position and set this new position as the system home position.

>**Example:**		
>->POSITION *get current position*		
>Elevation position. Local:-89.99 Absolute:-89.9936		
>Azimuth position. Local:359.99 Absolute:1799.9873		
>->ZERO *set new home position at local zero*		
>Homing to local zero...		
>ELEVATION  Moving to:  -1800.0 °, Speed:  24 RPM, Relative to  zero  position		
>AZIMUTH  Moving to:  1800.0 °, Speed:  24 RPM, Relative to  zero  position		
>Local Elevation:-89.99, Local Azimuth:359.99		
>.		
>.		
>Local Elevation:-89.99, Local Azimuth:359.99		
>AZIMUTH  Position Reached		
>Local Elevation:-89.04, Local Azimuth:359.99		
>.		
>.		
>.		
>Local Elevation:-0.15, Local Azimuth:359.99		
>ELEVATION  Position Reached		
>Local Elevation:-0.00, Local Azimuth:359.99		
>Axes at zero		

### Overview of the command "OFFSETS"
Using the "OFFSETS" command (OFFSETS,x,y) you can set the home offsets for both axes. The offsets are in steps and are relative to the home switch position.
- x - azimuth offset [STEPS]
- y - elevation offset [STEPS]

>**Example:**		
>->OFFSETS,1000,2000		
>Setting elevation home offset to: 1000		
>Setting azimuth home offset to: 2000		

### Overview of the command "STOP"
Using the "STOP" command (STOP) you can stop any move immediately and engage brakes. Take care as this command will put strain to the hardware, this means that this command should only be used in case of emergency.

>**Example:**		
>->STOP		

### Overview of the command "BRAKE"
Using the "BRAKE" command (BRAKE) you can stop a move with normal deceleration. This command will disrupt the current move and start decelerating the motors until standstill without stressing the hardware.

>**Example:**		
>->BRAKE		

### Overview of the command "STATUS"
Using the "STATUS" command (STATUS) you can print the status of the motor drivers. The response is propagated directly from the driver, and is a represantation of the status word register. If the returned status is "Fault" or "Fault reaction active", you can use the "ERROR" command to get more information.

**Posible responses:**
"Not ready to switch on"
"Ready to switch on"
"Switched on"
"Operation enabled"
"Quick stop active"
"Fault reaction active"
"Fault"
"Switch on disabled"

>**Example:**		
>->STATUS		
>Elevation axis status:  Switch on disabled		
>Azimuth axis status:  Switch on disabled		

### Overview of the command "ERROR"
Using the "ERROR" command (ERROR) you can print the error status of the motor drivers. The response is propagated directly from the driver, and is a represantation of the error word register.

**Posible responses:**
 "General error"
 "Current at the controller output too large"
 "Overvoltage/undervoltage at controller input"
 "Temperature error within the controller"
 "Interlock error: Bit 3 in 60FDh is set to `0`, the motor may not start (see the section Interlock function in the chapter Digital inputs)"
 "Software reset (watchdog)"
 "Internal software error, generic"
 "Rated current must be set (203Bh:01h/6075h)"
 "Warning: Ballast resistor thermally overloaded"
 "Motor blocked"
 "Internal error: Correction factor for reference voltage missing in the OTP"
 "Sensor 1 (see 3204h) faulty"
 "Sensor 2 (see 3204h) faulty"
 "Sensor n (see 3204h), where n is greater than 2"
 "Warning: Nonvolatile memory full or corrupt; restart the controller for cleanup work"
 "Error during fieldbus monitoring"
 "CANopen only: `Life Guard` error or `Heartbeat` error"
 "CANopen only: Slave took too long to send PDO messages."
 "CANopen only: PDO was not processed due to a length error"
 "CANopen only: PDO length exceeded"
 "CANopen only: unexpected sync length"
 "Error in speed monitoring: slippage error too large"
 "Position monitoring error: Following error too large"
 "Position monitoring error: Limit switch exceeded"
 "None"

>**Example:**		
>->ERROR		
>Elevation axis error:  None		
>Azimuth axis error:  None		

### Overview of the command "EXIT"
Using the "EXIT" command (EXIT) you can terminate the program.

>**Example:**		
>->EXIT		