"""
Tools for finding a particular symbol within a set of binaries
"""
import typing
import subprocess
from pathlib import Path
from .pathsHelper import PathLike,PathsLike,asPath,asPaths


class Symbol:
    """
    A single symbol within a binary
    """
    def __init__(self,dumpbinLine:str):
        self.cols=dumpbinLine.split()
        self.name=self.cols[-1].rsplit('$',1)[-1]
        self.linkageType=self.cols[4]

    @property
    def isImport(self)->bool:
        """
        Is this an imported symbol
        """
        return self.linkageType=='External'
    @property
    def isExport(self)->bool:
        """
        Is this an exported symbol
        """
        return not self.isImport()

    def __repr__(self):
        return self.name

# Global cache of files to symbols.
# Probably a bad idea to use this directly.
# Use getSymbols() instead.
SymbolsCache:typing.Dict[
    Path,
    typing.Tuple[typing.List[Symbol],typing.List[Symbol]]
    ]={}


def getSymbols(
    filename:PathLike
    )->typing.Tuple[typing.List[Symbol],typing.List[Symbol]]:
    """
    Get all of the symbols for a particular binary

    :return: [imports],[exports]
    """
    filename=asPath(filename)
    if filename not in SymbolsCache:
        imports=[]
        exports=[]
        cmd=["dumpbin","/SYMBOLS",str(filename)]
        po=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err=po.communicate()
        err=err.strip()
        if err:
            raise Exception(err.decode("utf-8",errors="ignore"))
        out=out.strip().decode("utf-8",errors="ignore")
        symbolTables=out.split('\nCOFF SYMBOL TABLE')
        if len(symbolTables)>1:
            for symbolTable in symbolTables[1:]:
                for line in symbolTable.split('\n')[1:]:
                    line=line.strip()
                    if not line:
                        break
                    symbol=Symbol(line)
                    if symbol.isImport:
                        imports.append(symbol)
                    else:
                        exports.append(symbol)
        SymbolsCache[filename]=(imports,exports)
    return SymbolsCache[filename]


def doesItExport(symbolName:str,inFilename:PathLike)->bool:
    """
    Determine if a binary file exports a given symbol
    """
    return len(doesItExportAny(symbolName,inFilename))>0


def doesItExportAny(
    symbolNames:typing.Union[str,typing.Iterable[str]],
    inFilename:PathLike)->typing.List[str]:
    """
    Determine which of a list of symbols a binary file exports
    """
    if isinstance(symbolNames,str):
        symbolNames=[symbolNames]
    exports=getSymbols(inFilename)[1]
    ret=[]
    for symbolName in symbolNames:
        if symbolName in exports:
            ret.append(symbolName)
    return ret


def whoExports(
    symbolName:str,filenames:PathsLike
    )->typing.Iterable[typing.Tuple[str,bool]]:
    """
    Determine which of a series of binary files exports a given symbol
    """
    for filename in filenames:
        yield filename,doesItExport(symbolName,filename)


def findBinaries(
    searchPaths:typing.Optional[PathsLike]=None,
    binaryExtensions:typing.Optional[typing.Iterable[str]]=None,
    recursive:bool=True
    )->typing.Generator[Path,None,None]:
    """
    Recursively find all of the binaries in given path(s)

    :searchPaths: if None, assumes the current working directory
    :binaryExtensions: if None, assumes the system StaticExportExtensions
    """
    if searchPaths is None:
        searchPaths='.'
    if binaryExtensions is None:
        from binaryFormats import StaticExportExtensions
        binaryExtensions=StaticExportExtensions
    searched=set()
    needToSearch=asPaths(searchPaths)
    for path in needToSearch:
        if path in searched:
            continue
        searched.add(path)
        for file in path.iterdir():
            if file.suffix in binaryExtensions:
                yield file
            elif recursive and file.is_dir():
                needToSearch.append(file)

def findSymbolDefinition(
    symbolName:str,
    searchPaths:typing.Optional[PathsLike]=None,
    binaryExtensions:typing.Optional[typing.Iterable[str]]=None,
    recursive:bool=True
    )->typing.Generator[Path,None,None]:
    """
    Find where a symbol is defined

    :searchPaths: if None, assumes the current working directory
    :binaryExtensions: if None, assumes the system StaticExportExtensions
    """
    for filename in findBinaries(searchPaths,binaryExtensions,recursive):
        if doesItExport(symbolName,filename):
            yield filename


def findSymbolDefinitions(
    symbolNames:typing.Iterable[str],
    searchPaths:typing.Optional[PathsLike]=None,
    binaryExtensions:typing.Optional[typing.Iterable[str]]=None,
    recursive:bool=True
    )->typing.Dict[Path,typing.List[str]]:
    """
    Find where a series of symbols are defined

    :searchPaths: if None, assumes the current working directory
    :binaryExtensions: if None, assumes the system StaticExportExtensions

    :return: {filename:[requestedSymbols]}
    """
    if isinstance(symbolNames,str):
        symbolNames=[symbolNames]
    ret={}
    for filename in findBinaries(searchPaths,binaryExtensions,recursive):
        exports=doesItExportAny(symbolNames,filename)
        if exports:
            ret[filename]=exports
    return ret


def findSymbolDefinitionsInErrorString(
    errString:str,
    searchPaths:typing.Optional[PathsLike]=None,
    binaryExtensions:typing.Optional[typing.Iterable[str]]=None,
    recursive:bool=True
    )->typing.Dict[Path,typing.List[str]]:
    """
    Find where missing symbols are defined

    :errString: error output string, eg from a linker
    :searchPaths: if None, assumes the current working directory
    :binaryExtensions: if None, assumes the system StaticExportExtensions

    :return: {filename:[requestedSymbols]}
    """
    symbolNames=set()
    for line in errString.split('\n'):
        cols=line.split('unresolved external symbol ',1)
        if len(cols)>1:
            symbolNames.add(cols[-1].split(' ',1)[0])
    return findSymbolDefinitions(
        symbolNames,searchPaths,binaryExtensions,recursive)
