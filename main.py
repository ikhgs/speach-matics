from flask import Flask, request, jsonify
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError
import os

# Charger la clé API depuis une variable d'environnement
API_KEY = os.getenv("API_KEY")
LANGUAGE = "en"

if not API_KEY:
    raise ValueError("API_KEY is not set. Please set the API_KEY environment variable.")

settings = ConnectionSettings(
    url="https://asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Initialisation de l'application Flask
app = Flask(__name__)

@app.route('/api/speechmatics', methods=['POST'])
def transcribe_audio():
    # Récupérer l'URL du fichier audio/vidéo
    audio_url = request.json.get('url')
    if not audio_url:
        return jsonify({"error": "No URL provided"}), 400

    # Paramètres de transcription
    conf = {
        "type": "transcription",
        "transcription_config": {
            "language": LANGUAGE
        }
    }

    try:
        with BatchClient(settings) as client:
            job_id = client.submit_job(
                audio=audio_url,
                transcription_config=conf,
            )
            print(f'job {job_id} submitted successfully, waiting for transcript')

            transcript = client.wait_for_completion(job_id, transcription_format='txt')
            return jsonify({"transcript": transcript})

    except HTTPStatusError as e:
        if e.response.status_code == 401:
            return jsonify({"error": "Invalid API key"}), 401
        elif e.response.status_code == 400:
            return jsonify({"error": e.response.json()['detail']}), 400
        else:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
