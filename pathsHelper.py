"""
Make working with Path objects easier
"""
import typing
import os
from pathlib import Path


PathLike=typing.Union[Path,str]
PathsLike=typing.Union[PathLike,typing.Iterable[PathLike]]


def asPath(
    path:PathLike,
    immutable:bool=True
    )->Path:
    """
    Convert anything path compatible to a Path
    """
    if isinstance(path,str):
        return Path(os.path.expandvars(path)).absolute()
    if immutable:
        return Path(path)
    return path


def asPaths(
    paths:typing.Optional[PathsLike]=None,
    immutable:bool=True
    )->typing.List[Path]:
    """
    Convert anything path compatible to Path objects
    """
    if not paths:
        return []
    if isinstance(paths,(str,Path)):
        return [asPath(paths,immutable)]
    return [asPath(path,immutable) for path in paths]
