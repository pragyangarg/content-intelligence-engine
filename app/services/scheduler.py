import time
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class Scheduler:

    def __init__(self, rss_monitor, db_session_factory):
        self.rss_monitor = rss_monitor
        self.db_session_factory = db_session_factory
        self.running = False

    def start(self, rss_url, interval=300):
        self.running = True

        def run():
            while self.running:
                logger.info("Running RSS automation...")

                db = self.db_session_factory()

                try:
                    self.rss_monitor.fetch_and_process(rss_url, db)
                finally:
                    db.close()

                logger.info("Waiting for next cycle...")
                time.sleep(interval)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()