[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9.-]*$')]
    [string]$HostEc2,
    [ValidatePattern('^[a-zA-Z_][a-zA-Z0-9_-]*$')]
    [string]$Usuario = 'ubuntu',
    [string]$Chave,
    [switch]$Publico,
    [switch]$Postgres,
    [switch]$SomentePacote
)

$ErrorActionPreference = 'Stop'
$raizProjeto = Split-Path -Parent $PSScriptRoot
if ($Postgres -and -not $Publico) {
    throw 'Use -Postgres junto com -Publico.'
}
if (-not $SomentePacote) {
    if (-not $HostEc2 -or -not $Chave) {
        throw 'Informe -HostEc2 e -Chave, ou use -SomentePacote.'
    }
    $caminhoChave = (Resolve-Path -LiteralPath $Chave).Path
}

$arquivos = @(
    'Dockerfile.api', '.dockerignore', 'requirements.runtime.txt', 'compose.yaml',
    'src', '.streamlit/config.toml', 'artifacts/modelo',
    'scripts/iniciar-ec2.sh', 'scripts/verificar-deploy.py'
)
if ($Postgres) {
    $arquivos += 'compose.postgres.yaml'
} else {
    $arquivos += 'data/raw/churn.csv'
}
if ($Publico) {
    $arquivos += @('compose.publico.yaml', 'deploy',
        'scripts/configurar-https.sh', 'scripts/renovar-https.sh',
        'scripts/proteger-host.sh')
}
foreach ($arquivo in $arquivos) {
    if (-not (Test-Path -LiteralPath (Join-Path $raizProjeto $arquivo))) {
        throw "Arquivo ausente: $arquivo. Exporte o champion antes de publicar."
    }
}

$idVersao = 'release-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' +
    [guid]::NewGuid().ToString('N').Substring(0, 6)
$diretorioPacotes = Join-Path $raizProjeto 'artifacts/pacotes'
New-Item -ItemType Directory -Path $diretorioPacotes -Force | Out-Null
$pacote = Join-Path $diretorioPacotes "$idVersao.tar.gz"
& tar -czf $pacote --exclude=__pycache__ --exclude=*.pyc -C $raizProjeto @arquivos
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o pacote de deploy.' }
Write-Output "Pacote: $pacote"
Write-Output "SHA256: $((Get-FileHash -LiteralPath $pacote -Algorithm SHA256).Hash)"
if ($SomentePacote) { return }

$destinoSsh = "${Usuario}@${HostEc2}"
$opcoesSsh = @('-i', $caminhoChave, '-o', 'BatchMode=yes', '-o',
    'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=accept-new')
$pastaRemota = "mlops-churn/releases/$idVersao"
& ssh @opcoesSsh $destinoSsh "mkdir -p $pastaRemota"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao conectar na EC2 por SSH.' }
& scp @opcoesSsh $pacote "${destinoSsh}:${pastaRemota}/pacote.tar.gz"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao enviar o pacote para a EC2.' }
$argumentosInicio = if ($Postgres) {
    "publico-postgres $HostEc2"
} elseif ($Publico) {
    "publico $HostEc2"
} else {
    'local'
}
& ssh @opcoesSsh $destinoSsh "cd $pastaRemota && tar -xzf pacote.tar.gz && bash scripts/iniciar-ec2.sh $argumentosInicio"
if ($LASTEXITCODE -ne 0) { throw 'Deploy falhou. Consulte a saída acima.' }
if ($Postgres) {
    Write-Output "Aplicacao conectada ao PostgreSQL. Pasta da release: $pastaRemota"
} elseif ($Publico) {
    & ssh @opcoesSsh $destinoSsh "cd $pastaRemota && bash scripts/configurar-https.sh $HostEc2 preparar"
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o proxy HTTPS.' }
    Write-Output "Proxy preparado. Pasta da release: $pastaRemota"
    Write-Output "Apos liberar TCP 80/443, execute configurar-https.sh $HostEc2 ativar na EC2."
} else {
    Write-Output 'Frontend disponivel no localhost:8501 da EC2 (use tunel SSH).'
}
