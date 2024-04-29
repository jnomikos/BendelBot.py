import asyncio
import subprocess

import yt_dlp

async def download_and_stream(url):
    # yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredquality': '160',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Download audio information
        info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
        
        # Open process for ffmpeg
        process = subprocess.Popen([
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-i', '-',  # Read from standard input (pipe)
            '-f', 's16le',
            '-ar', '44100',
            '-ac', '2',
            '-',  # Write to standard output
        ], stdin=subprocess.PIPE)

        # Download and stream audio data
        for chunk in ydl.download(url):
            process.stdin.write(chunk)

        # Wait for ffmpeg to finish processing
        process.wait()


# Example usage
asyncio.run(download_and_stream("https://www.youtube.com/watch?v=zWh3CShX_do"))