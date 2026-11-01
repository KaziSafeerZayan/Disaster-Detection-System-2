param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8501,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$appUrl = "http://127.0.0.1:$Port"
$logDirectory = Join-Path $PSScriptRoot 'logs'

function Test-DashboardReady {
    try {
        $response = Invoke-WebRequest -Uri "$appUrl/_stcore/health" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200 -and $response.Content.Trim() -eq 'ok'
    } catch {
        return $false
    }
}

function Open-Dashboard {
    Write-Host "Flooder is ready at $appUrl"
    Write-Host 'The app runs in the background. You can close this window.'
    if (-not $NoBrowser) { Start-Process -FilePath $appUrl -WindowStyle Hidden }
}

try {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        $existingServer = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        $existingParent = Get-CimInstance Win32_Process -Filter "ProcessId=$($existingServer.ParentProcessId)"
        $belongsToProject = ($existingServer.CommandLine -match [regex]::Escape($PSScriptRoot)) -or
            (($existingServer.CommandLine -match 'run_local\.py') -and ($existingParent.CommandLine -match [regex]::Escape($PSScriptRoot)))
        if (-not $belongsToProject) { throw "Another application is using port $Port. Start Flooder with a different -Port." }
        if (-not (Test-DashboardReady)) { throw "Flooder is running on port $Port but is not responding. Check the files in $logDirectory." }
        Open-Dashboard
        exit 0
    }

    if (-not (Test-Path -LiteralPath $pythonPath)) {
        Write-Host 'Creating the local Python environment...'
        if ($uvCommand) {
            & $uvCommand.Source venv .venv --python 3.11
        } else {
            $systemPython = Get-Command python -ErrorAction Stop
            & $systemPython.Source -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or newer is required"'
            if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or newer, then run start.bat again.' }
            & $systemPython.Source -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
    }

    $requirementsFile = Join-Path $PSScriptRoot 'requirements.txt'
    $hashAlgorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $requirementsHash = [BitConverter]::ToString($hashAlgorithm.ComputeHash([IO.File]::ReadAllBytes($requirementsFile))).Replace('-', '')
    } finally {
        $hashAlgorithm.Dispose()
    }
    $markerPath = Join-Path $PSScriptRoot '.venv\requirements.sha256'
    $installedHash = if (Test-Path -LiteralPath $markerPath) { (Get-Content -LiteralPath $markerPath -Raw).Trim() } else { '' }

    if ($installedHash -ne $requirementsHash) {
        Write-Host 'Installing project dependencies (first launch or dependency update)...'
        if ($uvCommand) {
            & $uvCommand.Source pip install --python $pythonPath -r $requirementsFile
        } else {
            & $pythonPath -m ensurepip --upgrade
            if ($LASTEXITCODE -ne 0) { throw 'Could not prepare pip.' }
            & $pythonPath -m pip install -r $requirementsFile
        }
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your connection and try again.' }
        Set-Content -LiteralPath $markerPath -Value $requirementsHash
    }

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $stdoutLog = Join-Path $logDirectory "server-$Port.log"
    $stderrLog = Join-Path $logDirectory "server-$Port.error.log"
    $serverFile = Join-Path $PSScriptRoot 'run_local.py'
    $serverArguments = @(('"' + $serverFile + '"'), '--server.port', $Port, '--server.address', '127.0.0.1', '--server.headless', 'true')
    Write-Host 'Starting Flooder...'
    $serverProcess = Start-Process -FilePath $pythonPath -ArgumentList $serverArguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
    Set-Content -LiteralPath (Join-Path $logDirectory "server-$Port.pid") -Value $serverProcess.Id

    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    do {
        if (Test-DashboardReady) {
            Open-Dashboard
            exit 0
        }
        $serverProcess.Refresh()
        if ($serverProcess.HasExited) {
            $details = if (Test-Path -LiteralPath $stderrLog) { (Get-Content -LiteralPath $stderrLog -Tail 12) -join [Environment]::NewLine } else { '' }
            throw "Flooder could not start. $details"
        }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Flooder did not become ready in time. Check $stderrLog."
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
