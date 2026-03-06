import feedparser


class RSSMonitor:

    def __init__(self, workflow_engine):
        self.workflow = workflow_engine


    def fetch_and_process(self, rss_url, db):
        feed = feedparser.parse(rss_url)

        results = []

        for entry in feed.entries[:5]:

            title = entry.title
            source = rss_url
            text = entry.summary

            result = self.workflow.process_content(
                title,
                source,
                text,
                db
            )

            results.append(result)

        return results