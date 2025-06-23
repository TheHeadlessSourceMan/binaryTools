"""
Represents a tree of linkages between code items,
that is, their requirements.

Useful for things like diagnosing missing modules
or finding circular dependencies.
"""
import typing


ItemCompatible=typing.Union["DependencyTreeItem",str]
class DependencyTreeItem:
    """
    A single named item in the linkage tree
    """
    def __init__(self,
        name:str):
        self.name=name

    @property
    def directDependencies(self
        )->typing.Iterable["DependencyTreeItem"]:
        """
        Dependencies directly required by this item
        """
        return []

    @property
    def allDependencies(self
        )->typing.Iterable["DependencyTreeItem"]:
        """
        Dependencies directly or indirectly required by this item
        (will only return each one once)
        """
        needToCheck=list(self.directDependencies)
        alreadyMentioned:typing.Set[str]=set()
        for requirement in needToCheck:
            yield requirement
            alreadyMentioned.add(requirement.name)
            for subRequirement in requirement.directDependencies:
                if subRequirement.name not in alreadyMentioned:
                    needToCheck.append(subRequirement) # noqa: E501 # pylint: disable=modified-iterating-list

    @property
    def depencencyTree(self)->typing.Iterable["DependencyTreeItem"]:
        """
        Get each layer of the dependency tree,
        even if it involves duplicates.

        Will not revisit circular dependencies

        TODO: not finished
        """
        needToCheck=list(self.directDependencies)
        alreadyMentioned:typing.Set[str]=set()
        for requirement in needToCheck:
            yield requirement
            alreadyMentioned.add(requirement.name)
            for subRequirement in requirement.directDependencies:
                if subRequirement.name not in alreadyMentioned:
                    needToCheck.append(subRequirement) # noqa: E501 # pylint: disable=modified-iterating-list

    @property
    def circularDependencies(self)->typing.Iterable["DependencyTreeItem"]:
        """
        Find circular dependencies

        TODO: create a full path to get a picture of who did what
        """
        needToCheck=list(self.directDependencies)
        alreadyMentioned:typing.Set[str]=set()
        for requirement in needToCheck:
            alreadyMentioned.add(requirement.name)
            for subRequirement in requirement.directDependencies:
                if subRequirement.name not in alreadyMentioned:
                    needToCheck.append(subRequirement) # noqa: E501 # pylint: disable=modified-iterating-list
                else:
                    yield requirement

    def __eq__(self,other:ItemCompatible):
        if not isinstance(other,str):
            other=other.name
        return self.name==other

    def __repr__(self,currentIndent='',indent='    '):
        ret=[currentIndent+self.name]
        nextIndent=currentIndent+indent
        for dep in self.directDependencies:
            ret.append(dep.__repr__(nextIndent))
        return '\n'.join(ret)

SymbolCompatible=typing.Union["Symbol",str]
class Symbol(DependencyTreeItem):
    """
    A single named symbol (either a Method or a Property)
    """
    def __init__(self,
        name:str,
        module:typing.Optional["Module"]=None):
        """ """
        DependencyTreeItem.__init__(self,name)
        self.module:typing.Optional[DependencyTreeItem]=module

class Property(Symbol):
    """
    A single property
    """
    def __init__(self,
        name:str,
        module:typing.Optional["Module"]=None):
        """ """
        Symbol.__init__(self,name,module)

class Method(Symbol):
    """
    A single method.

    This may have dependencies if it depends on other methods.
    """
    def __init__(self,
        name:str,
        module:typing.Optional["Module"]=None):
        """ """
        Symbol.__init__(self,name,module)


class Module(DependencyTreeItem):
    """
    A code module (.exe, .dll, .lib, .obj, etc)
    """
    def __init__(self,
        name:str):
        """ """
        self.imports:typing.Dict[str,Symbol]={}
        self.exports:typing.Dict[str,Symbol]={}
        DependencyTreeItem.__init__(self,name)

    @property
    def directDependencies(self
        )->typing.Iterable["DependencyTreeItem"]:
        """
        Dependencies directly required by this item
        """
        alreadyMentioned:typing.Set[str]=set()
        for imp in self.imports.values():
            if imp.module.name not in alreadyMentioned:
                alreadyMentioned.add(imp.module.name)
                yield imp
