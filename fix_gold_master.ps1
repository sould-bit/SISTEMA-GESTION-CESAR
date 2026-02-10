
$path = "c:\Users\jp151\lab\el_rincon\SISTEMA-GESTION-CESAR\tests-e2e\fixtures\gold_master_utf8.sql"
$lines = Get-Content $path

# 1. Clean up the end of the file
$lastValidLine = -1
for ($i = $lines.Count - 1; $i -ge 0; $i--) {
    if ($lines[$i] -match "ALTER TABLE ONLY public.users") {
        $lastValidLine = $i + 1 # Include the next line if it's the ADD CONSTRAINT
        if ($i + 1 -lt $lines.Count -and $lines[$i+1] -match "ADD CONSTRAINT") {
            $lastValidLine = $i + 1
        }
        break
    }
}

if ($lastValidLine -ne -1) {
    $newLines = $lines[0..$lastValidLine]
} else {
    $newLines = $lines
}

# 2. Add the permission to role_permissions
$enhancedLines = @()
$permissionAdded = $false
foreach ($line in $newLines) {
    $enhancedLines += $line
    if ($line -match "4085ff41-5a2e-4fca-bd9b-e77ba404c416" -and -not $permissionAdded) {
        $enhancedLines += "7afe4847-4daf-4417-91f6-da9275074bc8`t8011da3e-e193-45c8-ac46-4250db01d59e`tdcc21cd0-1a73-4a91-bc4f-f18267db396e`t\N`t2026-02-09 22:02:54.4953`t\N"
        $permissionAdded = $true
    }
}

# Add final footer
$enhancedLines += ""
$enhancedLines += "--"
$enhancedLines += "-- PostgreSQL database dump complete"
$enhancedLines += "--"

$enhancedLines | Set-Content $path -Encoding utf8
