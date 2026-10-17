param(
    [ValidateSet('as-is', 'to-be')][string]$Modo = 'to-be'
)
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$perfil = Join-Path $repoRoot (Join-Path 'local' "hermes-$Modo")
if (-not (Test-Path (Join-Path $perfil 'config.yaml'))) {
    throw 'Ejecuta primero scripts/preparar_hermes.py con un Python funcional.'
}
$anteriorHermesHome = $env:HERMES_HOME
try {
    $env:HERMES_HOME = $perfil
    Write-Host "Perfil de laboratorio: $perfil"
    Write-Host 'Comprueba /tools: debe aparecer solo mcp_laboratorio_laboratorio_controlado.'
    Write-Host 'Si hay otras herramientas, detén la prueba; no hay aislamiento comprobado.'
    & hermes chat --toolsets mcp-laboratorio
} finally {
    $env:HERMES_HOME = $anteriorHermesHome
}
