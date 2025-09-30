from googleapiclient.discovery import build
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_comments(video_id, max_results=100):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results
    )
    
    while request:
        response = request.execute()
        for item in response['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comment = snippet['textOriginal']
            user_name = snippet['authorDisplayName']
            comments.append({
                "video_id": video_id,
                "username": user_name,
                "comment": comment
            })
        
        request = youtube.commentThreads().list_next(request, response)
    
    return comments

video_list = ["QhmebdBeXKY", "lvb0_bGZDTU", "atYGhviVhf8", "SAAVZtoQTH4", "IzbN42Yi8cE", "_qZaQs__2yQ"]
all_comments = []

for video_id in video_list:
    print(f"Fetching comments from video: {video_id}")
    comments = get_comments(video_id)
    all_comments.extend(comments)

output_file = "raw/9_25_youtube_comments.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_comments, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_comments)} comments to {output_file}")
