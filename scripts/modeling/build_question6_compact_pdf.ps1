param(
    [string]$Python = 'D:/Python/Conda/envs/himcn-roads/python.exe',
    [string]$XeLaTeX = 'D:/texlive/2026/bin/windows/xelatex.exe'
)
$ErrorActionPreference = 'Stop'
$Q6ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
Push-Location -LiteralPath $Q6ProjectRoot
try {
    & $Python -X utf8 scripts/modeling/write_question6_real_chapter.py
    if ($LASTEXITCODE -ne 0) { throw 'Q6 source generation failed.' }
    New-Item -ItemType Directory -Path 'tmp/pdfs/q6_compact_build' -Force | Out-Null
    for ($Q6Pass = 1; $Q6Pass -le 2; $Q6Pass++) {
        & $XeLaTeX -interaction=nonstopmode -halt-on-error -output-directory=tmp/pdfs/q6_compact_build docs/paper/question6_adaptation.tex |
            Out-File -LiteralPath "tmp/pdfs/q6_compact_build/compiler_pass_$Q6Pass.txt" -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw "Q6 XeLaTeX pass $Q6Pass failed; inspect compiler log." }
    }
    Copy-Item -LiteralPath 'tmp/pdfs/q6_compact_build/question6_adaptation.pdf' -Destination 'output/pdf/question6_adaptation.pdf'
    & $Python -X utf8 scripts/modeling/verify_question6_chapter.py
    if ($LASTEXITCODE -ne 0) { throw 'Q6 document checks failed.' }
} finally {
    Pop-Location
}
