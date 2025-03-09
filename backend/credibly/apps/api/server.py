import os
import contextlib
import tempfile
from collections.abc import Iterator

import socketio
from textblob import TextBlob
import whisper
import moviepy
import yt_dlp
import easyocr
import cv2
from django.conf import settings
from django.core.asgi import get_asgi_application

from .models import BiasedContent, BiasedMedia
from .serializers import BiasedContentSerializer, BiasedMediaSerializer

# Initialize Socket.io server with explicit path
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
# Mount the Socket.io server at the root path
django_app = get_asgi_application()
app = socketio.ASGIApp(
    sio, 
    django_app,
    socketio_path='socket.io'  # Explicitly set the Socket.io path
)

# Initialize models
reader = easyocr.Reader(["en"])
audio_model = whisper.load_model("tiny")

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    print(f"Connection environment: {environ}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join(sid, data):
    """Handle client joining a room for a specific URL"""
    print(f"Join event received: {data}")
    if 'url' in data:
        url = data['url']
        print(f"Client {sid} joined room for URL: {url}")
        await sio.enter_room(sid, url)
        
        # Check if we already have analysis for this URL
        media = BiasedMedia.objects.filter(url=url).first()
        if media is not None and media.complete:
            # Send existing analysis
            await send_existing_analysis(sid, media)
        else:
            # Start new analysis
            await sio.emit('analysisStarted', {'status': 'Processing started'}, room=sid)
            await process_media(sid, url)

async def send_existing_analysis(sid, media):
    """Send existing analysis to client"""
    media_content = media.biased_content.all()
    
    # Calculate average bias strength
    total_bias = 0
    count = 0
    for content in media_content:
        total_bias += content.bias_strength
        count += 1
    
    avg_bias = total_bias / count if count > 0 else 0
    
    # Send credibility update
    await sio.emit('credibilityUpdate', {
        'bias_strength': avg_bias,
        'url': media.url
    }, room=sid)

async def process_media(sid, url):
    """Process media content and analyze for bias"""
    try:
        # Extract name from URL
        name = url.split('/')[-1] if '/' in url else url
        
        # Check if media already exists
        media = BiasedMedia.objects.filter(url=url).first()
        if media is None:
            media = BiasedMedia.objects.create(url=url, name=name)
        
        # Process video if it's a TikTok URL
        if 'tiktok.com' in url:
            audio_text, video_text = await process_video(url)
            
            # Analyze text for bias
            bias_results = await analyze_bias(audio_text, media)
            
            # Calculate average bias
            total_bias = sum(content.bias_strength for content in bias_results)
            avg_bias = total_bias / len(bias_results) if bias_results else 0
            
            # Send results to client
            await sio.emit('credibilityUpdate', {
                'bias_strength': avg_bias,
                'url': url
            }, room=url)
            
            # Mark as complete
            media.complete = True
            media.save()
        else:
            # For non-video URLs, use a simpler analysis
            await sio.emit('credibilityUpdate', {
                'bias_strength': 0.5,  # Default value
                'url': url
            }, room=url)
    except Exception as e:
        print(f"Error processing media: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

async def process_video(url):
    """Process video content to extract text"""
    print("Starting video processing")
    
    # Create temporary files
    temp_video = os.path.join(tempfile.gettempdir(), f"video_{url.split('/')[-1]}") + ".mp4"
    
    try:
        # Download video
        with yt_dlp.YoutubeDL({"outtmpl": temp_video}) as ydl:
            ydl.extract_info(url, download=True)
        
        print("Extracted video info")
        encoded_video = moviepy.VideoFileClip(temp_video)
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        encoded_video.audio.write_audiofile(temp_audio.name)
        
        print("Transcribing")
        with contextlib.redirect_stdout(None):
            # Transcribe audio
            transcribed_audio = audio_model.transcribe(temp_audio.name)
            
            lines = []
            for segment in transcribed_audio['segments']:
                time_duration = segment['end'] - segment['start']
                lines.append(f"{time_duration:.2f}s: {segment['text'].strip()}")
            
            audio_text = "\n".join(lines)
            
            # Extract text from video frames
            video_text = {}
            for t in range(0, encoded_video.n_frames, int(encoded_video.fps)):
                frame = encoded_video.get_frame(t)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                results = reader.readtext(frame, detail=0)
                if results:
                    video_text[t / int(encoded_video.fps)] = results
            
            video_text_str = "\n".join([f"{time}: {line}" for time, line in video_text.items()])
        
        # Clean up
        temp_audio.close()
        os.remove(temp_audio.name)
        os.remove(temp_video)
        
        return audio_text, video_text_str
    
    except Exception as e:
        print(f"Error processing video: {e}")
        # Clean up in case of error
        if os.path.exists(temp_video):
            os.remove(temp_video)
        return "", ""

async def analyze_bias(text: str, media: BiasedMedia) -> list:
    """Analyze text for bias using TextBlob"""
    print("Analyzing text for bias")
    results = []
    
    if not text:
        return results
    
    blob = TextBlob(text)
    for sentence in blob.sentences:
        content = BiasedContent.objects.create(
            media=media,
            content=sentence.raw,
            bias_strength=sentence.sentiment.subjectivity,
            accuracy=None,
        )
        results.append(content)
    
    return results

@sio.event
async def analysis(sid, data):
    """Handle analysis request for a URL"""
    print(f"Analysis event received: {data}")
    if 'url' in data:
        url = data['url']
        await process_media(sid, url) 