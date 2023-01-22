import time
import logging
import ctypes
from threading import Lock

logger = logging.getLogger(__name__)


_ERRORS = {
    # FTDI and Communication errors

    # The following errors are generated from the FTDI communications module
    # or supporting code.
    0: ("FT_OK", "Success"),
    1: ("FT_InvalidHandle", "The FTDI functions have not been initialized."),
    2: ("FT_DeviceNotFound", "The Device could not be found: This can be generated if the function TLI_BuildDeviceList() has not been called."),
    3: ("FT_DeviceNotOpened", "The Device must be opened before it can be accessed. See the appropriate Open function for your device."),
    4: ("FT_IOError", "An I/O Error has occured in the FTDI chip."),
    5: ("FT_InsufficientResources", "There are Insufficient resources to run this application."),
    6: ("FT_InvalidParameter", "An invalid parameter has been supplied to the device."),
    7: ("FT_DeviceNotPresent", """The Device is no longer present. The device may have been disconnected since the last TLI_BuildDeviceList() call."""),
    8: ("FT_IncorrectDevice", "The device detected does not match that expected"),
    # The following errors are generated by the device libraries.
    16: ("FT_NoDLLLoaded", "The library for this device could not be found"),
    #     17 (0x11) FT_NoFunctionsAvailable - No functions available for this device./term>
    #     18 (0x12) FT_FunctionNotAvailable - The function is not available for this device./term>
    #     19 (0x13) FT_BadFunctionPointer - Bad function pointer detected./term>
    #     20 (0x14) FT_GenericFunctionFail - The function failed to complete succesfully./term>
    # 21 (0x15) FT_SpecificFunctionFail - The function failed to complete
    # succesfully./term>

    # General DLL control errors

    # The following errors are general errors generated by all DLLs.

    # 32 (0x20) TL_ALREADY_OPEN - Attempt to open a device that was already open.
    # 33 (0x21) TL_NO_RESPONSE - The device has stopped responding.
    # 34 (0x22) TL_NOT_IMPLEMENTED - This function has not been implemented.
    # 35 (0x23) TL_FAULT_REPORTED - The device has reported a fault.
    # 36 (0x24) TL_INVALID_OPERATION - The function could not be completed at this time.
    # 36 (0x28) TL_DISCONNECTING - The function could not be completed because the device is disconnected.
    # 41 (0x29) TL_FIRMWARE_BUG - The firmware has thrown an error
    # 42 (0x2A) TL_INITIALIZATION_FAILURE - The device has failed to initialize
    # 43 (0x2B) TL_INVALID_CHANNEL - An Invalid channel address was supplied


    # Motor specific errors
    #
    # The following errors are motor specific errors generated by the Motor DLLs.
    #
    # 37 (0x25) TL_UNHOMED - The device cannot perform this function until it has been Homed.
    # 38 (0x26) TL_INVALID_POSITION - The function cannot be performed as it would result in an illegal position.
    # 39 (0x27) TL_INVALID_VELOCITY_PARAMETER - An invalid velocity parameter was supplied
    #  The velocity must be greater than zero.
    # 44 (0x2C) TL_CANNOT_HOME_DEVICE - This device does not support Homing
    #  Check the Limit switch parameters are correct.
    # 45 (0x2D) TL_JOG_CONTINOUS_MODE - An invalid jog mode was supplied for the jog function.
    # 46 (0x2E) TL_NO_MOTOR_INFO - There is no Motor Parameters available to
    # convert Real World Units.

}

TCUBEDLL = "Thorlabs.MotionControl.TCube.DCServo.dll"
DEVICEMANAGERDLL = "Thorlabs.MotionControl.DeviceManager.dll"
TDC001_TYPE_ID = 83


def _err(retval):
    if retval == 0:
        return retval
    else:
        err_name, description = _ERRORS.get(
            retval, ("UNKNOWN", "Unknown error code."))
        raise IOError("Thorlabs Kinesis Error [{}] {}: {} ".format(
            retval, err_name, description))


