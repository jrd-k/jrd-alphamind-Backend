<#
PowerShell helper to set GitHub repository secrets using the `gh` CLI.

Usage:
  - Set the following environment variables locally (in the shell), then run:
      .\scripts\set_github_secrets.ps1

Environment variables used (examples):
  $env:OPENAI_API_KEY
  $env:DEEPSEEK_API_KEY
  $env:EXNESS_API_KEY
  $env:EXNESS_BASE_URL
  $env:JUSTMARKETS_API_KEY
  $env:JUSTMARKETS_BASE_URL
  $env:TRADINGVIEW_WEBHOOK_SECRET

Requires: GitHub CLI (`gh`) authenticated with repo access.
This script only sets secrets; it does not echo them back.
#>

function Set-SecretIfExists([string]$name) {
    $val = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrEmpty($val)) {
        Write-Host "Skipping $name (not set in environment)"
        return
    }

    Write-Host "Setting GitHub secret: $name"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($val)
    $temp = [IO.Path]::GetTempFileName()
    [IO.File]::WriteAllBytes($temp, $bytes)
    gh secret set $name --body (Get-Content $temp -Raw) | Out-Null
    Remove-Item $temp
}

$secrets = 'OPENAI_API_KEY','DEEPSEEK_API_KEY','EXNESS_API_KEY','EXNESS_BASE_URL','JUSTMARKETS_API_KEY','JUSTMARKETS_BASE_URL','TRADINGVIEW_WEBHOOK_SECRET'

foreach ($s in $secrets) { Set-SecretIfExists $s }

Write-Host "Done. Verify secrets in GitHub repository Settings → Secrets → Actions."
