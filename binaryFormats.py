"""
Tools for converting between binary format types
"""
#import typing
import os
import subprocess
from .dataBlocks import DataBlock,DataBlocks


WindowsExecutableExtension='.exe'
WindowsDynamicLibraryExtension='.dll'
WindowsStaticLibraryExtension='.lib'
WindowsObjectFileExtension='.obj'
WindowsStaticExportExtensions=[
    WindowsStaticLibraryExtension,
    WindowsObjectFileExtension]
WindowsBinaryExtensions=[
    WindowsExecutableExtension,
    WindowsDynamicLibraryExtension,
    WindowsStaticLibraryExtension,
    WindowsObjectFileExtension]

LinuxExecutableExtension=''
LinuxDynamicLibraryExtension='.ld'
LinuxStaticLibraryExtension='.a'
LinuxObjectFileExtension='.o'
LinuxStaticExportExtensions=[
    LinuxStaticLibraryExtension,
    LinuxObjectFileExtension]
LinuxBinaryExtensions=[
    LinuxDynamicLibraryExtension,
    LinuxStaticLibraryExtension,
    LinuxObjectFileExtension]

if os.name=='nt':
    CurrentOsExecutableExtension=WindowsExecutableExtension
    CurrentOsDynamicLibraryExtension=WindowsDynamicLibraryExtension
    CurrentOsStaticLibraryExtension=WindowsStaticLibraryExtension
    CurrentOsObjectFileExtension=WindowsObjectFileExtension
    CurrentOsStaticExportExtensions=WindowsStaticExportExtensions
    CurrentOsBinaryExtensions=WindowsBinaryExtensions
else:
    CurrentOsExecutableExtension=LinuxExecutableExtension
    CurrentOsDynamicLibraryExtension=LinuxDynamicLibraryExtension
    CurrentOsStaticLibraryExtension=LinuxStaticLibraryExtension
    CurrentOsObjectFileExtension=LinuxObjectFileExtension
    CurrentOsStaticExportExtensions=LinuxStaticExportExtensions
    CurrentOsBinaryExtensions=LinuxBinaryExtensions
CurrentExecutableExtension=CurrentOsExecutableExtension
CurrentDynamicLibraryExtension=CurrentOsDynamicLibraryExtension
CurrentStaticLibraryExtension=CurrentOsStaticLibraryExtension
CurrentObjectFileExtension=CurrentOsObjectFileExtension
CurrentStaticExportExtensions=CurrentOsStaticExportExtensions
CurrentBinaryExtensions=CurrentOsBinaryExtensions
ExecutableExtension=CurrentExecutableExtension
DynamicLibraryExtension=CurrentDynamicLibraryExtension
StaticLibraryExtension=CurrentStaticLibraryExtension
ObjectFileExtension=CurrentObjectFileExtension
StaticExportExtensions=CurrentStaticExportExtensions
BinaryExtensions=CurrentBinaryExtensions


def elfFileToIhexFile(filename:str)->str:
    """
    Convert a .elf file into a .hex file

    (requires the "objcopy" utility from gnu tools)
    """
    ihexFilename=filename.rsplit('.',1)[0]+'.hex'
    if not os.path.exists(ihexFilename) \
        or os.path.getmtime(filename)>os.path.getmtime(ihexFilename):
        # (re)generate the ihexFilename file
        cmd=['objcopy','-S','-O','ihex',filename,ihexFilename]
        po=subprocess.Popen(cmd,shell=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        _,err=po.communicate()
        errStr=err.decode('utf-8',errors='ignore').strip()
        if errStr:
            raise TypeError('Error converting .elf to .hex: '+errStr)
    return ihexFilename


def looksLikeIhex(data:bytes)->bool:
    """
    determine if the data looks like intel hex format
    """
    if len(data)>=10:
        asc=data[0:10].decode('ascii')
        if asc[0]==':':
            import re
            exp=r':[0-9A-Fa-f]{2}\s+[[0-9A-Fa-f]{4,99}'
            if re.match(exp,asc) is not None:
                return True
    return False


def looksLikeElf(data:bytes)->bool:
    """
    determine if the data looks like elf format
    """
    if len(data)>=4:
        asc=data[1:4].decode('ascii')
        return asc==b'ELF'
    return False


def loadIhex(filename:str)->DataBlocks:
    """
    Load an intel .hex file
    """
    extn=filename.rsplit('.',1)[-1].lower()
    if extn=='elf':
        filename=elfFileToIhexFile(filename)
    try:
        import intelhex # type: ignore
    except ImportError as e:
        print('intelhex library (for .hex format) was not found.  Try:')
        print('    pip install intelhex')
        raise e
    ret=DataBlocks()
    ihex=intelhex.IntelHex(filename)
    for start,stop in ihex.segments():
        data=bytes(ihex.tobinarray(start,stop))
        ret.append(DataBlock(start,data)) # type: ignore
    return ret


# since it supports elf files, let's be lazy
loadElf=loadIhex

if __name__=='__main__':
    # whatever they give us, dump it
    import sys
    print(loadIhex(sys.argv[1]))
