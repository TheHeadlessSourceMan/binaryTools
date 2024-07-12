"""
Tools for working with wireshark captures.

requires the pyshark library
"""
import typing
import pyshark # type: ignore
from pyshark.packet.packet import Packet # type: ignore

def saveCapture(
    capture:pyshark.LiveCapture,
    filename:str):
    """
    Save a capture to file
    """
    with pyshark.FileCapture(output_file=filename) as file:
        for packet in capture:
            # TODO: figure this out
            file.write(packet)

def loadCapture(
    filename:str
    )->typing.Iterable[Packet]:
    """
    Load a serial capture
    """
    packet:Packet
    packets:typing.List[Packet]=[]
    with pyshark.FileCapture(filename) as file:
        for packet in file:
            if not hasattr(packet,"usb"):# or not hasattr(packet,"DATA"):
                continue
            if not packet.usb.transfer_type=='0x03':
                continue
            packets.append(packet)
    if len(packets)<=0:
        print(f'WARN: no USB data packets found in "{filename}"')
    return packets

def extractPacketData(
    packets:typing.Iterable[Packet],
    includeDataIn:bool=True,
    includeDataOut:bool=True
    )->typing.Iterable[typing.Tuple[bool,bytes]]:
    """
    Goes through all packets and extracts raw data

    TODO: this currently only works with USB captures.
        need to expand it for regular network captures.

    Returns:
        typing.Iterable[typing.Tuple[bool,bytes]]: like [(dataIn,data)]
    """
    ret=[]
    currentBytes=bytearray()
    currentDirectionIn=True
    endpointDirectionMask=0b10000000
    for packet in packets:
        if not hasattr(packet,"ftdi-ft") \
            or not hasattr(packet,"usb"):
            continue
        endpoint=int(packet.usb.endpoint_address,base=16)
        if endpoint&endpointDirectionMask==endpointDirectionMask:
            directionIn=True
            if not includeDataIn:
                continue
        else:
            directionIn=False
            if not includeDataOut:
                continue
        ftdi=getattr(packet,"ftdi-ft")
        if hasattr(ftdi,"if_a_rx_payload"):
            data=ftdi.if_a_rx_payload
        elif hasattr(ftdi,"if_a_tx_payload"):
            data=ftdi.if_a_tx_payload
        else:
            continue
        if currentDirectionIn!=directionIn:
            # data direction change
            if currentBytes:
                ret.append((currentDirectionIn,bytes(currentBytes)))
                currentBytes.clear()
            currentDirectionIn=directionIn
        for byte in data.split(':'):
            currentBytes.append(int(byte,base=16))
    if currentBytes:
        ret.append((currentDirectionIn,bytes(currentBytes)))
    return ret

def getOutputData(
    source:typing.Union[
        typing.Iterable[Packet],
        typing.Iterable[typing.Tuple[bool,bytes]],
        ]
    )->bytes:
    """
    Get a single set of bytes containing all output data joined together
    """
    ret=bytearray()
    for testThing in source:
        if isinstance(testThing,Packet):
            source=extractPacketData(source,includeDataIn=False)
        break
    for isInput,data in source:
        if not isInput:
            ret.extend(data)
    return bytes(ret)

def getInputData(
    source:typing.Union[
        typing.Iterable[Packet],
        typing.Iterable[typing.Tuple[bool,bytes]],
        ]
    )->bytes:
    """
    Get a single set of bytes containing all output data joined together
    """
    ret=bytearray()
    for testThing in source:
        if isinstance(testThing,Packet):
            source=extractPacketData(source,includeDataOut=False)
        break
    for isInput,data in source:
        if isInput:
            ret.extend(data)
    return bytes(ret)

def printPacketDataBytes(
    packets:typing.Iterable[Packet],
    lineLength:int=32+2):
    """
    print the packet data as bytes
    """
    import re
    from byteFormatting import ansiColorize,byteText
    for directionIn,data in extractPacketData(packets):
        if directionIn:
            print(f"\nPC << DEVICE ({len(data)})")
        else:
            print(f"\nPC >> DEVICE ({len(data)})")
        print(
            ansiColorize(
                byteText(data,lineLength=lineLength,lineNumberStartAt=0xFF),
                (
                    (re.compile(r"^[^\s]{4}",re.MULTILINE),46),
                    ("AA",95),
                    ("FF",105)
                )
            )
            )

def example():
    """
    Example to show how reading a .pcap file works
    """
    filename=r"capture.pcapng"
    packets=loadCapture(filename)
    #printPacketDataBytes(packets,lineLength=512)
    import re
    from byteFormatting import ansiColorize,byteText
    data=getInputData(packets)
    for sample in data.split(b'\xff'):
        print(
            ansiColorize(
                byteText(
                    sample,
                    lineLength=9999,
                    lineNumberWidth=0,
                    ),
                (
                    (re.compile(r"^[^\s]{4}",re.MULTILINE),46),
                    ("AA",95),
                    ("FF",105)
                )
            )
            )
        print()

if __name__=='__main__':
    example()
