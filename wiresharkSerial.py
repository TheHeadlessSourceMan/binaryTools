"""
Tools for evesdropping on serial connections using wireshark

NOTE: this will be equivilent to the wireshark filter:
   (usb.endpoint_address==0x02&&usb.endpoint_address.direction=="OUT")||
   (usb.endpoint_address==0x81&&usb.endpoint_address.direction=="IN")
"""
import typing
import time
import threading
try:
    import pyshark # type: ignore
    from pyshark.packet.packet import Packet # type: ignore
    hasPyShark=True
    def requirePyshark(): # type: ignore
        """
        Function that raises exception when pyshark is not installed
        """
except ImportError:
    hasPyShark=False
    class Packet: # type: ignore
        """ Dummy for when pyshark is not installed """
    def requirePyshark():
        """
        Function that raises exception when pyshark is not installed
        """
        raise ImportError("pyshark library is required for this funtion. Install with\n\tpip install pyshark") # noqa: E501 # pylint: disable=line-too-long
try:
    from serial import Serial # type: ignore
    hasPySerial=True
except ImportError:
    # pyserial not found. some functions may be limited
    class Serial: # type: ignore
        """
        Dummy stand-in for serial.Serial
        """
        def __init__(self,_):
            pass
    hasPySerial=False


if __name__=='__main__':
    import os
    import sys
    d=os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(d))


def captureSerial(
    timeout:float,
    data:typing.Optional[bytes]=None,
    regex:typing.Optional[typing.Pattern]=None,
    interface:str="USBPcap2"
    )->typing.Tuple[bool,pyshark.LiveCapture]: # type: ignore
    """
    Capture serial data

    returns (timeoutOccourred,capture)
    """
    capture=pyshark.LiveCapture( # type: ignore
        interface=interface,
        display_filter="ftdi-ft.if_a_rx_payload || ftdi-ft.if_a_tx_payload")
    startTime=time.time()
    capture.sniff(timeout=timeout)
    capture.close()
    packet:Packet
    for packet in capture:
        if data is not None and packet.find(data): # type: ignore
            return False,capture
        if regex is not None and regex.match(data) is not None:
            return False,capture
        if time.time()-startTime>=timeout:
            break
    return True,capture

def runAndCapture(
    serial:Serial,
    command:str,
    timeout:float,
    data:typing.Optional[bytes]=None,
    regex:typing.Optional[typing.Pattern]=None,
    interface:str="USBPcap2"
    )->typing.Tuple[bool,pyshark.LiveCapture,str]: # type: ignore
    """
    Run a serial command and capture the output

    returns (timedOut,capture,commandOutput)
    """
    if not hasPySerial:
        msg=['Cannot use runAndCapture()',
            'because pyserial is not installed',
            'install it with',
            '  pip install pyserial']
        raise ImportError('\n'.join(msg))
    functionResults={}
    def captureThreadFn():
        timedOut,capture=captureSerial(timeout,data,regex,interface)
        functionResults["timedOut"]=timedOut
        functionResults["capture"]=capture
    thread=threading.Thread(target=captureThreadFn)
    thread.start()
    try:
        serial.write(command+'\n') # type: ignore
        time.sleep(0.5)
        commandResponse=serial.read(serial.in_waiting()) # type: ignore
    except Exception as e:
        print(e)
    thread.join()
    return (
        functionResults["timedOut"], # type: ignore
        functionResults["capture"], # type: ignore
        commandResponse) # type: ignore

def example():
    """
    Example to show how runAndCapture() works
    """
    serial=Serial("COM5")
    timeout,capture,_=runAndCapture(serial,"?",10) # type: ignore
    for packet in capture:
        print(packet)
    if timeout:
        print('[timeout]')

if __name__=='__main__':
    example()
