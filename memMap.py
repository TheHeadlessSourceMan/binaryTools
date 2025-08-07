"""
Read a .map file

Primary purpose is to determine
the location of global symbols
"""
import sys
import typing
import re


class MapEntry:
    """
    An entry within a memory map
    """

    def __init__(self,
        memoryMap:"MemoryMap",
        section:str,
        module:typing.Optional["MapEntry"],
        entryType:str,
        name:str,
        address:int,
        size:int=-1,
        end=-1,
        access:str='rwx'):
        """ """
        self.memoryMap=memoryMap
        self.module=module
        self.section=section
        self.entryType=entryType
        self.name=name
        if size<0 and end>=0:
            size=end-address
        self.size=size
        self.address=address
        self.access=access

    @property
    def memory(self)->"MapEntry":
        """
        Get the memory where this item resides
        """
        result=self.memoryMap.getMemoryAt(self.start)
        if result is None:
            raise IndexError(f'{self.name} not found in memory')
        return result

    @property
    def sizePercent(self):
        """
        What percent is this size of the overall memory
        """
        if self.size<=0:
            return 0
        total=self.memory.size
        if total<=0:
            return 1.0
        return self.size/total

    @property
    def start(self):
        """
        Start location of value
        """
        return self.address
    @start.setter
    def start(self,start:int):
        self.address=start
    @property
    def location(self):
        """
        Start location of value
        """
        return self.address
    @location.setter
    def location(self,location:int):
        self.address=location
    @property
    def end(self):
        """
        End location of value
        """
        return self.address+self.size
    @end.setter
    def end(self,end:int):
        self.size=end-self.start

    def __repr__(self):
        sizeStr="N/A"
        if self.start>=0:
            if self.end>=0:
                sizeStr='0x%08X .. 0x%08X'%(self.start,self.end)
            else:
                sizeStr='0x%08X'%self.start
        return f"({self.entryType}){self.name}\t\t\t{sizeStr}"


