# Zettlr PortableApps community x64 launcher build (b1r3).
# Uses Microsoft's documented Developer PowerShell initialization and .NET's
# structured ArgumentList. Never relay quoted Visual Studio paths to cmd.exe.
# Avoids shell-dependent quoting bugs for paths with spaces / Unicode names.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$component = 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64'
$seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$locations = [System.Collections.Generic.List[string]]::new()

function Add-VsCandidate([string] $directory) {
    if ([string]::IsNullOrWhiteSpace($directory)) { return }
    $directory = $directory.Trim().TrimEnd([char]'\')
    if ((Test-Path -LiteralPath $directory -PathType Container) -and $seen.Add($directory)) {
        $locations.Add($directory)
    }
}

if (Test-Path -LiteralPath $vswhere -PathType Leaf) {
    $results = @(& $vswhere -all -products '*' -requires $component -property installationPath)
    $vsStatus = $LASTEXITCODE
    Write-Host "vswhere required-component exit code: $vsStatus"
    foreach ($location in $results) { Add-VsCandidate ([string] $location) }
    if ($locations.Count -eq 0) {
        $allResults = @(& $vswhere -all -products '*' -property installationPath)
        $allStatus = $LASTEXITCODE
        Write-Host "vswhere all-installations exit code: $allStatus"
        foreach ($location in $allResults) { Add-VsCandidate ([string] $location) }
    }
} else {
    Write-Warning "vswhere.exe absent at $vswhere; checking known Visual Studio locations."
}

# Do not tie the builder to a single VS release year or Enterprise edition.
foreach ($year in @('2026','2022','2019')) {
    foreach ($edition in @('Enterprise','Professional','Community','BuildTools')) {
        Add-VsCandidate (Join-Path $env:ProgramFiles "Microsoft Visual Studio\$year\$edition")
    }
}

$selected = $null
foreach ($candidate in $locations) {
    $devCmd = Join-Path $candidate 'Common7\Tools\VsDevCmd.bat'
    $devShell = Join-Path $candidate 'Common7\Tools\Launch-VsDevShell.ps1'
    $msvc = Join-Path $candidate 'VC\Tools\MSVC'
    $compilers = @()
    if (Test-Path -LiteralPath $msvc -PathType Container) {
        $compilers = @(Get-ChildItem -LiteralPath $msvc -Directory -ErrorAction Stop | ForEach-Object {
            Join-Path $_.FullName 'bin\Hostx64\x64\cl.exe'
        } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
    }
    Write-Host "MSVC candidate: $candidate | developer shell: $(Test-Path -LiteralPath $devShell -PathType Leaf) | x64 compilers: $($compilers.Count)"
    if ((Test-Path -LiteralPath $devCmd -PathType Leaf) -and
        (Test-Path -LiteralPath $devShell -PathType Leaf) -and $compilers.Count -gt 0) {
        $selected = @{ Shell = $devShell; Root = $candidate }
        break
    }
}
if ($null -eq $selected) {
    throw 'No complete MSVC x64 and Developer PowerShell installation found. Confirm VsDevCmd.bat, Launch-VsDevShell.ps1 and Hostx64\x64\cl.exe on runner.'
}

# Launch-VsDevShell.ps1 is the Microsoft documented build-automation interface.
# This modifies PATH/LIB/INCLUDE only in this short-lived CI PowerShell process.
Write-Host "Initializing Developer PowerShell: $($selected.Shell)"
& ($selected.Shell) -Arch amd64 -HostArch amd64 -SkipAutomaticLocation
if ([string]::IsNullOrWhiteSpace($env:VSCMD_VER)) {
    throw 'Visual Studio Developer PowerShell returned without VSCMD_VER; compiler environment was not initialized.'
}
$cl = (Get-Command -Name cl.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$rc = (Get-Command -Name rc.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
if (-not (Test-Path -LiteralPath $cl -PathType Leaf) -or -not (Test-Path -LiteralPath $rc -PathType Leaf)) {
    throw 'Developer PowerShell did not expose working compiler and resource compiler paths.'
}
if (-not $cl.StartsWith($selected.Root + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Compiler resolved outside the selected Visual Studio root: $cl"
}
Write-Host "Initialized VS $env:VSCMD_VER | cl.exe: $cl | rc.exe: $rc"

# Structured ArgumentList preserves each path as ONE Windows argument, even if
# the CI checkout directory contains spaces or Unicode. No cmd.exe /c or
# nested batch-script command strings are needed.
function Invoke-BuildTool([string] $file, [string[]] $arguments) {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $file
    $startInfo.WorkingDirectory = $root
    $startInfo.UseShellExecute = $false
    foreach ($arg in $arguments) { [void] $startInfo.ArgumentList.Add($arg) }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) { throw "Process could not start: $file" }
        $process.WaitForExit()
        $status = $process.ExitCode
    } finally {
        $process.Dispose()
    }
    if ($status -ne 0) { throw "Build tool $file returned exit code $status" }
}

$dest = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'assets\portable.ico') -Destination (Join-Path $root 'launcher\portable.ico') -Force
$resource = Join-Path $dest 'portable-launcher.res'
$rcSource = Join-Path $root 'launcher\portable-launcher.rc'
$cppSource = Join-Path $root 'launcher\ZettlrPortable.cpp'
$exe = Join-Path $dest 'ZettlrPortable.exe'

Write-Host 'Compiling launcher resource with rc.exe'
Invoke-BuildTool $rc @('/nologo', '/i', (Join-Path $root 'launcher'), '/fo', $resource, $rcSource)
if (-not (Test-Path -LiteralPath $resource -PathType Leaf)) { throw 'Resource compilation produced no .res output' }
Write-Host 'Compiling ZettlrPortable.exe with initialized x64 MSVC'
Invoke-BuildTool $cl @(
    '/nologo', '/std:c++17', '/EHsc', '/O2', '/W4', '/utf-8',
    '/DUNICODE', '/D_UNICODE',
    ('/Fe:' + $exe), $cppSource, $resource,
    '/link', '/SUBSYSTEM:WINDOWS', '/MACHINE:X64', 'Shell32.lib', 'User32.lib'
)
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'MSVC reported success but the launcher .exe is missing' }
& $exe --self-test
$selfTestStatus = $LASTEXITCODE
if ($selfTestStatus -ne 0) { throw "Compiled launcher self-test failed with exit code $selfTestStatus" }
Write-Host 'WINDOWS-COMPILED: compiled the x64 launcher and passed isolated pre-staging self-test.'
