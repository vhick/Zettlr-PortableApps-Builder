# Zettlr PortableApps C++ launcher compile.
# Detect the real installed MSVC toolchain instead of trusting a single vswhere
# result/exit-code combination; fail closed if x64 compiler files are absent.
# No machine-wide SDK installation or registry changes are performed.
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

# Query all matching installations: -latest combined with pipeline -First 1
# can hide a good alternative or produce unreliable native-command exit status.
if (Test-Path -LiteralPath $vswhere -PathType Leaf) {
    $results = @(& $vswhere -all -products '*' -requires $component -property installationPath)
    $vsStatus = $LASTEXITCODE  # Read immediately after invoking this native command.
    Write-Host "vswhere required-component exit code: $vsStatus"
    foreach ($location in $results) { Add-VsCandidate ([string] $location) }
    # Additional readable diagnostics/fallback if the component query was empty.
    if ($locations.Count -eq 0) {
        $allResults = @(& $vswhere -all -products '*' -property installationPath)
        $allStatus = $LASTEXITCODE
        Write-Host "vswhere all-installations exit code: $allStatus"
        foreach ($location in $allResults) { Add-VsCandidate ([string] $location) }
    }
} else {
    Write-Warning "vswhere.exe absent at $vswhere; checking conventional GitHub runner installation paths."
}

# Pin no VS release year: GitHub-hosted runners may change installation years.
foreach ($year in @('2026','2022','2019')) {
    foreach ($edition in @('Enterprise','Professional','Community','BuildTools')) {
        Add-VsCandidate (Join-Path $env:ProgramFiles "Microsoft Visual Studio\$year\$edition")
    }
}

$selected = $null
foreach ($candidate in $locations) {
    $dev = Join-Path $candidate 'Common7\Tools\VsDevCmd.bat'
    $msvc = Join-Path $candidate 'VC\Tools\MSVC'
    $compilers = @()
    if (Test-Path -LiteralPath $msvc -PathType Container) {
        $compilers = @(Get-ChildItem -LiteralPath $msvc -Directory -ErrorAction Stop | ForEach-Object {
            Join-Path $_.FullName 'bin\Hostx64\x64\cl.exe'
        } | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
    }
    Write-Host "MSVC candidate: $candidate | developer shell: $(Test-Path -LiteralPath $dev -PathType Leaf) | x64 compilers: $($compilers.Count)"
    if ((Test-Path -LiteralPath $dev -PathType Leaf) -and $compilers.Count -gt 0) {
        $selected = @{ Dev = $dev; Root = $candidate }
        break
    }
}
if ($null -eq $selected) {
    throw 'No installed MSVC x64 compiler and VsDevCmd.bat found. Review detected installations and GitHub runner image; do not download unverified toolchains.'
}

$dest = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'assets\portable.ico') -Destination (Join-Path $root 'launcher\portable.ico') -Force
$batch = Join-Path $env:RUNNER_TEMP 'compile-zettlr-launcher.cmd'
$lines = @(
    '@echo off',
    'chcp 65001 >nul',
    'call "' + $selected.Dev + '" -no_logo -arch=amd64 -host_arch=amd64',
    'if errorlevel 1 exit /b 1',
    'cd /d "' + $root + '"',
    'rc.exe /nologo /i "' + $root + '\launcher" /fo "' + $root + '\bin\portable-launcher.res" "' + $root + '\launcher\portable-launcher.rc"',
    'if errorlevel 1 exit /b 1',
    'cl.exe /nologo /std:c++17 /EHsc /O2 /W4 /utf-8 /DUNICODE /D_UNICODE /Fe:"' + $root + '\bin\ZettlrPortable.exe" "' + $root + '\launcher\ZettlrPortable.cpp" "' + $root + '\bin\portable-launcher.res" /link /SUBSYSTEM:WINDOWS /MACHINE:X64 Shell32.lib User32.lib',
    'exit /b %errorlevel%'
)
# Explicit UTF-8 is used for the cmd script (after chcp 65001); GitHub-hosted
# RUNNER_TEMP is local to the ephemeral runner and contains no user data.
[System.IO.File]::WriteAllText($batch, ($lines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
Write-Host "Compiling ZettlrPortable.exe with MSVC from $($selected.Root)"
& cmd.exe /d /c "`"$batch`""
$buildStatus = $LASTEXITCODE
if ($buildStatus -ne 0) { throw "Launcher MSVC compilation failed with exit code $buildStatus" }
$exe = Join-Path $dest 'ZettlrPortable.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'MSVC returned success but launcher executable is missing' }
& $exe --self-test
$selfTestStatus = $LASTEXITCODE
if ($selfTestStatus -ne 0) { throw "Compiled launcher self-test failed with exit code $selfTestStatus" }
Write-Host 'WINDOWS-COMPILED: compiled 64-bit launcher and passed its isolated pre-staging self-test.'
