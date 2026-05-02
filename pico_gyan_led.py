import os
import subprocess
import json
import time
import serial
import queue
import pvporcupine
import sounddevice as sd
from gpiozero import LED, RGBLED
from gtts import gTTS
from google import genai
from vosk import Model, KaldiRecognizer
from pvrecorder import PvRecorder
from dotenv import load_dotenv

load_dotenv()

# --- IMPORT FACE MODULE ---
try:
    from face import RobotFace
except ImportError:
    print("[ERROR] 'face.py' missing. OLED disabled.")
    RobotFace = None

# --- 1. BRUTE FORCE NETWORK FIX ---
print("[INIT] Checking Network...")
try:
    # This might fail if not root, but that's okay if dhcpcd.conf is set!
    subprocess.run("echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf", shell=True, check=True)
    print("[INIT] DNS forced to 8.8.8.8")
except Exception as e:
    print(f"[WARN] DNS Fix skipped (Permission/Root issue): {e}")

# --- CONFIGURATION ---
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
PICOVOICE_KEY = os.getenv("PICOVOICE_KEY")
MIC_DEVICE_INDEX = 2
WAKE_WORD = 'blueberry' 

# --- HARDWARE SETUP ---
led_white = LED(25)
led_rgb = RGBLED(red=8, green=23, blue=24, active_high=True)

# Start OLED Face
bot_face = None
if RobotFace:
    bot_face = RobotFace()
    bot_face.start()
    
    # --- ADD THIS SPLASH SCREEN CODE ---
    bot_face.set_text("Developed by \n\nVishwas Paliwal \n\nIoT CoE, SIStec")
    bot_face.set_state("BOOTING") 
    # -----------------------------------
# ESP32 UART
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    ser.flush()
    print("[INIT] Serial connection to ESP32 established.")
except Exception as e:
    print(f"[ERROR] Serial failed: {e}")
    ser = None
    led_rgb.color = (1, 0, 0)

# --- AI MODELS ---
print("[INIT] Loading Models...")
client = genai.Client(api_key=GENAI_API_KEY)
v_model = Model("/home/iot-coe-2025/vosk-model-small-en-in-0.4")
rec = KaldiRecognizer(v_model, 16000)

MOVEMENT_KEYWORDS = {
    "dance": "dance", "walk": "walk", "hug": "hug",
    "handshake": "handshake", "tarzan": "tarzan", "stand": "stand",
    "salute": "salute", "swag": "swag", "one leg": "one leg",
    "pick": "pick", "drop": "drop"
}

audio_q = queue.Queue()

def audio_callback(indata, frames, time, status):
    audio_q.put(bytes(indata))

def set_rgb_color(color):
    led_rgb.color = color

def play_audio(text):
    if not text: return
    print(f"[BOT] {text}")
    
    # VISUALS: Speaking Mode
    if bot_face: 
        bot_face.set_text(text)
        bot_face.set_state("SPEAKING")
    set_rgb_color((0, 1, 0))
    
    clean_text = text.replace("*", "").replace('"', '').strip()

    try:
        tts = gTTS(text=clean_text, lang='en', tld='co.in')
        tts.save("response.mp3")
        subprocess.run(['mpg123', '-q', 'response.mp3'])
    except Exception as e:
        print(f"Cloud Voice Failed: {e}. Switching to Festival.")
        try:
            with open("tts_backup.txt", "w") as f:
                f.write(clean_text)
            subprocess.run(['festival', '--tts', 'tts_backup.txt'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.STDOUT)
        except Exception as festival_err:
            print(f"Audio Failed: {festival_err}")
            set_rgb_color((1, 0, 0))
            time.sleep(1)

    led_rgb.off()
    led_white.on()
    if bot_face: bot_face.set_state("IDLE")

def send_to_esp32(cmd):
    if ser:
        ser.write(f"{cmd}\n".encode('utf-8'))
        print(f"[UART] Sent to ESP32: {cmd}")
    else:
        set_rgb_color((1, 0, 0)) 

def get_gemini_reply(text):
    # VISUALS: Processing Mode
    if bot_face:
        bot_face.set_text(text)
        bot_face.set_state("PROCESSING")
        
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=text,
            config={'system_instruction': "You are a helpful robot. Be concise."}
        )
        return response.text
    except:
        set_rgb_color((1, 0, 0))
        return "I cannot reach the internet."

def smart_listen():
    print("[LISTENING] ...")
    set_rgb_color((0, 0, 1))
    
    # VISUALS: Listening Mode
    if bot_face: bot_face.set_state("LISTENING")
    
    os.system('speaker-test -t sine -f 800 -l 1 > /dev/null 2>&1 & sleep 0.1 && pkill -9 speaker-test')
    
    rec.Reset()
    text_heard = ""
    
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                           channels=1, callback=audio_callback):
        start_time = time.time()
        while True:
            data = audio_q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text_heard = res.get("text", "")
                if text_heard: break 
            if time.time() - start_time > 10: break
    
    led_rgb.off()
    return text_heard

def main():
    porcupine = pvporcupine.create(access_key=PICOVOICE_KEY, keywords=[WAKE_WORD])
    try:
        recorder = PvRecorder(device_index=MIC_DEVICE_INDEX, frame_length=porcupine.frame_length)
    except RuntimeError:
        print(f"[CRITICAL] PvRecorder failed on Index {MIC_DEVICE_INDEX}. Check mic connection.")
        exit(1)
        
    print(f"\n--- ROBOT READY ---")
    led_white.on()
    if bot_face: bot_face.set_state("IDLE")
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            if porcupine.process(pcm) >= 0:
                print("\n[WAKE WORD DETECTED]")
                recorder.stop()
                
                command_text = smart_listen()
                
                if command_text:
                    print(f">>> YOU SAID: {command_text}")
                    
                    is_movement = False
                    for key, esp_cmd in MOVEMENT_KEYWORDS.items():
                        if key in command_text.lower():
                            play_audio(f"Okay, {key}")
                            send_to_esp32(esp_cmd)
                            is_movement = True
                            break
                    
                    if not is_movement:
                        reply = get_gemini_reply(command_text)
                        play_audio(reply)
                
                print(f"\n[WAITING] Say '{WAKE_WORD.upper()}'...")
                if bot_face: bot_face.set_state("IDLE")
                recorder.start()
                
    except KeyboardInterrupt:
        print("\nShutting down...")
        if bot_face: bot_face.stop()
        led_white.off()
        led_rgb.off()
    finally:
        recorder.stop()
        porcupine.delete()
        recorder.delete()

if __name__ == '__main__':
    main()