class TDC001DCServoDev:

    @staticmethod
    def read_serial_numbers(kinesis_path="C:\Program Files\Thorlabs\Kinesis"):
        dll_path = kinesis_path + r"\Thorlabs.MotionControl.DeviceManager.dll"
        dll = ctypes.cdll.LoadLibrary(dll_path)
        _err(dll.TLI_BuildDeviceList())
        serialNos = ctypes.create_string_buffer(100)
        _err(dll.TLI_GetDeviceListByTypeExt(serialNos, 100, TDC001_TYPE_ID))
        return [x.decode() for x in serialNos.value.split(b',') if x]

    @staticmethod
    def pick_available_sn(target_sn=None, kinesis_path="C:\Program Files\Thorlabs\Kinesis", debug=False):
        serial_numbers = TDC001DCServoDev.read_serial_numbers(kinesis_path)
        if target_sn in serial_numbers:
            return target_sn
        elif serial_numbers:
            if debug:
                print('Warning: using first device of available!')
                print('specify serial_num from available numbers')
                print(serial_numbers)
            return serial_numbers[0]
        else:
            raise IOError(f'no TDC001 devices detected')

    def __init__(self, kinesis_path=r"C:\Program Files\Thorlabs\Kinesis", serial_num=None, debug=False):
        """
        serial_num if defined should be a string or integer
        """
        self.debug = debug
        self.serial_num = self.pick_available_sn(serial_num, kinesis_path, debug)
        self._id = self.serial_num.encode()
        self.cc_dll = ctypes.windll.LoadLibrary(kinesis_path + "\\" + TCUBEDLL)
        self.lock = Lock()
        self._status = 0
        self.open()
        self.update_status_bits()

    def open(self):
        with self.lock:
            _err(self.cc_dll.CC_Open(self._id))

    def close(self):
        with self.lock:
            _err(self.cc_dll.CC_Close(self._id))

    def serial_num_in_use(self):
        return self._id.decode()

    def stop_immediate(self):
        with self.lock:
            _err(self.cc_dll.CC_StopImmediate(self._id))

    def stop_profiled(self):
        with self.lock:
            _err(self.cc_dll.CC_StopProfiled(self._id))

    def read_position(self):
        with self.lock:
            _err(self.cc_dll.CC_RequestPosition(self._id))
            index = self.cc_dll.CC_GetPosition(self._id)
        return index

    def write_move_to_position(self, index):
        """
        Move the device to the specified position in (index). 
        Returns immediately (non-blocking)
        motor will move until position is reached, or stopped        
        """
        if self.debug:
            logger.debug(f"write_move_to_position index: {index}")
        with self.lock:
            _err(self.cc_dll.CC_MoveToPosition(self._id, index))

    def move_and_wait(self, pos, timeout=10):
        self.write_move_to_position(pos)
        t0 = time.time()
        while(self.read_position() != pos):
            time.sleep(0.1)
            if (time.time() - t0) > timeout:
                self.stop_profiled()
                raise(IOError("Failed to move"))

    def start_home(self):
        """
        Homing the device will set the device to a known state and determine the home position,
        Returns immediately (non-blocking)
        motor will home until position is reached, or stopped
        will be in position 0 when done
        """
        with self.lock:
            _err(self.cc_dll.CC_Home(self._id))

    def home_and_wait(self, timeout=100):
        self.start_home()
        t0 = time.time()
        while self.read_is_homing():
            time.sleep(0.1)
            if (time.time() - t0) > timeout:
                self.stop_profiled()
                raise(IOError("Failed to home"))

    def jog(self, direction_forward=True):
        if direction_forward:
            direc = ctypes.c_short(0x01)
        else:
            direc = ctypes.c_short(0x02)
        with self.lock:
            _err(self.cc_dll.CC_MoveJog(self._id, direc))

    def read_jog_step_size(self):
        with self.lock:
            size = self.cc_dll.CC_GetJogStepSize(self._id)
        return size

    def write_jog_step_size(self, size):
        with self.lock:
            self.cc_dll.CC_SetJogStepSize(self._id, size)

    def update_status_bits(self):
        with self.lock:
            _err(self.cc_dll.CC_RequestStatusBits(self._id))
            self._status = self.cc_dll.CC_GetStatusBits(self._id)

    def parse_status(self, status_bit):
        '''call self.updated_status_bits first'''
        #  status_bit
        #  0x00000001 CW hardware limit switch (0=No contact, 1=Contact).
        #  0x00000002 CCW hardware limit switch (0=No contact, 1=Contact).
        #  0x00000004 Not applicable.
        #  0x00000008 Not applicable.
        #  0x00000010 Motor shaft moving clockwise (1=Moving, 0=Stationary).
        #  0x00000020 Motor shaft moving counterclockwise (1=Moving, 0=Stationary).
        #  0x00000040 Shaft jogging clockwise (1=Moving, 0=Stationary).
        #  0x00000080 Shaft jogging counterclockwise (1=Moving, 0=Stationary).
        #  0x00000100 Not applicable.
        #  0x00000200 Motor homing (1=Homing, 0=Not homing).
        #  0x00000400 Motor homed (1=Homed, 0=Not homed).
        #  0x00000800 For Future Use.
        #  0x00001000 Not applicable.
        #  0x00002000
        #  ...
        #  0x00080000
        #  0x00100000 General Digital Input 1.
        #  0x00200000 General Digital Input 2.
        #  0x00400000 General Digital Input 3.
        #  0x00800000 General Digital Input 4.
        #  0x01000000 General Digital Input 5.
        #  0x02000000 General Digital Input 6.
        #  0x04000000 For Future Use.
        #  0x08000000 For Future Use.
        #  0x10000000 For Future Use.
        #  0x20000000 Active (1=Active, 0=Not active).
        #  0x40000000 For Future Use.
        #  0x80000000 Channel enabled (1=Enabled, 0=Disabled).
        return bool(self._status & status_bit)

    def is_active(self):
        return self.parse_status(0x20000000)

    def is_homed(self):
        return self.parse_status(0x00000400)

    def is_homing(self):
        return self.parse_status(0x00000200)

    def is_moving(self):
        # clockwise and anticlockwise
        return self.parse_status(0x00000010) or self.parse_status(0x00000020)


if __name__ == '__main__':
    serial_numbers = TDC001DCServoDev.read_serial_numbers()
    dev = TDC001DCServoDev(serial_numbers[0])
