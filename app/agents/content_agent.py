from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

from app.agents.tools import summarize_tool, sentiment_tool


class ContentAgent:

    def __init__(self):

        print("Initializing Content Agent...")

        # Create local LLM (agent brain)

        hf_pipeline = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            max_length=256
        )

        self.llm = HuggingFacePipeline(
            pipeline=hf_pipeline
        )

        # Register tools

        self.tools = [
            summarize_tool,
            sentiment_tool
        ]

        print("Content Agent ready.")

    def process_article(self, text: str):

        print("Agent processing article...")

        # Tool execution pipeline

        # Step 1: Summarize
        summary = summarize_tool.invoke(text)

        # Step 2: Sentiment
        sentiment = sentiment_tool.invoke(summary)

        return {
            "summary": summary,
            "sentiment": sentiment
        }