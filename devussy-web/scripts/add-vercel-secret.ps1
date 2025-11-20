param(
    [string]$envName = "REQUESTY_API_KEY",
    [ValidateSet('development','preview','production')]
    [string]$targetEnv = 'production'
)

Write-Host "Make sure you're logged in: vercel login"
Write-Host "Adding secret: $envName to Vercel environment: $targetEnv"

# This will prompt for a value interactively (safer than writing it in plaintext).
vercel env add $envName $targetEnv

Write-Host "Done. You can now deploy with the secret available in the environment."
