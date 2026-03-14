Automated Content Intelligence Engine



Problem Statement-->
Modern organizations consume large volumes of unstructured content from sources such as news websites, blogs, and RSS feeds. Manually reading and analyzing this information to extract insights is time-consuming and inefficient.

There is a need for an automated system that can continuously monitor content sources, summarize large text articles, analyze sentiment, and store structured insights for decision-making.

This project aims to build an automated content intelligence engine that ingests data from RSS feeds, processes it using transformer-based NLP models for summarization and sentiment analysis, and stores the results in a database through a scalable API-based pipeline.


Architecture-->

RSS Feed
   ↓
Scheduler
   ↓
RSS Monitor
   ↓
Workflow Engine
   ↓
Summarizer (BART)
   ↓
Sentiment Analysis
   ↓
SQLite Database
   ↓
FastAPI API
   ↓
Docker Container





Run Instructions
docker build -t content-intelligence-engine .
docker run -p 8000:8000 content-intelligence-engine


