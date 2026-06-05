$ErrorActionPreference = 'Stop'
try {
  Start-ScheduledTask -TaskName 'Tang_Chariot_Auto_Refine'
  'started OK' | Out-File -LiteralPath 'D:\大唐三省六部\06_Exports_Output\reports\scheduler\start_signal.txt' -Encoding utf8
}
catch {
  ('start FAILED: ' + $_.Exception.Message) | Out-File -LiteralPath 'D:\大唐三省六部\06_Exports_Output\reports\scheduler\start_signal.txt' -Encoding utf8
}
