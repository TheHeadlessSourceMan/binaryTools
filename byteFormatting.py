"""
Tools for formatting bytes as strings
"""
import typing
import re


def str2Bytes(s:typing.Union[bytes,bytearray,str]):
    r"""
    Attempt to transform a string bytes
    representation into a bytes value

    This will attempt to decode things like:
        "0x410DFF..." # most typical useage
        "0x41 0x0D 0xFF ..." # ignores whitespace
        "0x41,0x0D,0xFF,..." # ignores commas
        "410dff..." # always assumes hex (not decimal)
        "b'A\r\xFF'" # python bytes dump
        "0b10001000" # binary numbers
        "0o777" # octal numbers
        NOTE: does not support decimal numbers
            (because, "how big is it?")

    NOTE: If you want to turn a string's characters themselves
    into bytes, use s.encode(encoding) instead

    NOTE: If a bytes value is passed in, this first
    converts it to a string, then decodes.
    (Useful when reading binary files)
    """
    if isinstance(s,(bytes,bytearray)):
        s=s.decode('utf-8',errors='ignore')
    s=s.replace(',','').replace(' ','').replace('\t','')\
        .replace('\r','').replace('\n','')
    if s.startswith("b'"): # python b strings
        # mitigate against injection attacks
        s="b'"+s.split("'",2)[1]+"'"
        # use the interpreter to decode it
        b=eval(s) # pylint: disable=eval-used
    elif s.startswith('0b'): # binary
        s=s.replace('0b','')
        s=s[2:]
        while len(s)%8!=0:
            s='0'+s
        b=bytes(int(s[i:i+8],2) for i in range(0,len(s),8))
    elif s.startswith('0o'): # octal
        s=s.replace('0o','')
        while len(s)%3!=0:
            s='0'+s
        b=bytes(int(s[i:i+3],8) for i in range(0,len(s),3))
    else: # hex
        s=s.replace('0x','')
        if len(s)%2!=0:
            s='0'+s
        b=bytes(int(s[i:i+2],16) for i in range(0,len(s),2))
    return b

def undoByteText(
    s:typing.Union[str,bytes,bytearray,typing.Iterable[str]],
    sep:typing.Union[None,str,typing.Iterable[str]]=None,
    startColumn:int=0,
    endColumn:typing.Optional[int]=None,
    )->bytes:
    """
    Attempt to do the opposite of byteText, that is,
    decode an ascii byte table to a series of bytes

    :s: string to decode (if it's a bytes, convert it to string,
        then decode - useful when reading binary files)
        Can also pass in a list of data lines.
    :sep: what separates columns (default is [' ','\t',','])
    :startColumn: column where data starts
        useful for chopping off a line numbers column
    :endColumn: column where data ends
        (can be negative like array slices)
        useful if there is an ascii column at the end,
        you can use this to chop it off

    NOTE: If there may be colors in this, you might want to
    do ansiUndoColorize() first
    """
    if sep is None:
        sep=(' ','\t',',')
    sep=[re.escape(s) for s in sep]
    regex=re.compile("("+(")|(".join(sep))+")")
    if isinstance(s,(bytes,bytearray)):
        s=s.decode('utf-8',errors='ignore')
    if isinstance(s,str):
        s=s.strip().split('\n')
    b=bytearray()
    for line in s:
        line=line.strip()
        if not line:
            continue
        columns=regex.split(line)
        if endColumn is not None:
            ss=columns[startColumn:endColumn]
        else:
            ss=columns[startColumn:]
        b.extend(str2Bytes(''.join(ss)))
    return bytes(b)

def byteText(
    data:bytes,
    lineLength:typing.Optional[int]=32,
    lineNumberIsByteOffset:bool=True,
    lineNumberStartAt:int=0,
    lineNumberWidth:int=4,
    lineNumberWidthAutoextend:bool=True,
    sep:str=' ',
    lineSep:str='\n',
    )->typing.Iterable[str]:
    """
    Print a hunk of bytes as text in a variety of ways

    :data: data to print
    :lineLength: how many bytes per line
    :lineNumberIsByteOffset: instead of a line number
        show hex offset of the start of the line
    :lineNumberStartAt: whether to start at 0 or 1
    :lineNumberWidth: how wide the line numbers are padded to
        set to 0 to disable
    :lineNumberWidthAutoextend: if there is a line number wider than
        lineNumberWidth, increase all lineNumberWidth to that
    :sep: separator between bytes
    :lineSep: separator between lines
    """
    ret=['%02X%s'%(b,sep) for b in data]
    if lineLength is not None:
        lines=[]
        for lineIdx in range(0,len(ret),lineLength):
            lines.append(''.join(ret[lineIdx:lineIdx+lineLength]))
        if lineNumberWidth>=0:
            if lineNumberWidthAutoextend:
                x=len(str(len(lines)+lineNumberStartAt))
                if x>lineNumberWidth:
                    lineNumberWidth=x
            for i,line in enumerate(lines):
                if lineNumberIsByteOffset:
                    lines[i]=f"%0{lineNumberWidth}X%s%s"%(
                        (i+lineNumberStartAt)*lineLength,sep,line)
                else:
                    lines[i]=f"%0{lineNumberWidth}d%s%s"%(
                        i+lineNumberStartAt,sep,line)
        return lineSep.join(lines)
    return ret

def loadBin(filename:str)->bytes:
    """
    Shorcut to load a binary file as bytes
    """
    with open(filename,"rb") as f:
        return f.read()

def ansiUndoColorize(s:str)->str:
    """
    Remove ansi color strings
    """
    regex=re.compile(r'\033\[[0-9;]{1,6}m')
    return ''.join(regex.split(s))


def ansiColorize(s:typing.Union[str,typing.Iterable[str]],
    rules:typing.Iterable[typing.Tuple[
        typing.Union[str,typing.Pattern],
        typing.Union[int,str]]]):
    """
    :rules: map text to ansi escape code color
        the text can either be plain text or a compiled regex
        the mapping can either be a foreground or background color number
        or a full-fledged escape code
    NOTE: Rules are evaluated in-order, so if things don't look like you
        intend, it's probably an order issue
    SEE ALSO:
        https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    """
    if not isinstance(s,str):
        s='\n'.join(s)
    colorReset='\033[0m'
    for k,v in rules:
        if isinstance(v,int):
            if v>=40: # background color
                v=f'\033[90;{v}m'
            else: # foreground color
                v=f'\033[{v}m'
        if isinstance(k,str):
            replacement=f'{v}{k}{colorReset}'
            s=s.replace(k,replacement)
        else:
            replacement=f'{v}\\g<0>{colorReset}'
            s=k.sub(replacement,s)
    return s

def example():
    """
    Example to show what this library can do
    """
    data=loadBin("bytes.bin")
    print(
        ansiColorize(
            byteText(data,lineLength=66),
            {"AA":95,"FF":105,re.compile(r"^[^\s]*",re.MULTILINE):46}
        )
        )

if __name__=='__main__':
    example()
