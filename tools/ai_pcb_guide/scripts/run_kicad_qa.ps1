# Reference convenience wrapper. Strict PCB/release remains blocked.
[CmdletBinding()]
param([string] $ProjectRoot = '.', [string] $KiCadCli = 'kicad-cli', [string] $PythonExe = 'python')
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
& $PythonExe (Join-Path $ProjectRoot 'tools/pcb.py') verify --project ads8588s --scope release --kicad-cli $KiCadCli
exit $LASTEXITCODE
