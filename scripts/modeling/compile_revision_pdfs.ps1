param([string[]]$Documents = @('full_paper', 'full_paper_zh', 'question1_protection_definition', 'question2_framework', 'question3_framework', 'question4_sensitivity', 'question5_evaluation', 'question6_adaptation'), [string]$OutputDirectory = 'output/pdf/skill_checked_20261007')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$pdfDirectory = Join-Path $projectRoot $OutputDirectory
$logDirectory = Join-Path $projectRoot 'output/revision_feasibility/20261006'
New-Item -ItemType Directory -Force -Path $pdfDirectory, $logDirectory | Out-Null
Push-Location $projectRoot
try {
    foreach ($document in $Documents) {
        if ($document -notin @('full_paper', 'full_paper_zh', 'question1_protection_definition', 'question2_framework', 'question3_framework', 'question4_sensitivity', 'question5_evaluation', 'question6_adaptation')) { throw "Unknown document: $document" }
        $jobName = if ($document -eq 'full_paper_zh') { 'full_paper_zh_explained' } else { $document }
        $source = "docs/paper/$document.tex"
        for ($pass = 1; $pass -le 2; $pass++) {
            $runLog = Join-Path $logDirectory "compile_${jobName}_pass${pass}.txt"
            & 'D:/texlive/2026/bin/windows/xelatex.exe' -interaction=nonstopmode -halt-on-error -file-line-error "-output-directory=$pdfDirectory" "-jobname=$jobName" $source *> $runLog
            if ($LASTEXITCODE -ne 0) { throw "Compilation failed: $source, pass $pass. See $runLog" }
        }
        Write-Output "Compiled $jobName.pdf (two passes)."
    }
} finally { Pop-Location }
