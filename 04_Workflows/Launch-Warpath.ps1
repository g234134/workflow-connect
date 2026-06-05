#Requires -Version 5.1
<#
.SYNOPSIS
    Launch-Warpath.ps1 — v2.53 一鍵指揮系統（戰路全自動管線）

.DESCRIPTION
    嚴格按下列順序執行：
        1. 體檢 (Doctor)   ：gov_main 跑 _doctor_main_cabin.py
        2. 登錄 (Register) ：gov_main 跑 _register_fingerprints.py --dir <raw_inbound>
        3. 精煉 (Refine)   ：gov_agency 跑 _factory_wave_01.py --wave <N>
        3b.難案入庫       ：gov_main 跑 _ingest_difficult_case_library.py（案例庫，供下波 Groq 快取）
        4. 報喜 (Alert)    ：gov_main 跑 _warpath_alert.py "<完成訊息>"

    技術紀律：
      · 雙艙皆以 & "venv\Scripts\python.exe" 直呼，**不** 走 Activate.ps1。
      · 強制 PYTHONPATH = D:\大唐三省六部、PYTHONUTF8=1、TANG_GOV_ROOT=root。
      · 任何步驟非 0 退碼 → 立即發 Telegram 警告並中止；不洩漏任何金鑰原文。

.PARAMETER WaveN
    Wave 件數，對應 _factory_wave_01.py 的 --wave。預設 100。

.PARAMETER InboundDir
    指紋登錄掃描目錄；預設 05_Temp_Cache\raw_inbound。

.PARAMETER DryRun
    僅列印計畫的命令鏈，不實際執行 (用於管線連通性自檢)。

.PARAMETER SkipAlert
    全程不發 Telegram（含失敗警告與最終報喜）；測試用。

.PARAMETER SkipRefine
    略過第 3 步（精煉），僅做體檢 + 登錄 + 報喜。煙霧測試專用。

.PARAMETER SkipCloseout
    略過第 4 步之後的「戰報同步 + 結案草案 Telegram」（v2.56）；預設會執行。

.PARAMETER SkipCaseIngest
    略過第 3b 步（難案案例庫合併）；預設於精煉成功後執行。

.EXAMPLE
    . .\Launch-Warpath.ps1                          # 正式跑：Wave=100
    .\Launch-Warpath.ps1 -DryRun                    # 連通性檢查
    .\Launch-Warpath.ps1 -WaveN 1 -SkipAlert        # 小量真打、靜默 Telegram
#>

[CmdletBinding()]
param(
    [int]$WaveN = 100,
    [string]$InboundDir = $null,
    [switch]$DryRun,
    [switch]$SkipAlert,
    [switch]$SkipRefine,
    [switch]$SkipCloseout,
    [switch]$SkipCaseIngest
)

$ErrorActionPreference = 'Stop'

# ── 路徑解析 ─────────────────────────────────────────────
$Root        = Split-Path -Parent $PSScriptRoot
$Workflows   = Join-Path $Root '04_Workflows'
$VenvMainPy  = Join-Path $Root '01_Environments\python_venvs\gov_main\Scripts\python.exe'
$VenvAgcPy   = Join-Path $Root '01_Environments\python_venvs\gov_agency\Scripts\python.exe'
$DoctorPy    = Join-Path $Workflows '_doctor_main_cabin.py'
$RegisterPy  = Join-Path $Workflows '_register_fingerprints.py'
$FactoryPy   = Join-Path $Workflows '_factory_wave_01.py'
$SyncPipePy  = Join-Path $Workflows '_sync_wave_to_scout_pipeline.py'
$ReportGenPy = Join-Path $Workflows '_report_generator.py'
$CaseIngestPy = Join-Path $Workflows '_ingest_difficult_case_library.py'
$CompareBenchPy = Join-Path $Workflows '_wave_compare_benchmark.py'
$AlertPy     = Join-Path $Workflows '_warpath_alert.py'
$EnvLoader   = Join-Path $Workflows '_Load-TangEnv.ps1'

if (-not $InboundDir) {
    $InboundDir = Join-Path $Root '05_Temp_Cache\raw_inbound'
}

