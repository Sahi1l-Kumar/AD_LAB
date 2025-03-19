from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import re
import time
import asyncio
from dotenv import load_dotenv
from googleapiclient.discovery import build
from typing import List, Dict, Any
import google.generativeai as genai
from groq import AsyncGroq
import logging
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv(".env.local")

app = FastAPI()


app.mount("/styles", StaticFiles(directory="styles"), name="styles")
templates = Jinja2Templates(directory=".")


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')


if GROQ_API_KEY:
    groq_client = AsyncGroq(api_key=GROQ_API_KEY)


MIN_REQUEST_INTERVAL = 1


last_request_time = {
    "gemini": 0,
    "groq": 0
}


def extract_video_id(url):
    """Extract YouTube video ID from URL"""

    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL")


async def fetch_comments(video_id: str, max_comments: int) -> List[dict]:
    """Fetch comments from a YouTube video"""
    comments = []
    next_page_token = None

    try:
        while len(comments) < max_comments:

            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)
                               ),
                pageToken=next_page_token,
                textFormat="plainText"
            )

            response = request.execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token or len(comments) >= max_comments:
                break

        return comments[:max_comments]

    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching comments: {str(e)}")


async def rate_limit_request(api_name):
    """Implement rate limiting to avoid 429 errors"""
    current_time = time.time()
    elapsed = current_time - last_request_time[api_name]

    if elapsed < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - elapsed
        await asyncio.sleep(wait_time)

    last_request_time[api_name] = time.time()


async def analyze_batch_with_gemini(comments_batch: List[Dict]) -> List[str]:
    """Analyze a batch of comments with Gemini API"""
    await rate_limit_request("gemini")

    try:

        comments_text = "\n".join(
            [f"Comment {i+1}: {comment['text']}" for i, comment in enumerate(comments_batch)])

        prompt = f"""
        Analyze the sentiment of each of the following {len(comments_batch)} YouTube comments.
        For each comment, classify it as 'positive', 'neutral', or 'negative'.
        
        {comments_text}
        
        Respond in JSON format with comment numbers as keys and sentiment as values:
        {{
          "1": "positive",
          "2": "negative",
          ...
        }}
        
        Only return the JSON object, nothing else.
        """

        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1]
        if response_text.endswith("```"):
            response_text = response_text.split("```")[0]

        response_text = response_text.strip()
        if not response_text.startswith("{"):

            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]

        results = json.loads(response_text)

        sentiments = []
        for i in range(len(comments_batch)):
            sentiment = results.get(str(i+1), "neutral").lower()
            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"
            sentiments.append(sentiment)

        return sentiments

    except Exception as e:
        logger.error(f"Error with Gemini API batch: {e}")

        return ["neutral"] * len(comments_batch)


async def analyze_batch_with_groq(comments_batch: List[Dict]) -> List[str]:
    """Analyze a batch of comments with Groq API"""
    await rate_limit_request("groq")

    try:

        comments_text = "\n".join(
            [f"Comment {i+1}: {comment['text']}" for i, comment in enumerate(comments_batch)])

        response = await groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analysis assistant. You will receive multiple YouTube comments. Analyze each comment and classify it as 'positive', 'neutral', or 'negative'. Return results as a JSON object."
                },
                {
                    "role": "user",
                    "content": f"""
                    Analyze the sentiment of each of the following {len(comments_batch)} YouTube comments.
                    
                    {comments_text}
                    
                    Return a JSON object with comment numbers as keys and sentiment values ('positive', 'neutral', or 'negative'):
                    {{
                      "1": "positive",
                      "2": "negative",
                      ...
                    }}
                    Only return the JSON object, nothing else.
                    """
                }
            ],
            max_tokens=1000
        )

        response_text = response.choices[0].message.content.strip()

        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1]
        if response_text.endswith("```"):
            response_text = response_text.split("```")[0]

        response_text = response_text.strip()
        if not response_text.startswith("{"):

            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]

        results = json.loads(response_text)

        sentiments = []
        for i in range(len(comments_batch)):
            sentiment = results.get(str(i+1), "neutral").lower()
            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"
            sentiments.append(sentiment)

        return sentiments

    except Exception as e:
        logger.error(f"Error with Groq API batch: {e}")

        return ["neutral"] * len(comments_batch)


async def batch_analyze_sentiment(comments: List[dict], model: str, batch_size: int = 10) -> List[dict]:
    """Analyze sentiment in real batches for efficiency and to avoid rate limits"""
    results = []

    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]

        if model.lower() == "gemini" and GEMINI_API_KEY:
            batch_sentiments = await analyze_batch_with_gemini(batch)
        else:
            batch_sentiments = await analyze_batch_with_groq(batch)

        for j, sentiment in enumerate(batch_sentiments):
            if i + j < len(comments):
                results.append({
                    **batch[j],
                    "sentiment": sentiment
                })

    return results


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(
    request: Request,
    video_url: str = Form(...),
    comment_count: int = Form(...),
    model: str = Form(...)
):
    try:

        video_id = extract_video_id(video_url)

        comments = await fetch_comments(video_id, comment_count)

        max_comments_to_process = min(len(comments), 100)
        if max_comments_to_process < len(comments):
            logger.warning(
                f"Limiting analysis to {max_comments_to_process} comments to avoid API rate limits")

        comments_to_process = comments[:max_comments_to_process]

        batch_size = 20
        analyzed_comments = await batch_analyze_sentiment(comments_to_process, model, batch_size)

        sentiment_counts = {
            "positive": sum(1 for c in analyzed_comments if c["sentiment"] == "positive"),
            "neutral": sum(1 for c in analyzed_comments if c["sentiment"] == "neutral"),
            "negative": sum(1 for c in analyzed_comments if c["sentiment"] == "negative")
        }

        return {
            "video_id": video_id,
            "comments": analyzed_comments,
            "stats": sentiment_counts
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
