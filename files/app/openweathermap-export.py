"""Application exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge, Enum
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)-15s %(message)s')
LOG = logging.getLogger("openweathermap-export")

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, app_port=80, polling_interval_seconds=5):
        self.app_port = app_port
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.current_requests = Gauge("app_requests_current", "Current requests")
        self.pending_requests = Gauge("app_requests_pending", "Pending requests")
        self.total_uptime = Gauge("app_uptime", "Uptime")
        self.health = Enum("app_health", "Health", states=["healthy", "unhealthy"])

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Fetch raw status data from the application
        #resp = requests.get(url=f"http://localhost:{self.app_port}/status")
        #status_data = resp.json()

        # Update Prometheus metrics with application metrics
        self.current_requests.set(1)
        self.pending_requests.set(2)
        self.total_uptime.set(3)
        self.health.state("healthy")
        LOG.info("Update prometheus")

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "300"))
    app_port = int(os.getenv("APP_PORT", "80"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9003"))

    app_metrics = AppMetrics(
        app_port=app_port,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    LOG.info("start prometheus port: %s", exporter_port)
    app_metrics.fetch()
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()