# ── 環境變數（強制） ─────────────────────────────────────
$env:PYTHONPATH    = $Root
$env:PYTHONUTF8    = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:TANG_GOV_ROOT = $Root

# 載入 .env（共用工具，只在實跑時做；DryRun 也可載以便驗證鍵存在性）
if (Test-Path -LiteralPath $EnvLoader) {
    . $EnvLoader
    Initialize-TangEnv -Root $Root -Label 'warpath' | Out-Null
}
else {
    Write-Warning "_Load-TangEnv.ps1 不存在：$EnvLoader（.env 可能未載入）"
}

# ── 預檢：venv / 腳本存在性 ──────────────────────────────
$preflight = @(
    @{ Name = 'gov_main python';  Path = $VenvMainPy  },
    @{ Name = 'gov_agency python'; Path = $VenvAgcPy  },
    @{ Name = 'doctor script';     Path = $DoctorPy   },
    @{ Name = 'register script';   Path = $RegisterPy },
    @{ Name = 'factory script';    Path = $FactoryPy  },
    @{ Name = 'sync pipeline';    Path = $SyncPipePy },
    @{ Name = 'report generator'; Path = $ReportGenPy },
    @{ Name = 'case ingest';      Path = $CaseIngestPy },
    @{ Name = 'benchmark compare'; Path = $CompareBenchPy },
    @{ Name = 'alert script';      Path = $AlertPy    }
)
$missing = @()
foreach ($p in $preflight) {
    if (-not (Test-Path -LiteralPath $p.Path)) { $missing += "$($p.Name) → $($p.Path)" }
}
if ($missing.Count -gt 0) {
    Write-Error ("[Warpath] 預檢失敗，缺少：`n  - " + ($missing -join "`n  - "))
    return
}

# 確保 raw_inbound 存在（不存在則建立空資料夾，登錄會回報 0 件）
if (-not (Test-Path -LiteralPath $InboundDir)) {
    New-Item -ItemType Directory -Path $InboundDir -Force | Out-Null
}

# 互動點火亦寫入排程日誌（與 Setup-Schedule 相同路徑），方便戰後封存
$TranscriptLog = Join-Path $Root '06_Exports_Output\reports\scheduler\last_run.log'
if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Split-Path $TranscriptLog) | Out-Null
    try { Stop-Transcript | Out-Null } catch {}
    try { Start-Transcript -LiteralPath $TranscriptLog -Force | Out-Null } catch {}
}

# ── Telegram 警報函式（透過 gov_main + _warpath_alert.py） ───────
function Send-WarpathAlert {
    param([Parameter(Mandatory)][string]$Message)
    if ($SkipAlert) {
        Write-Host "[warpath-alert] (skipped) $Message" -ForegroundColor DarkGray
        return
    }
    try {
        & $VenvMainPy $AlertPy $Message | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "[warpath-alert] exit=$LASTEXITCODE（已忽略，不阻斷主流程）"
        }
    }
    catch {
        Write-Warning "[warpath-alert] exception: $($_.Exception.GetType().Name)"
    }
}

# ── 步驟執行器 ───────────────────────────────────────────
function Invoke-WarpathStep {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$PyExe,
        [Parameter(Mandatory)][string[]]$Argv,
        [switch]$NoFailAlert
    )
    $pretty = "$Label`n  $PyExe " + ($Argv -join ' ')
    Write-Host "── [$Label] ──────────────" -ForegroundColor Cyan
    Write-Host "  cmd: $PyExe $($Argv -join ' ')" -ForegroundColor DarkGray

    if ($DryRun) {
        Write-Host "  (dry-run: 略過實際執行)" -ForegroundColor Yellow
        return
    }

    & $PyExe @Argv
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        $err = "[戰路警報] 步驟『$Label』失敗 (exit=$code)。管線中止。"
        if (-not $NoFailAlert) { Send-WarpathAlert -Message $err }
        throw $err
    }
    Write-Host "  [OK] $Label 完成" -ForegroundColor Green
}

