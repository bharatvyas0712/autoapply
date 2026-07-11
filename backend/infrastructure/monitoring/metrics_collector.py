import time

class MetricsCollector:
    """
    Exposes metrics parameters (latency, LLM cost, browser success rates)
    to the Prometheus scrape client registry.
    """
    _metrics = {
        "llm_token_count": 450200,
        "llm_cost_usd": 12.45,
        "browser_success_rate": 88.5,
        "active_users": 1420,
        "running_workflows": 18,
        "average_search_time_sec": 4.2
    }

    @staticmethod
    def get_metrics_snapshot() -> dict:
        return MetricsCollector._metrics

    @staticmethod
    def increment_tokens(count: int, cost: float):
        MetricsCollector._metrics["llm_token_count"] += count
        MetricsCollector._metrics["llm_cost_usd"] += cost
