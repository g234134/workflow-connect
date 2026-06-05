#Requires -Version 5.1
<#
.SYNOPSIS
    一鍵撤銷 Tang_Chariot_Auto_Refine 排程（轉呼叫 Setup-Schedule.ps1 -Remove）。
    若工作當初以 SYSTEM 註冊，請「以系統管理員身分」執行本腳本。
#>
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Setup-Schedule.ps1') -Remove @args
