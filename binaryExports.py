"""
status: works great, but could be faster by being multithreaded
"""
import typing
import os
import subprocess


def dllExports(dllFilename)->typing.Generator[str,None,None]:
    """
    dump the exports lists of a binary dll or executable
    """
    po=subprocess.Popen(['dumpbin','/exports',dllFilename],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,_=po.communicate()
    lines=out.decode('utf-8',errors='ignore').split('\n')
    inExports=False
    for line in lines:
        if not inExports:
            if line.startswith('    ordinal hint RVA      name'):
                inExports=True
        elif line.startswith('  Summary'):
            return
        else:
            cols=line.strip().split()
            if len(cols)>3:
                yield cols[3]

def findExportNamed(
    exportName,paths,
    extensions=('.dll','.exe')
    )->typing.Generator[str,None,None]:
    """
    finds all binary files and then searches their exports list
    for a particular symbol
    """
    visited=set()
    tape=[]
    if isinstance(paths,str):
        paths=[paths]
    def processFile(filename)->typing.Generator[str,None,None]:
        for exp in dllExports(filename):
            if exp==exportName:
                yield filename
                return
    extensions=set([e.replace('.','') for e in extensions])
    for p in paths:
        p=os.path.abspath(os.path.expandvars(p))
        if os.path.isdir(p):
            tape.append(p)
        elif p.rsplit('.',1)[-1] in extensions:
            processFile(p)
    while tape:
        d=tape.pop(0)
        visited.add(d)
        for filename in os.listdir(d):
            filename=os.path.join(d,filename)
            if os.path.isdir(filename):
                if filename not in visited:
                    tape.append(filename)
            elif filename.rsplit('.',1)[-1] in extensions:
                yield from processFile(filename)
