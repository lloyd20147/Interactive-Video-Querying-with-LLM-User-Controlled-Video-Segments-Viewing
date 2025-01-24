import os
import requests
import json
import re
import config
from flask import Flask, render_template, request, jsonify
app=Flask(__name__)
from youtube_transcript_api import YouTubeTranscriptApi
import webbrowser
import pandas as pd
#from flask import Flask, request, render_template, send_file, redirect, url_for
from datetime import datetime
from io import StringIO
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {config.api_key}", 
    "Content-Type": "application/json"
}
def upload_video(video_id):
   try:
        srt = YouTubeTranscriptApi.get_transcript(video_id)
        with open("subtitles.txt", "w") as f:
                for idx, entry in enumerate(srt):
                        f.write(f"Subtitle {idx+1}\n")
                        s_time=entry['start']
                        e_time=s_time+entry['duration']
                        s_minutes, s_seconds = divmod(s_time, 60)
                        s_seconds, s_milliseconds = divmod(s_seconds * 1000, 1000)
                        start_time=f"{int(s_minutes):02}:{int(s_seconds):02}:{int(s_milliseconds):03}"
                        e_minutes, e_seconds = divmod(e_time, 60)
                        e_seconds, e_milliseconds = divmod(s_seconds * 1000, 1000)
                        end_time=f"{int(e_minutes):02}:{int(e_seconds):02}:{int(e_milliseconds):03}"
                        f.write(f"Time: {start_time} - {end_time}\n")
        
        # Writing the subtitle text
                        f.write(f"{entry['text']}\n\n")
   except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None
   return "subtitles.txt"                     

def extracted_text(path):
        with open(path, 'r') as file:
                text=file.read()
        return text
        
def query(prompt, extracted_text):
                        prompt = prompt+extracted_text
    
                # Send text to OpenAI API
                        data = {
                            "model": "gpt-4o-mini",  # Change model if needed
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 1500,
                            "temperature": 0.5
                        }
                    # data = {
                    #     "model": "gpt-4o-mini",  # Change model if needed
                    #     "messages": [
                    #         {"role": "user", "content": f"give me only {st} in detailed information from {extracted_text}  in json format without extra information"}
                    #     ],
                    #     "max_tokens": 1500,
                    #     "temperature": 0.5
                    # }

                        response = requests.post(OPENAI_URL, headers=HEADERS, data=json.dumps(data))
                        if response.status_code == 200:
                            response_data = response.json()
                            message = response_data['choices'][0]['message']['content']
                            print(message)
                            return message
def runnning_video(message, video_id):
        time_pattern=r'(\d{2}:\d{2}.\d{3})'
        match=re.search(time_pattern, message)
        if match:
                start_time=match.group(1)
                minutes, seconds_ms, milliseconds=start_time.split(':')
                start_seconds=int(minutes)*60+int(seconds_ms)+int(milliseconds)/1000
                print(start_seconds)
# URL of the YouTube video
                youtube_url = f'https://www.youtube.com/watch?v={video_id}&t={int(start_seconds)}s'  # 180 seconds = 3 minutes

# Open the YouTube video in the default web browser
                webbrowser.open(youtube_url)
        else:
                print(message)
@app.route('/',methods=['GET', 'POST'])
def index():
        if request.method=='POST':
                video_url=request.form.get('video_url')
                user_query=request.form.get('query')
                if video_url:
                       start_pos=0
                       eqaul_po=video_url.find('=', start_pos)
                       video_id=video_url[eqaul_po+1:]
                       subtitles_file=upload_video(video_id) 
                       if subtitles_file:
                           extracted_text_file=extracted_text(subtitles_file)
                           if user_query:
                                message=query(user_query,extracted_text_file)
                                runnning_video(message, video_id)
                                return render_template('index.html', video_url=video_url, message=message, query=query, extracted_text=extracted_text_file)
                           return render_template('index.html', video_url=video_url, extracted_text=extracted_text_file, subtitle_processed=True)
                       return render_template('index.html', error="Failed to process video subtitles")
                else:
                        return render_template('index.html', error="No URL Provided")
         
        return render_template('index.html')
if __name__=='__main__':
        app.run(debug=True)
