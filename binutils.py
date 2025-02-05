"""
Interfaces to the GNU binutils tools.
    https://www.gnu.org/software/binutils/

These allow you to do cool things like profile, inspect, and modify
executables and libraries on any system that binutils supports.
(which is a mostly everything)

NOTE: on windows, these ship with the mingw compiler.

TODO: there are other packages that do this by accessing
BFD (Binary File Descriptor) library directly, which would
be more efficient than command line fiddling.
    https://github.com/syscall7/python-bfd
    https://ftp.gnu.org/old-gnu/Manuals/bfd-2.9.1/html_chapter/bfd_1.html
"""
import typing
import subprocess


# TODO: this is a bit unusual to move in on a vagrant installation.
# We really need to perform a proper search for it.
MINGW_DIR='C:\\HashiCorp\\Vagrant\\embedded\\mingw64\\'
BINUTILS_DIR=MINGW_DIR+'bin\\'


def nm(filename:str,data:typing.Optional[bytes]):
    """
    call the binutils nm util
    """
    raise NotImplementedError()

def valgrind(filename:str):
    """
    TODO: this is a placeholder.  need to move it out

    See also:
    https://stackoverflow.com/questions/517589/tools-to-get-a-pictorial-function-call-graph-of-code/31190167#31190167
    https://stackoverflow.com/questions/375913/how-do-i-profile-c-code-running-on-linux/378024#378024
    """
    raise NotImplementedError()

def gprof(
    filename:str,
    sourceDirectories:typing.Iterable[str]=(),
    callGraph:bool=True
    )->str:
    """
    Run the executable file using gprof profiler.
    In many ways valgrind is better.

    See also:
    https://sourceware.org/binutils/docs-2.39/gprof/index.html
    """
    cmd=[BINUTILS_DIR+'gprof.exe','-p']
    if callGraph:
        cmd.append('-q')
    if sourceDirectories:
        cmd.append('-I '+(';'.join(sourceDirectories)))
    cmd.append(f'"{filename}"')
    print(cmd)
    po=subprocess.Popen(cmd,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
    out,_=po.communicate()
    return out.decode('UTF-8',errors='ignore')


def listExports(filename:str,data:typing.Optional[bytes])->typing.List[str]:
    """
    List symbols exported by a module
    """
    nmresults=nm(filename,data)
    raise NotImplementedError()

def visualStudioCoverage(filename:str)->str:
    """
    NOTE: must compile with the /Profile linker switch in the makefile

    TODO: need to execute these, of course
    TODO: I know the outputs are output.vsp and output.vsp.coverage
        but what to do with them?  They don't seem to open correctly
        with visual studio.

    See also:
    https://github.com/danielpalme/ReportGenerator/wiki/Visual-Studio-Coverage-Tools
    https://learn.microsoft.com/en-us/visualstudio/test/using-code-coverage-to-determine-how-much-code-is-being-tested?view=vs-2022&tabs=csharp
    https://github.com/Microsoft/vstest-docs/blob/main/docs/extensions/datacollector.md
    https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-code-coverage?tabs=windows
    https://learn.microsoft.com/en-us/visualstudio/test/microsoft-code-coverage-console-tool?view=vs-2022
    """
    ret:typing.List[str]=[]
    # inject instrumentation in the generated executable
    cmd=['VSInstr','/COVERAGE',filename]
    ret.append(' '.join(cmd))
    # shut down any existing monitor
    cmd=['VSPerfCmd','/shutdown']
    ret.append(' '.join(cmd))
    # start the monitor as another thread
    cmd=['vsperfmon','/coverage','/output:output.vsp']
    cmd.insert(0,'start')
    cmd.insert(1,'""')
    ret.append(' '.join(cmd))
    # start the coverage logging
    cmd=['VSPerfCmd','/start:trace','/output:output.vsp']
    ret.append(' '.join(cmd))
    cmd=['VSPerfCmd','/globalon']
    ret.append(' '.join(cmd))
    # run the program as normal
    cmd=[filename]
    ret.append(' '.join(cmd))
    # stop the coverage logging
    cmd=['VSPerfCmd','/globaloff']
    ret.append(' '.join(cmd))
    cmd=['VSPerfCmd','/shutdown']
    ret.append(' '.join(cmd))
    return '\n'.join(ret)


if __name__=='__main__':
    import sys
    results=visualStudioCoverage(sys.argv[1])
    print(results)