# ── 主流程 ───────────────────────────────────────────────
Write-Host '======== Launch-Warpath v2.53 ========' -ForegroundColor Magenta
Write-Host "  Root         = $Root"
Write-Host "  PYTHONPATH   = $env:PYTHONPATH"
Write-Host "  WaveN        = $WaveN"
Write-Host "  InboundDir   = $InboundDir"
Write-Host "  DryRun       = $DryRun"
Write-Host "  SkipAlert    = $SkipAlert"
Write-Host "  SkipRefine   = $SkipRefine"
Write-Host "  SkipCloseout = $SkipCloseout"
Write-Host "  SkipCaseIngest = $SkipCaseIngest"
Write-Host '──────────────────────────────────────'

# 大量 Wave 時縮減 Telegram 進度頻率，避免洗版（仍保留 Groq 節流於 Evaluator 內）
$progressEvery = 10
if ($WaveN -gt 200) {
    $progressEvery = [int][Math]::Max(200, [Math]::Ceiling($WaveN / 40.0))
}
if ($progressEvery -gt 2000) { $progressEvery = 2000 }
Write-Host "  progress_every (factory --every) = $progressEvery" -ForegroundColor DarkGray

try {
    Invoke-WarpathStep -Label '1/4 體檢 Doctor (gov_main)' `
                       -PyExe $VenvMainPy `
                       -Argv @($DoctorPy)

    Invoke-WarpathStep -Label '2/4 指紋登錄 Register (gov_main)' `
                       -PyExe $VenvMainPy `
                       -Argv @($RegisterPy, '--dir', $InboundDir)

    if ($SkipRefine) {
        Write-Host "── [3/4 精煉 Refine] 已被 -SkipRefine 略過 ──" -ForegroundColor Yellow
    }
    else {
        Invoke-WarpathStep -Label '3/4 精煉 Refine (gov_agency)' `
                           -PyExe $VenvAgcPy `
                           -Argv @($FactoryPy, '--wave', "$WaveN", '--every', "$progressEvery")
        if (-not $SkipCaseIngest) {
            Write-Host '── [3b 難案入庫 Case ingest (gov_main)] ──────────────' -ForegroundColor Cyan
            try {
                & $VenvMainPy $CaseIngestPy | Out-Host
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "[3b] difficult case ingest exit=$LASTEXITCODE（已繼續後續步驟）"
                }
            }
            catch {
                Write-Warning "[3b] difficult case ingest exception: $($_.Exception.Message)（已繼續）"
            }
        }
        else {
            Write-Host '── [3b 難案入庫] 已被 -SkipCaseIngest 略過 ──' -ForegroundColor Yellow
        }
    }

    if (-not $SkipCloseout) {
        Invoke-WarpathStep -Label '4a 戰報同步 scout_last_pipeline (gov_main)' `
                           -PyExe $VenvMainPy `
                           -Argv @($SyncPipePy)

        Invoke-WarpathStep -Label '4b 結案草案 v2.56 (gov_main, Telegram)' `
                           -PyExe $VenvMainPy `
                           -Argv @($ReportGenPy, '--write', '--telegram-send')
        Write-Host '── [4c 波次耗時對照 wave_benchmark] ──────────────' -ForegroundColor Cyan
        try {
            $minSampled = 0
            if ($WaveN -ge 500) { $minSampled = $WaveN }
            & $VenvMainPy $CompareBenchPy --min-sampled $minSampled | Out-Host
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "[4c] benchmark compare exit=$LASTEXITCODE（已忽略）"
            }
        }
        catch {
            Write-Warning "[4c] benchmark compare exception: $($_.Exception.Message)"
        }
    }
    else {
        Write-Host "── [4a/4b 結案草案] 已被 -SkipCloseout 略過 ──" -ForegroundColor Yellow
    }

    if (-not $DryRun) {
        $tail = "WaveN=$WaveN ；結案報告見 06_Exports_Output\reports\closing_draft_*.txt 與 scout_last_pipeline.json"
        Send-WarpathAlert -Message "戰路系統：精煉管線執行完畢。$tail"
    }
    Write-Host '========== [DONE] Warpath 全鏈完成 ==========' -ForegroundColor Green
}
catch {
    Write-Host '========== [ABORT] Warpath 中止 ==========' -ForegroundColor Red
    Write-Host "  reason: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    if (-not $DryRun) {
        try { Stop-Transcript | Out-Null } catch {}
    }
}
