"The module related to byte packing specific data into bytes"

import numpy as np

<<<<<<< HEAD
=======
def pack_angle(angle: float) -> int:
    "Convert an angle in radians into a number between 0 and 255"

    return int((angle+np.pi)/(2*np.pi) * 255)

def unpack_angle(angle: int) -> float:
    "Convert a byte angle into an angle between -pi and pi"

    return (angle/255)*(2*np.pi)-np.pi

>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
def pack_velocity(x: float, y: float) -> tuple[int, bool]:
    """
    Pack a velocity vector of 2 integers into polar coordinates. The angle is 1-byte long, while the
    length is either 0 or 1.

    This essentially transforms any vector into a unit-vector, if it's length isn't zero.
    """
    
<<<<<<< HEAD
    byte_angle = int((np.arctan2(y, x)+np.pi)/(2*np.pi) * 255)
=======
    byte_angle = pack_angle(np.arctan2(y, x))
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    bool_length = int(np.sqrt(x**2+y**2))

    return byte_angle, bool_length != 0

def unpack_velocity(vel_angle: int, vel_len: bool) -> tuple[float, float]:
    "Unpack byte-packed velocity back into a unit-vector velocity"

<<<<<<< HEAD
    vel_rad = (vel_angle/255)*(2*np.pi)
=======
    vel_rad = unpack_angle(vel_angle)
>>>>>>> 21250e21a0d3c519c569c4b7537a8cf58aa1eb75
    
    return (np.cos(vel_rad)*vel_len, np.sin(vel_rad)*vel_len)