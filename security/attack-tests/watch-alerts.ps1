# watch-alerts.ps1 — Surveillance des états du moteur de remédiation RESILIENCE-ALPHA
# Lance une notification Windows Toast à chaque transition d'état (SUSPECT, MITIGATING, RECOVERED)
# Usage : powershell -ExecutionPolicy Bypass -File watch-alerts.ps1

param(
    [string]$StatusUrl = "http://192.168.137.1:8080/api/remediation/status",
    [int]$PollIntervalSeconds = 3
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime

# Chargement des APIs WinRT nécessaires pour les toasts
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]

function Show-Toast {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Scenario = "default"
    )
    $appId = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"

    $xml = @"
<toast scenario="$Scenario">
  <visual>
    <binding template="ToastGeneric">
      <text>$Title</text>
      <text>$Message</text>
    </binding>
  </visual>
  <audio src="ms-winsoundevent:Notification.Looping.Alarm2" loop="false"/>
</toast>
"@
    $toastXml = [Windows.Data.Xml.Dom.XmlDocument]::new()
    $toastXml.LoadXml($xml)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
}

$stateConfig = @{
    "SUSPECT"    = @{ Title = "⚠️  ML — Comportement suspect"; Scenario = "reminder";   Color = "yellow" }
    "MITIGATING" = @{ Title = "🔴  DDoS détecté — Mitigation active"; Scenario = "alarm";    Color = "red"    }
    "RECOVERED"  = @{ Title = "✅  Service rétabli"; Scenario = "default"; Color = "green"  }
    "FAILED"     = @{ Title = "💀  Remédiation en échec"; Scenario = "alarm";    Color = "red"    }
    "NORMAL"     = @{ Title = "🟢  Système nominal"; Scenario = "default"; Color = "green"  }
}

$previousState = $null
Write-Host "RESILIENCE-ALPHA — Surveillance active sur $StatusUrl" -ForegroundColor Cyan
Write-Host "Intervalle de sondage : ${PollIntervalSeconds}s  |  Ctrl+C pour arrêter`n" -ForegroundColor DarkGray

while ($true) {
    try {
        $response = Invoke-RestMethod -Uri $StatusUrl -Method GET -TimeoutSec 5 -ErrorAction Stop
        $currentState = $response.state

        if ($currentState -ne $previousState) {
            $ts = Get-Date -Format "HH:mm:ss"
            $cfg = $stateConfig[$currentState]

            if ($cfg) {
                Write-Host "[$ts]  $($cfg.Title)  (était : $previousState)" -ForegroundColor $cfg.Color
                $body = if ($previousState) { "Transition : $previousState → $currentState" } else { "État initial détecté" }
                Show-Toast -Title $cfg.Title -Message $body -Scenario $cfg.Scenario
            } else {
                Write-Host "[$ts]  Nouvel état inconnu : $currentState" -ForegroundColor DarkYellow
            }
            $previousState = $currentState
        }
    } catch {
        $ts = Get-Date -Format "HH:mm:ss"
        Write-Host "[$ts]  Erreur de connexion : $_" -ForegroundColor DarkRed
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}
