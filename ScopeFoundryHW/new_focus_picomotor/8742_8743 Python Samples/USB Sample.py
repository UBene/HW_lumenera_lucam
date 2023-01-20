import sys
import os
import inspect
# Import the .NET Common Language Runtime (CLR) to allow interaction with .NET
import clr
import numpy as np

print ("Python %s\n\n" % (sys.version,))

strCurrFile = os.path.abspath (inspect.stack()[0][1])
print ("Executing File = %s\n" % strCurrFile)

# Initialize the DLL folder path to where the DLLs are located
strPathDllFolder = os.path.dirname (strCurrFile)
print ("Executing Dir  = %s\n" % strPathDllFolder)

# Add the DLL folder path to the system search path (before adding references)
sys.path.append (strPathDllFolder)

# Add a reference to each .NET assembly required
clr.AddReference ("UsbDllWrap")

# Import a class from a namespace
from Newport.USBComm import *
from System.Text import StringBuilder
from System.Collections import Hashtable
from System.Collections import IDictionaryEnumerator

# Call the class constructor to create an object
oUSB = USB (True)

# Discover all connected devices
bStatus = oUSB.OpenDevices (0, True)

if (bStatus) :
    oDeviceTable = oUSB.GetDeviceTable ()
    nDeviceCount = oDeviceTable.Count
    print ("Device Count = %d" % nDeviceCount)

    # If no devices were discovered
    if (nDeviceCount == 0) :
        print ("No discovered devices.\n")
    else :
        oEnumerator = oDeviceTable.GetEnumerator ()
        strDeviceKeyList = np.array ([])

        # Iterate through the Device Table creating a list of Device Keys
        for nIdx in range (0, nDeviceCount) :
            if (oEnumerator.MoveNext ()) :
                strDeviceKeyList = np.append (strDeviceKeyList, oEnumerator.Key)

        print ('strDeviceKeyList', strDeviceKeyList)
        print ("\n")

        strBldr = StringBuilder(64)
        print('strBldr', repr(strBldr.ToString()), strBldr.Length)

        # Iterate through the list of Device Keys and query each device with *IDN?
        for oDeviceKey in strDeviceKeyList :
            strDeviceKey = str (oDeviceKey)
            print(strDeviceKey)
            # strBldr.Remove(0, strBldr.Length)
            strBldr = StringBuilder(64)

            print('strBldr', repr(strBldr.ToString()), strBldr.Length)
            nReturn = oUSB.Query (strDeviceKey, "*IDN?", strBldr)
            print('strBldr', repr(strBldr.ToString()), strBldr.Length)
            strBldr.Remove(0, strBldr.Length)
            print('strBldr', repr(strBldr.ToString()), strBldr.Length)

            print ("Return Status = %d" % nReturn)
            print ("*IDN Response = %s\n" % strBldr.ToString ())
            
            strBldr = StringBuilder(64)
            print(oUSB.Query(strDeviceKey, "1TP?", strBldr))
            print('strBldr', "1TP?", repr(strBldr.ToString()), strBldr.Length)

            strBldr.Remove(0, strBldr.Length)
            print(oUSB.Query(strDeviceKey, "2TP?", strBldr))
            strBldr.Remove(0, strBldr.Length)
            print(oUSB.Query(strDeviceKey, "3TP?", strBldr))
            strBldr.Remove(0, strBldr.Length)
            print(oUSB.Query(strDeviceKey, "4TP?", strBldr))
else :
    print ("\n***** Error:  Could not open the devices. *****\n\nCheck the log file for details.\n")

# Shut down all communication





oUSB.CloseDevices ()



print ("Devices Closed.\n")
