<#
.SYNOPSIS
  KiCad 10 independent ERC + static parity + DRC evidence capture (read-only).
.DESCRIPTION
  Does NOT regenerate fabrication files and does NOT modify .kicad_pcb.
  The DRC is expected to FAIL until the board has been rebuilt and routed.
#>
[CmdletBinding()]
param(
    [string] $ProjectRoot = (Resolve-Path '.').Path,
    [string] $KiCadCli = 'D:\Software\KiCad\10.0\bin\kicad-cli.exe',
    [string] $PythonExe = 'python'
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$Sch = Join-Path $ProjectRoot 'hardware\ax7010_servo_reva.kicad_sch'
$Pcb = Join-Path $ProjectRoot 'hardware\ax7010_servo_reva.kicad_pcb'
$Audit = Join-Path $ProjectRoot 'tools\ai_pcb_guide\scripts\board_parity_audit.py'
$Artifact = Join-Path $ProjectRoot 'artifacts\pcb-qa'
New-Item -ItemType Directory -Force $Artifact | Out-Null
foreach ($p in @($KiCadCli, $Sch, $Pcb, $Audit)) { if (!(Test-Path $p)) { throw "Missing: $p" } }
$rc = @{}
& $KiCadCli version
if ($LASTEXITCODE -ne 0) { throw 'KiCad CLI failed' }
function Run-Step($Name, $Command, $Argv) {
    Write-Host "`n=== $Name ==="
    & $Command @Argv
    $result = $LASTEXITCODE
    $script:rc[$Name] = $result
    Write-Host "EXIT_CODE $Name = $result"
}
Run-Step 'ERC' $KiCadCli @('sch','erc','--severity-all','--exit-code-violations','--output',(Join-Path $Artifact 'erc.rpt'),$Sch)
Run-Step 'XML NETLIST' $KiCadCli @('sch','export','netlist','--format','kicadxml','--output',(Join-Path $Artifact 'netlist.xml'),$Sch)
$xml = Join-Path $Artifact 'netlist.xml'
if ($rc['XML NETLIST'] -eq 0 -and (Test-Path $xml)) { Run-Step 'STATIC PARITY' $PythonExe @($Audit,'--netlist',$xml,'--board',$Pcb,'--output',(Join-Path $Artifact 'parity_audit.json'),'--strict') } else { $rc['STATIC PARITY'] = 1 }
foreach ($check in @('check_native_schematic','check_kicad_grid','check_schematic_layout','check_schematic_connectivity','check_design','test_pcb_checks')) {
    Run-Step $check $PythonExe @((Join-Path $ProjectRoot ('tools\' + $check + '.py')))
}
Run-Step 'TUTORIAL TESTS' $PythonExe @('-m','unittest','discover','-s',(Join-Path $ProjectRoot 'tools\ai_pcb_guide\tests'),'-v')
$native = Join-Path $Artifact 'netlist.net'
Run-Step 'NATIVE NETLIST' $KiCadCli @('sch','export','netlist','--output',$native,$Sch)
if ($rc['NATIVE NETLIST'] -eq 0 -and (Test-Path $native)) {
    foreach ($check in @('check_netlist_safety','check_ocp_behavior','check_pcb_parity','check_pcb_constraints')) {
        Run-Step $check $PythonExe @((Join-Path $ProjectRoot ('tools\' + $check + '.py')),$native)
    }
} else { $rc['NATIVE NETLIST DEPENDENTS'] = 1 }
Run-Step 'NATIVE DRC' $KiCadCli @('pcb','drc','--schematic-parity','--refill-zones','--severity-all','--exit-code-violations','--output',(Join-Path $Artifact 'pcb_drc.rpt'),$Pcb)
($rc | ConvertTo-Json -Depth 3) | Set-Content -Encoding utf8 (Join-Path $Artifact 'step_exit_codes.json')
Write-Host "Evidence: $Artifact"
if (@($rc.Values | Where-Object { $_ -ne 0 }).Count -gt 0) { exit 2 } else { exit 0 }
