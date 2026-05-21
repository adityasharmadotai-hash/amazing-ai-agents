"""
recorder.py — Real-time browser microphone recording via Streamlit HTML component.

Uses the browser's MediaRecorder API (WebRTC) to record audio directly
in the browser, encode it as WebM/Opus, and pass the base64 bytes back
to Python via Streamlit's component value mechanism.
"""

import base64
import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────────────────────────────────────────
# The recorder component HTML/JS
# ─────────────────────────────────────────────────────────────────────────────

RECORDER_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; font-family: Inter, sans-serif; }
  body { background: transparent; padding: 4px; }

  #recorder-wrap {
    background: linear-gradient(135deg, #1e1b4b, #1e3a5f);
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
  }

  /* Mic button */
  #mic-btn {
    width: 72px; height: 72px; border-radius: 50%;
    border: none; cursor: pointer; font-size: 28px;
    transition: all 0.25s ease;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    box-shadow: 0 0 0 8px rgba(99,102,241,0.18), 0 6px 20px rgba(99,102,241,0.45);
    color: white; display: flex; align-items: center;
    justify-content: center; margin: 0 auto 12px;
  }
  #mic-btn:hover { transform: scale(1.07); }
  #mic-btn.recording {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    box-shadow: 0 0 0 12px rgba(239,68,68,0.2), 0 6px 20px rgba(239,68,68,0.5);
    animation: rec-pulse 1s infinite;
  }
  @keyframes rec-pulse {
    0%, 100% { box-shadow: 0 0 0 12px rgba(239,68,68,0.2), 0 6px 20px rgba(239,68,68,0.5); }
    50%       { box-shadow: 0 0 0 20px rgba(239,68,68,0.08), 0 6px 28px rgba(239,68,68,0.6); }
  }

  #status {
    color: #94a3b8; font-size: 13px; font-weight: 500;
    min-height: 20px; margin-bottom: 10px;
  }
  #status.active { color: #f87171; font-weight: 700; }
  #status.done   { color: #4ade80; font-weight: 700; }

  /* Timer */
  #timer {
    font-size: 24px; font-weight: 800; color: white;
    font-variant-numeric: tabular-nums;
    min-height: 32px; letter-spacing: 2px;
    margin-bottom: 8px;
  }

  /* Waveform bars */
  #waveform {
    display: flex; align-items: flex-end; justify-content: center;
    gap: 3px; height: 36px; margin-bottom: 12px;
    visibility: hidden;
  }
  .bar {
    width: 4px; background: #818cf8; border-radius: 2px;
    animation: wave 0.8s ease infinite;
    min-height: 4px;
  }
  .bar:nth-child(1) { animation-delay: 0s; }
  .bar:nth-child(2) { animation-delay: 0.1s; }
  .bar:nth-child(3) { animation-delay: 0.2s; }
  .bar:nth-child(4) { animation-delay: 0.3s; }
  .bar:nth-child(5) { animation-delay: 0.4s; }
  .bar:nth-child(6) { animation-delay: 0.3s; }
  .bar:nth-child(7) { animation-delay: 0.2s; }
  .bar:nth-child(8) { animation-delay: 0.1s; }
  .bar:nth-child(9) { animation-delay: 0s; }
  @keyframes wave {
    0%, 100% { height: 6px; }
    50%       { height: 26px; }
  }

  /* Send button */
  #send-btn {
    display: none;
    width: 100%; padding: 10px 0; border: none; border-radius: 10px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; font-size: 14px; font-weight: 700;
    cursor: pointer; margin-top: 8px;
    transition: opacity 0.2s;
  }
  #send-btn:hover { opacity: 0.9; }

  /* Audio playback */
  #playback { display: none; margin-top: 10px; }
  #playback audio { width: 100%; border-radius: 8px; }

  /* Permission error */
  #perm-err {
    display: none;
    background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px;
    padding: 10px 14px; font-size: 12px; color: #dc2626;
    margin-top: 8px; text-align: left;
  }

  /* Hint text */
  .hint { color: #64748b; font-size: 12px; margin-top: 4px; }
</style>
</head>
<body>
<div id="recorder-wrap">
  <div id="waveform">
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
  </div>

  <button id="mic-btn">🎙️</button>
  <div id="timer"></div>
  <div id="status">Click to start recording</div>

  <div id="playback">
    <audio id="audio-player" controls></audio>
  </div>

  <button id="send-btn">📤 Send to ARIA</button>
  <div id="perm-err">
    🚫 Microphone access denied.<br>
    Please allow microphone access in your browser and refresh.
  </div>
  <div class="hint">Supports Chrome · Edge · Firefox · Safari</div>
</div>

<script>
  let mediaRecorder = null;
  let audioChunks   = [];
  let timerInterval = null;
  let secondsElapsed = 0;
  let audioBlob = null;

  const micBtn   = document.getElementById('mic-btn');
  const statusEl = document.getElementById('status');
  const timerEl  = document.getElementById('timer');
  const waveform = document.getElementById('waveform');
  const sendBtn  = document.getElementById('send-btn');
  const playback = document.getElementById('playback');
  const audioEl  = document.getElementById('audio-player');
  const permErr  = document.getElementById('perm-err');

  function formatTime(s) {
    const m = Math.floor(s / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return m + ':' + sec;
  }

  function startTimer() {
    secondsElapsed = 0;
    timerEl.textContent = '00:00';
    timerInterval = setInterval(() => {
      secondsElapsed++;
      timerEl.textContent = formatTime(secondsElapsed);
      // Auto-stop at 5 minutes
      if (secondsElapsed >= 300) stopRecording();
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
  }

  async function startRecording() {
    permErr.style.display = 'none';
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
      });

      // Prefer webm/opus, fall back to whatever browser supports
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/ogg') ? 'audio/ogg'
        : '';

      mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      audioChunks = [];

      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });

        // Show playback
        const url = URL.createObjectURL(audioBlob);
        audioEl.src = url;
        playback.style.display = 'block';
        sendBtn.style.display  = 'block';
        waveform.style.visibility = 'hidden';
      };

      mediaRecorder.start(100); // collect every 100ms

      micBtn.classList.add('recording');
      micBtn.textContent  = '⏹';
      statusEl.textContent = 'Recording... click to stop';
      statusEl.className   = 'active';
      waveform.style.visibility = 'visible';
      playback.style.display    = 'none';
      sendBtn.style.display     = 'none';

      startTimer();

    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        permErr.style.display = 'block';
        statusEl.textContent  = 'Microphone access denied';
      } else {
        statusEl.textContent = 'Error: ' + err.message;
      }
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      stopTimer();
      micBtn.classList.remove('recording');
      micBtn.textContent   = '🎙️';
      statusEl.textContent = '✅ Recording saved — preview below';
      statusEl.className   = 'done';
      timerEl.textContent  = formatTime(secondsElapsed) + ' recorded';
    }
  }

  micBtn.addEventListener('click', () => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      startRecording();
    } else {
      stopRecording();
    }
  });

  sendBtn.addEventListener('click', async () => {
    if (!audioBlob) return;
    sendBtn.disabled    = true;
    sendBtn.textContent = '⏳ Processing...';
    statusEl.textContent = 'Sending to ARIA...';

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1];
      const ext = audioBlob.type.includes('ogg') ? '.ogg' : '.webm';
      // Send to Streamlit via component value
      window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: { audio_b64: base64, ext: ext, duration: secondsElapsed }
      }, '*');
      sendBtn.textContent = '✅ Sent!';
      statusEl.textContent = 'Sent to ARIA — check the chat!';
    };
    reader.readAsDataURL(audioBlob);
  });
</script>
</body>
</html>
"""


def mic_recorder(key: str = "mic_recorder", height: int = 340) -> dict | None:
    """
    Render the microphone recorder component.
    Returns dict {"audio_b64": "...", "ext": ".webm", "duration": 12}
    when the user clicks Send, or None if not yet recorded.
    """
    result = components.html(
        RECORDER_HTML,
        height=height,
        scrolling=False,
    )
    return result


def decode_recording(result: dict) -> tuple[bytes, str]:
    """
    Decode the component result into (audio_bytes, file_extension).
    """
    if not result or not isinstance(result, dict):
        return b"", ".webm"
    b64 = result.get("audio_b64", "")
    ext = result.get("ext", ".webm")
    if not b64:
        return b"", ext
    try:
        return base64.b64decode(b64), ext
    except Exception:
        return b"", ext
