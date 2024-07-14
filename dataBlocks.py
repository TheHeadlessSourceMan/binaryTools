"""
Data blocks consist of a memory location and set of bytes
that reside there.
"""
import typing


class DataBlock:
    """
    Block of data on a memory device, eg, flash.
    """
    def __init__(self,address:int,data:bytes):
        self.address=address
        self.data=data

    @property
    def startAddress(self)->int:
        """
        Start address of the data block
        """
        return self.address
    @property
    def endAddress(self)->int:
        """
        End address of the data block
        """
        return self.address+self.size
    @property
    def size(self)->int:
        """
        Size of the data block
        """
        return len(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        """
        Dumps as a byte table
        """
        from byteFormatting import byteText,ansiColorize
        import re
        return ansiColorize(
            byteText(self.data,
                lineNumberStartAt=self.address,lineLength=32),
            {re.compile(r"^[^\s]*",re.MULTILINE):46}
            )


class DataBlocks:
    """
    Set of data blocks
    """
    def __init__(self,dataBlocks:typing.Iterable[DataBlock]=()):
        self.blocks:typing.List[DataBlock]=[]
        if dataBlocks:
            self.append(dataBlocks)

    def __iter__(self):
        return self.blocks.__iter__()

    def append(self,block:typing.Union[DataBlock,typing.Iterable[DataBlock]]):
        """
        Add more data blocks
        """
        if isinstance(block,DataBlock):
            self.blocks.append(block)
        else:
            self.blocks.extend(block)
    add=append
    extend=append

    def __repr__(self):
        return '\n\n'.join([repr(block) for block in self.blocks])
