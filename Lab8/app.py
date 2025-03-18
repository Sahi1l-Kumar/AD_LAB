from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import math
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import groq


load_dotenv(".env.local")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


AI_MODEL = "gemini"


if GEMINI_API_KEY and AI_MODEL == "gemini":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')


if GROQ_API_KEY and AI_MODEL == "groq":
    groq_client = groq.Client(api_key=GROQ_API_KEY)

app = FastAPI(title="YouTube Comment Analyzer")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory=".")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")


class CommentRequest(BaseModel):
    video_url: str
    comment_count: int = 100


class Comment(BaseModel):
    author: str
    text: str
    sentiment: str
    like_count: int
    published_at: str


class CommentResponse(BaseModel):
    comments: List[Comment]
    total_comments: int
    total_pages: int
    current_page: int
    page_size: int
    video_title: str


def extract_video_id(url: str) -> str:
    if "youtube.com/watch?v=" in url:
        return url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")


async def analyze_sentiment(text: str) -> str:
    try:
        if AI_MODEL == "gemini" and GEMINI_API_KEY:
            response = model.generate_content(
                f"Analyze the sentiment of this YouTube comment as 'positive', 'neutral', or 'negative'. Only return the sentiment label. Comment: {text}"
            )
            sentiment = response.text.strip().lower()

            if sentiment not in ["positive", "neutral", "negative"]:
                return "neutral"
            return sentiment

        elif AI_MODEL == "groq" and GROQ_API_KEY:
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis assistant. Respond with only 'positive', 'neutral', or 'negative'."},
                    {"role": "user", "content": f"Analyze the sentiment of this YouTube comment: {text}"}
                ],
                max_tokens=10
            )
            sentiment = response.choices[0].message.content.strip().lower()

            if sentiment not in ["positive", "neutral", "negative"]:
                return "neutral"
            return sentiment

        else:

            positive_words = ["good", "great", "awesome",
                              "amazing", "love", "excellent", "best", "perfect"]
            negative_words = ["bad", "terrible", "awful", "hate",
                              "worst", "horrible", "poor", "disappointing"]

            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if pos_count > neg_count:
                return "positive"
            elif neg_count > pos_count:
                return "negative"
            else:
                return "neutral"
    except Exception as e:
        print(f"Sentiment analysis error: {str(e)}")
        return "neutral"


async def fetch_youtube_comments(video_id: str, max_results: int = 100):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    video_response = youtube.videos().list(
        part='snippet',
        id=video_id
    ).execute()

    if not video_response['items']:
        raise HTTPException(status_code=404, detail="Video not found")

    video_title = video_response['items'][0]['snippet']['title']

    comments = []
    next_page_token = None

    while len(comments) < max_results:
        try:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                pageToken=next_page_token
            ).execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comment_text = comment['textDisplay']

                sentiment = await analyze_sentiment(comment_text)

                comments.append({
                    'author': comment['authorDisplayName'],
                    'text': comment_text,
                    'sentiment': sentiment,
                    'like_count': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })

            if 'nextPageToken' in response and len(comments) < max_results:
                next_page_token = response['nextPageToken']
            else:
                break

        except HttpError as e:
            if e.resp.status == 403:
                raise HTTPException(
                    status_code=403, detail="Comments are disabled for this video")
            else:
                raise HTTPException(
                    status_code=500, detail=f"YouTube API error: {str(e)}")

    return comments[:max_results], video_title


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/comments/")
async def get_comments(request: CommentRequest, page: int = 1, page_size: int = 10):
    try:
        video_id = extract_video_id(request.video_url)
        comments, video_title = await fetch_youtube_comments(video_id, request.comment_count)

        total_comments = len(comments)
        total_pages = math.ceil(total_comments / page_size)
        current_page = min(page, total_pages) if total_pages > 0 else 1

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_comments = comments[start_idx:end_idx]

        return {
            "comments": paginated_comments,
            "total_comments": total_comments,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size,
            "video_title": video_title
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
