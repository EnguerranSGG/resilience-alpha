import httpx

from remediation_engine.signals import LokiSecuritySignals, PrometheusDegradationProbe


def _vector(value: str) -> dict:
    return {"status": "success", "data": {"resultType": "vector", "result": [{"value": [0, value]}]}}


def test_prometheus_probe_reads_recording_rules() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params["query"]
        return httpx.Response(200, json=_vector("1200" if "latency" in query else "0.1"))

    report = PrometheusDegradationProbe("http://p", 1, httpx.MockTransport(handler)).measure()
    assert report.available and report.latency_p95_ms == 1200 and report.error_rate == 0.1


def test_prometheus_down_is_reported_unavailable() -> None:
    report = PrometheusDegradationProbe("http://p", 1, httpx.MockTransport(lambda r: httpx.Response(503))).measure()
    assert not report.available


def test_nan_and_empty_results_are_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "latency" in request.url.params["query"]:
            return httpx.Response(200, json=_vector("NaN"))
        return httpx.Response(200, json={"data": {"result": []}})

    report = PrometheusDegradationProbe("http://p", 1, httpx.MockTransport(handler)).measure()
    assert report.latency_p95_ms is None and report.error_rate is None


def test_loki_counts_blocked_requests() -> None:
    report = LokiSecuritySignals(
        "http://l", 1, httpx.MockTransport(lambda r: httpx.Response(200, json=_vector("42")))
    ).measure()
    assert report.available and report.blocked_requests_1m == 42
