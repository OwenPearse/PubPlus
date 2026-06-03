# Apply PubPlus migrations + Melbourne seed to a local Docker Postgres (no Supabase CLI).
# Prereq: Docker running. Optional: $env:PGPORT (default 54333), $env:PGCONTAINER (default pubplus-mel-seed-pg)
$ErrorActionPreference = "Stop"
docker version 1>$null 2>&1
if ($LASTEXITCODE -ne 0) {
  throw "Docker is not available or the daemon is not running. Start Docker Desktop, then retry."
}
$root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $root "database\supabase\migrations"))) {
  throw "Could not find database/ from script location; run from repo."
}
$port = if ($env:PGPORT) { $env:PGPORT } else { "54333" }
$name = if ($env:PGCONTAINER) { $env:PGCONTAINER } else { "pubplus-mel-seed-pg" }

Write-Host "Using repo: $root"
$running = docker ps -q -f "name=$name"
if (-not $running) {
  Write-Host "Starting Postgres container $name on port $port..."
  docker run -d --rm --name $name -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres -p "${port}:5432" postgres:16-alpine
  Start-Sleep -Seconds 3
} else {
  Write-Host "Container $name already running."
}

$env:PGPASSWORD = "postgres"
$dbUrl = "postgresql://postgres:postgres@127.0.0.1:$port/postgres"

function Run-PsqlFile($path) {
  $p = (Resolve-Path $path).Path
  Write-Host "-> $p"
  Get-Content -Raw $p | docker exec -i $name psql -U postgres -d postgres -v ON_ERROR_STOP=1
  if ($LASTEXITCODE -ne 0) { throw "psql failed on $p" }
}

function Run-PsqlString($sql) {
  $sql | docker exec -i $name psql -U postgres -d postgres -v ON_ERROR_STOP=1
  if ($LASTEXITCODE -ne 0) { throw "psql failed" }
}

Run-PsqlFile (Join-Path $root "scripts\bootstrap_local_db_auth_stub.sql")

$migs = Get-ChildItem (Join-Path $root "database\supabase\migrations\*.sql") | Sort-Object Name
foreach ($f in $migs) {
  Run-PsqlFile $f.FullName
}

Run-PsqlFile (Join-Path $root "database\sql\seeds\dev_seed_reference_minimum.sql")
Run-PsqlFile (Join-Path $root "database\sql\seeds\dev_seed_reference_melbourne_localities.sql")
Run-PsqlFile (Join-path $root "database\sql\seeds\dev_seed_melbourne_inner_venues.sql")
Run-PsqlFile (Join-Path $root "database\sql\seeds\dev_seed_melbourne_inner_specials.sql")

Write-Host "Done. DSN: $dbUrl"
Write-Host "Run verification: scripts\verify_melbourne_seed_local.sql | docker exec -i $name psql -U postgres -d postgres"
