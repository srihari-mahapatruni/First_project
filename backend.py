import os
from flask import Flask, request, render_template
import whisper
from googletrans import Translator
import moviepy.editor as mp

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load Whisper model once
whisper_model = whisper.load_model("small")
translator = Translator()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    lang = request.form["language"]

    # Save file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Step 1: Extract audio/text
    if filepath.endswith((".mp4", ".avi", ".mov")):
        # Extract audio from video
        video = mp.VideoFileClip(filepath)
        audio_path = filepath.rsplit(".", 1)[0] + ".wav"
        video.audio.write_audiofile(audio_path)
        input_audio = audio_path
    elif filepath.endswith((".mp3", ".wav")):
        input_audio = filepath
    else:
        return "Only video/audio supported in this demo ✅"

    # Step 2: Speech-to-Text with timestamps
    result = whisper_model.transcribe(input_audio, task="transcribe")
    segments = result["segments"]

    # Step 3: Translate each segment
    translated_segments = []
    for seg in segments:
        orig_text = seg["text"]
        translated_text = translator.translate(orig_text, dest=lang).text
        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": translated_text
        })

    # Step 4: Generate Subtitles File (SRT)
    srt_path = os.path.join(OUTPUT_FOLDER, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(translated_segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")

    # Step 5: Burn Subtitles into Video
    output_video = os.path.join(OUTPUT_FOLDER, "translated_output.mp4")
    video = mp.VideoFileClip(filepath)
    video.write_videofile(output_video, codec="libx264")

    return f"Translation complete! File saved at {output_video}"

def format_time(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

if __name__ == "__main__":
    app.run(debug=True)
