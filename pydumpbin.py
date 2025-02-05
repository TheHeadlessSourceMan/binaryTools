"""
the idea is to use dumpbin to inspect a .lib file and list all exports for
mimicking but in practical application, it includes a whole lot that you
wouldn't want to mimick

See also:
https://learn.microsoft.com/en-us/cpp/build/reference/dumpbin-options?view=msvc-170
"""
import typing
import os
from pathlib import Path
import k_runner.osrun as osrun


def _dumpbin(filename:typing.Union[str,Path])->typing.Iterable[str]:
    """
    call the dumpbin program
    """
    if not isinstance(filename,Path):
        filename=Path(filename)
    dumpbin_exe=Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\VC\Tools\MSVC\14.16.27023\bin\Hostx64\x64\dumpbin.exe") # noqa: E501 # pylint: disable=line-too-long
    cmd=['cmd','/c',dumpbin_exe,'/ALL',filename]
    workingDirectory=filename.parent
    print(' '.join([f'"{c}"' for c in cmd]))
    print(workingDirectory)
    dumpbin=osrun.OsRun(cmd,shell=True)
    result=dumpbin()
    return result.stdouterr.split('\n')


class Obj:
    """
    Represents an object file
    """
    def __init__(self,firstLine:str):
        fl=firstLine.split(':',1)
        self.name=fl[-1].strip()
        self._parseMode=''
        self.symbols:typing.Dict[str,int]={} # {name:location}

    def addLine(self,line:str):
        """
        Add a line to the object
        """
        if self._parseMode=='':
            if line.endswith(' public symbols'):
                self._parseMode='symbols'
                #print('symbols')
            else:
                pass #print('ignore',line)
        elif self._parseMode=='symbols':
            if not line:
                self._parseMode='symbols1'
                #print('symbols1')
        elif self._parseMode=='symbols1':
            if not line:
                self._parseMode=''
                #print('done symbols')
            else:
                items=line.split()
                #print('symbol',items)
                self.symbols[items[1]]=int(items[0])
        else:
            print(f'bogus mode "{self._parseMode}"')
        # TODO: parse each line

    def __repr__(self):
        ret=[self.name]
        for k in self.symbols:
            ret.append(k)
        return '\n\t'.join(ret)


def dumpbin(filename:str)->typing.Dict[str,Obj]:
    """
    call the dumpbin utility on a file
    and get the object files that constitute it
    """
    objs={}
    objCurrent=None
    with open(filename,'r',encoding='utf-8',errors='ignore') as f:
        for line in f:
            orig=line.rstrip()
            line=orig.lstrip()
            #indent=len(orig)-len(line)
            if line.startswith("Archive member name at "):
                if objCurrent is not None:
                    objs[objCurrent.name]=objCurrent
                objCurrent=Obj(line)
            elif objCurrent is not None:
                objCurrent.addLine(line)
            else:
                pass #print(line)
    if objCurrent is not None:
        objs[objCurrent.name]=objCurrent
    for v in objs.values():
        print(v)
    return objs


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                arg[0]=arg[0].lower()
                if arg[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                print(dumpbin(arg))
    if printhelp:
        print('Usage:')
        print('  pydumpbin.py [options] [file(s)]')
        print('Options:')
        print('Example:')
        print(r'   pydumpbin.py "myfile.lib"') # noqa: E501 # pylint: disable=line-too-long
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
