#Requires -Version 5.1
# _Load-TangEnv.ps1 — 共用：將 01_Environments\.env 載入目前 Process 環境變數（不印出任何值）
# 由 Enter-Main.ps1 / Enter-Agency.ps1 點源。

function Initialize-TangEnv {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $EnvFile = Join-Path $Root '01_Environments\.env'
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        Write-Host "[$Label] 未找到 .env：$EnvFile"
        return 0
    }
    $loaded = 0
    foreach ($line in Get-Content -LiteralPath $EnvFile -Encoding UTF8) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        $idx = $t.IndexOf('=')
        if ($idx -lt 1) { continue }
        $k = $t.Substring(0, $idx).Trim()
        $v = $t.Substring($idx + 1).Trim().Trim('"').Trim("'")
        if ($k) {
            Set-Item -Path "Env:$k" -Value $v
            $loaded++
        }
    }
    Write-Host "[$Label] .env 已載入 $loaded 鍵 (內容遮罩)"
    return $loaded
}
