"""
Tools for managing strings containing hex data
"""
import typing
import re


def iterbytes(
    data:typing.Union[bytes,bytearray],
    startPos:int=0,endPos:int=-1,
    chunkSize:int=1
    )->typing.Generator[int,None,None]:
    """
    Utility to iterate over bytes in an array.
    """
    if not isinstance(data,bytearray):
        data=bytearray(data)
    datalen=len(data)
    if startPos<0:
        startPos+=datalen
    if endPos<0:
        endPos+=datalen
    if endPos<0 or endPos>=datalen or startPos<0 or startPos>=datalen:
        raise IndexError('Data index [{startPos}:{endPos}] out of range [0:{datalen}]') # noqa: E501 # pylint: disable=line-too-long
    if (endPos-startPos)%chunkSize!=0:
        raise IndexError('Data index [{startPos}:{endPos}] is not an even multiple of chunkSize {chunkSize}') # noqa: E501 # pylint: disable=line-too-long
    for idx in range(startPos,endPos,chunkSize):
        ret=0
        for i in range(idx,idx+chunkSize):
            ret=(ret<<1)|data[i]
        yield ret


def hexTable(data:bytes,
    startPos:int=0,endPos:int=-0,
    valBytes:int=1,valFmt=r'%02X',
    positionFmt:typing.Optional[str]=r'%08',
    printAscii=True,
    asciiBumpers='|',
    valsPerLine:int=16,
    colSep=' ',
    asciiUnprintableChar:int=0x32
    )->str:
    """
    Get a hex table capable of user-viewing
    """
    ret:typing.List[str]=[]
    rowVals:typing.List[int]=[]
    row:typing.List[str]=[]
    for i,b in enumerate(iterbytes(data,startPos,endPos,valBytes)):
        if i%valsPerLine==0:
            if row:
                if printAscii:
                    asc=bytes([(c if (c>=0x20 and c!=0x7f) else asciiUnprintableChar) for c in rowVals]).decode('ascii',errors="ignore") # noqa: E501 # pylint: disable=line-too-long
                    row.append(asciiBumpers+asc+asciiBumpers)
                ret.append(colSep.join(row))
                row=[]
                rowVals=[]
            if positionFmt is not None and positionFmt:
                row.append(positionFmt%i*valBytes)
        rowVals.append(b)
        row.append(valFmt%b)
    if row:
        if printAscii:
            asc=bytes(rowVals).decode('ascii',errors="ignore")
            row.append(asciiBumpers+asc+asciiBumpers)
        ret.append(colSep.join(row))
    return '\n'.join(ret)


HEXTABLE_RE_TEXT=r"""(((?P<val>[0-9a-f]+)\s+){2}(?P<asc>[^\r\n$]*)\r*(\n|$))+""" # noqa: E501 # pylint: disable=line-too-long
HEXTABLE_RE=re.compile(HEXTABLE_RE_TEXT,re.IGNORECASE)
def findHexTable(s:str)->typing.Optional[str]:
    """
    Find a hex table in a block of text.

    Normally you don't need to call this as
    decodeHexTable calls it automatically.
    """
    for m in HEXTABLE_RE.finditer(s):
        return m.group(0)
    return None


def decodeHexTable(s:str)->typing.Optional[typing.Any]:
    """
    Decode an arbitray hex table into bytes
    """
    # find a hex table in the input
    hextableStr=findHexTable(s)
    if hextableStr is None:
        return hextableStr
    rows:typing.List[typing.List[str]]=[]
    colIntBases:typing.List[int]=[10]
    # parse the string into a table of strings
    # (not decoded to numbers yet since we don't know what's hex)
    for line in hextableStr.split('\n'):
        cols:typing.List[str]=[]
        col:typing.List[str]=[]
        colIdx=0
        scanningCol=False
        for c in line.lower():
            if c.isdigit():
                scanningCol=True
                if col or c!='0': # ignore leading zeroes
                    col.append(c)
            elif c.isalpha() and c in ('a','b','c','d','e','f','x'):
                scanningCol=True
                colIntBases[colIdx]=16
                if c!='x': # as in 0xff
                    col.append(c)
            elif c==' ':
                if scanningCol:
                    scanningCol=False
                    if not col:
                        cols.append('0')
                    else:
                        cols.append(''.join(col))
                    colIdx+=1
                    if len(colIntBases)<=colIdx:
                        colIntBases.append(10)
                    col=[]
            else:
                break
        if cols:
            rows.append(cols)
    # decode all values
    # lastBase ensures that all columns to the right of a hex column are hex
    valueTable:typing.List[typing.List[int]]=[]
    firstColIsCount=True
    firstRow=True
    bytecount=0 # not counting the first column of each row
    for row in rows:
        valueRow:typing.List[int]=[]
        lastBase=10
        firstCol=True
        for intBase,strVal in zip(colIntBases,row):
            if intBase>lastBase:
                lastBase=intBase
            val=int(strVal,base=lastBase)
            valueRow.append(val)
            if firstCol:
                firstCol=False
                if firstColIsCount:
                    # try to disprove
                    if firstRow:
                        firstColIsCount=val==0
                    elif val!=bytecount:
                        firstColIsCount=False
            else:
                bytecount+=1
        valueTable.append(valueRow)
        firstRow=False
    # decode to bytes
    ret:typing.List[int]=[]
    for valueRow in valueTable:
        firstCol=True
        for value in valueRow:
            if firstCol:
                firstCol=False
                if not firstColIsCount:
                    ret.append(value)
            else:
                ret.append(value)
    return bytes(ret)


def test_rount_trip():
    """
    Test that encoding data to a table, then decoding it,
    results in the original data
    """
    data="rtklerj tlkjertelkj\nertkl jerlktjelkrtjelrktjklertjlkerjtklejrtlkejrtklerjtklerjtklerjtlkejrtlekrjt".encode('ascii') # noqa: E501 # pylint: disable=line-too-long
    startPos=1
    endPos=-1

    tbl=hexTable(
        data=data,
        startPos=startPos,
        endPos=endPos,
        valBytes=1,
        valFmt=r'%02x',
        positionFmt=r'%04d',
        printAscii=True,
        asciiBumpers='|',
        valsPerLine=16,
        colSep=' ',
        asciiUnprintableChar='~'.encode('ascii')[0]
        )
    tbl=f'This is a hex table:\n\n{tbl}\n210 bytes total'
    print('---')
    decoded=decodeHexTable(tbl)
    print(data[startPos:endPos])
    print(decoded)
    print(decoded==data[startPos:endPos])

if __name__=='__main__':
    test_rount_trip()