class MemoryMap:
    """
    Read a .map file

    Primary purpose is to determine
    the location of global symbols
    """
    def __init__(self,filename:str):
        self.entries:typing.List[MapEntry]=[]
        self.load(filename)

    def load(self,filename:str):
        """
        Load a .mem file
        """
        with open(filename,"r",encoding="utf-8",errors="ignore") as f:
            data=f.read().replace('\r','')
            sections=data\
                .split("Memory Configuration",1)[-1]\
                .split("Linker script and memory map",1)
            # read the memory configuration
            regex=re.compile(r'\s*(?P<Name>[^\s*]+)\s+(?P<Origin>[^\s]+)\s+(?P<Length>[^\s]+)\s+(?P<Attributes>[^\s]+)') # noqa:E501 # pylint: disable=line-too-long
            for line in sections[0].split("Attributes",1)[-1].strip().split('\n'): # noqa:E501 # pylint: disable=line-too-long
                m=regex.match(line)
                if m:
                    self.entries.append(MapEntry(self,
                        section="",
                        module=None,
                        entryType="Memory",
                        name=m.group("Name"),
                        address=int(m.group("Origin"),base=16),
                        size=int(m.group("Length"),base=16),
                        end=-1,
                        access=m.group("Attributes")))
            # read the map
            regex=re.compile(r'\s*(?P<SectionName>[._()a-zA-Z]*)\s*(?P<Address>0x[0-9a-zA-Z]{8,})\s*(?P<Size>0x[0-9a-zA-Z]+)?\s*(?P<Name>.+)') # noqa:E501 # pylint: disable=line-too-long
            currentModule=None
            lastItem=None
            okSection=False
            for line in sections[1].strip().split('\n\n',1)[-1].split('\n'):
                if not line:
                    continue
                if line[0]=='.':
                    currentModule=None
                    lastItem=None
                    section=line.split(maxsplit=1)[0]
                    okSection=section in (
                        '.bss','.tbss','data','.tdata',
                        '.data1','.rodata','.txt','.txt.memcpy')
                    continue
                if not okSection:
                    continue
                m=regex.match(line)
                if m:
                    section=''
                    if m.group('SectionName') is not None and m.group('SectionName'): # noqa:E501 # pylint: disable=line-too-long
                        # it's a new module
                        if m.group("Size") is None or not m.group("Size"):
                            size=-1
                        else:
                            size=int(m.group("Size"),base=16)
                        newItem=MapEntry(self,
                            section=m.group("SectionName"),
                            module=None,
                            entryType="Module",
                            name=m.group("Name"),
                            address=int(m.group("Address"),base=16),
                            size=size,
                            end=-1,
                            access="rwx")
                        self.entries.append(newItem)
                        currentModule=newItem
                        lastItem=None
                        continue
                    end=-1
                    access='rwx'
                    if currentModule is not None:
                        end=currentModule.end
                        access=currentModule.access
                    newItem=MapEntry(self,
                        section=section,
                        module=currentModule,
                        entryType="Global",
                        name=m.group("Name"),
                        address=int(m.group("Address"),base=16),
                        size=-1,
                        end=end,
                        access=access)
                    self.entries.append(newItem)
                    if lastItem is not None:
                        # update the length of the last item
                        lastItem.end=newItem.start-1
                    lastItem=newItem

    @property
    def html(self)->str:
        """
        Get an html file for visualizing this memory
        """
        if '.' not in sys.path:
            sys.path.append('.')
        from memMapUI import memMapToHtml # type: ignore # pylint: disable=import-error
        return memMapToHtml(self)

    @property
    def htmlElements(self)->str:
        """
        Get an html element for visualizing this memory

        NOTE: you will also have to include MemoryMapVisualizationCSS
        in whatever html file you create with this.
        """
        if '.' not in sys.path:
            sys.path.append('.')
        from memMapUI import memMapToHtmlElements # noqa:E501 # type: ignore # pylint: disable=import-error
        return memMapToHtmlElements(self)

    def getEntriesByType(self,
        memoryType:str
        )->typing.Generator[MapEntry,None,None]:
        """
        Yield all map entries of a given type
        """
        for entry in self.entries:
            if entry.entryType==memoryType:
                yield entry

    @property
    def modules(self)->typing.Generator[MapEntry,None,None]:
        """
        Yield all modules
        """
        yield from self.getEntriesByType('Module')

    @property
    def memory(self)->typing.Generator[MapEntry,None,None]:
        """
        Yield all memory device blocks
        """
        yield from self.getEntriesByType('Memory')

    def getMemoryAt(self,location:int)->typing.Optional[MapEntry]:
        """
        Get the memory block at a given memory location
        """
        for g in self.memory:
            if location>=g.start and location<=g.end:
                return g
        return None

    @property
    def globals(self)->typing.Generator[MapEntry,None,None]:
        """
        Yield all global values
        """
        yield from self.getEntriesByType('Global')

    def getGlobalAt(self,location:int)->typing.Optional[MapEntry]:
        """
        Get the global at a given memory location
        """
        for g in self.globals:
            if location>=g.start and location<=g.end:
                return g
        return None
    getGlobalStartingAt=getGlobalAt

    def getGlobalEndingAt(self,location:int)->typing.Optional[MapEntry]:
        """
        Get the global ending at a given memory location
        """
        for g in self.globals:
            if g.end==location:
                return g
        return None

    def getGlobal(self,name:typing.Union[str,typing.Pattern])->MapEntry:
        """
        Get a global of a given name
        """
        if isinstance(name,str):
            for g in self.globals:
                if g.name==name:
                    return g
        else:
            for g in self.globals:
                if name.match(g.name):
                    return g
        raise Exception(f'Value "{name}" not found')

    def getAdjacentGlobals(self,
        globalName:str,
        distance=1
        )->typing.Iterable[MapEntry]:
        """
        Get the globals that are adjacent to the given global

        :distance: how far away from the given value to search

        (can aid in diagnosing memory overwrites)
        """
        ret=[]
        g=self.getGlobal(globalName)
        start=g.start
        end=g.end
        for _ in range(distance):
            s=self.getGlobalEndingAt(start)
            if s is not None:
                ret.append(s)
                start=s.start
            e=self.getGlobalStartingAt(end)
            if e is not None:
                ret.append(e)
                end=e.end
        return ret

    @property
    def statsStr(self)->str:
        """
        get a stats str
        """
        ret=[]
        totalSize=0
        totalPercent=0.0
        for m in self.modules:
            size=m.size
            totalSize+=size
            percent=round(m.sizePercent*100.0,1)
            totalPercent+=percent
            ret.append(f'{m.name} {size} ({percent}%)')
        ret.append('---------')
        ret.append(f'TOTAL: {totalSize} ({totalPercent}%)')
        return '\n'.join(ret)

    def differences(self,other:"MemoryMap"
        )->typing.Iterable[typing.Tuple[
            str,
            typing.Optional[MapEntry],
            typing.Optional[MapEntry]
            ]]:
        """
        Get all differences between this, and another, memory map
        """
        globals1:typing.Dict[str,MapEntry]={}
        for g1 in self.globals:
            globals1[g1.name]=g1
        for g2 in other.globals:
            if g2.name not in globals1:
                yield ("Only right",None,g2)
            else:
                g1=globals1[g2.name]
                if g1.address!=g2.address:
                    yield ("Location different",g1,g2)
                if g1.size!=g2.size:
                    yield ("Size different",g1,g2)
                del globals1[g2.name]
        for g1 in globals1.values():
            yield ("Only left",g1,None)

    def differencesStr(self,other:"MemoryMap"
        )->str:
        """
        Differences between two memory maps as a string
        """
        ret=['Differences:']
        for diff,g1,g2 in self.differences(other):
            if diff.startswith("Only"):
                if g1 is not None:
                    ret.append(f" {g1.name} {diff}")
                elif g2 is not None:
                    ret.append(f" {g2.name} {diff}")
                else:
                    raise IndexError()
            elif diff.startswith("Size"):
                if g1 is not None and g2 is not None:
                    ret.append(f" {g1.name} {diff} ({g1.size} != {g2.size})")
                else:
                    raise IndexError()
            elif diff.startswith("Location"):
                if g1 is not None and g2 is not None:
                    ret.append(f" {g1.name} {diff} ({g1.location} != {g2.location})") # noqa:E501 # pylint: disable=line-too-long
                else:
                    raise IndexError()
        return "\n".join(ret)

    def diagnose(self):
        """
        Attempt to find common memory issues
        """
        ret=["Potential memory issues:"]
        for g in self.globals:
            memory=g.memory
            if g.end>memory.end:
                ret.append(f' {g.name} past end of memory')
            if g.start<memory.start:
                ret.append(f' {g.name} past start of memory')
            module=g.module
            if module is not None:
                if g.end>module.end:
                    ret.append(f' {g.name} past end of module')
                if g.start<module.start:
                    ret.append(f' {g.name} past start of module')
            for g2 in self.globals:
                if g.name==g2.name:
                    # check for multiple instances of the same symbol
                    if module is not None \
                        and g2.module is not None \
                        and module!=g2.module:
                        #
                        ret.append(f' {g.name} from {module.name} redefined in {g2.module.name}') # noqa:E501 # pylint: disable=line-too-long
                else:
                    # check for overlapping symbols
                    if (g.start>=g2.start and g.start<g2.end)\
                        or (g.end>g2.start and g.end<=g2.end):
                        ret.append(f' {g.name}({g.start}..{g.end}) and {g2.name}({g2.start}..{g2.end}) overlap in memory') # noqa:E501 # pylint: disable=line-too-long
        return '\n'.join(ret)

    def __repr__(self):
        return '\n'.join([str(entry) for entry in self.entries])
