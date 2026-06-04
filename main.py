import sys
import os
import asyncio
from urllib.parse import quote
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

HOST = "0.0.0.0"
PORT = 1337
PUBLIC_URL = os.getenv("PUBLIC_URL")

async def stream_process_output(youtube_url: str):
    """
    Spawns yt-dlp as an async subprocess and streams the raw video binary chunks
    directly from stdout, bypassing the server's hard drive entirely.
    """
    cmd = [
        "yt-dlp",
        "-f", "best",
        "-o", "-",
        "--quiet",
        "--no-playlist",
        youtube_url
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        while True:
            # Read chunks of data (64KB) as they stream in from YouTube
            chunk = await process.stdout.read(64 * 1024)
            if not chunk:
                break
            yield chunk
    except asyncio.CancelledError:
        # If the user cancels the download mid-way, terminate the subprocess immediately
        try:
            process.terminate()
            await process.wait()
        except ProcessLookupError:
            pass
        raise
    finally:
        # Clean up process resources when finished
        if process.returncode is None:
            try:
                process.terminate()
                await process.wait()
            except ProcessLookupError:
                pass

@app.get("/download")
async def download_video(url: str, title: str = "video"):
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL parameter")
        
    # URL-encode the title so spaces or special characters don't break the HTTP header
    safe_filename = f"{quote(title)}.mp4"
        
    # Force the browser to trigger a "Save File" dialog instead of playing it
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_filename}"',
        "Cache-Control": "no-cache"
    }
        
    return StreamingResponse(
        stream_process_output(url),
        media_type="application/octet-stream",
        headers=headers
    )

if __name__ == "__main__":
    if not PUBLIC_URL:
        sys.exit("Error: PUBLIC_URL environment variable not set")

    # Clean execution block—no blocking scheduler loops needed anymore!
    uvicorn.run(app, host=HOST, port=PORT)
