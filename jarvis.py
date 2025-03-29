import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import subprocess
import datetime
import os
import webbrowser
from dotenv import load_dotenv
import pywhatkit
import sys
import time
from pywinauto import Application
import pyautogui

load_dotenv("jarvis.env")

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize engines
engine = pyttsx3.init('sapi5')
engine.setProperty('voice', engine.getProperty('voices')[0].id)
recognizer = sr.Recognizer()

def speak(text):
    """Convert text to speech with error handling"""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Speech error: {e}")

def listen_command():
    """Listen to user command with improved reliability"""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            query = recognizer.recognize_google(audio, language='en-in').lower()
            print(f"You: {query}")
            return query
        except sr.WaitTimeoutError:
            return "none"
        except Exception as e:
            print(f"Recognition error: {e}")
            return "none"

def generate_response(query):
    """Generate AI response with better error handling"""
    try:
        response = model.generate_content(
            query,
            generation_config=genai.GenerationConfig(
                max_output_tokens=100,
                temperature=0.3
            )
        )
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def open_software(software_name):
    """Open applications with improved Edge handling"""
    apps = {
        'chrome': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        'edge': r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe'
    }
    
    websites = {
        'youtube': "https://youtube.com",
        'google': "https://google.com"
    }

    software_name = software_name.lower()
    
    if software_name in apps:
        speak(f"Opening {software_name}")
        if software_name == 'edge':
            # Launch Edge with user data dir for better tab management
            subprocess.Popen([apps[software_name], "--remote-debugging-port=9222"])
        else:
            subprocess.Popen(apps[software_name])
    elif software_name in websites:
        speak(f"Opening {software_name}")
        webbrowser.open(websites[software_name])
    elif 'play' in software_name:
        song = software_name.replace('play', '').strip()
        speak(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)
    else:
        speak(f"Couldn't find {software_name}")

def close_youtube_tab():
    """Reliable YouTube tab closing using multiple methods"""
    try:
        # Method 1: UI Automation
        try:
            app = Application(backend="uia").connect(title_re=".*Microsoft Edge.*", timeout=3)
            edge = app.window(title_re=".*Microsoft Edge.*")
            tabs = edge.child_window(control_type="TabItem").children()
            
            for tab in tabs:
                if "youtube" in tab.window_text().lower():
                    tab.click_input()
                    edge.type_keys("^w")  # Ctrl+W
                    speak("Closed YouTube tab")
                    return True
        except Exception as e:
            print(f"UI Automation failed: {e}")

        # Method 2: Keyboard Shortcuts
        try:
            # Focus on Edge window
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            # Close current tab
            pyautogui.hotkey('ctrl', 'w')
            speak("Closed current tab")
            return True
        except Exception as e:
            print(f"Keyboard method failed: {e}")

        # Method 3: Fallback to closing entire browser
        speak("Couldn't close just the YouTube tab. Closing Edge completely")
        os.system("taskkill /f /im msedge.exe")
        return True
        
    except Exception as e:
        print(f"Close YouTube error: {e}")
        speak("Sorry, I couldn't close YouTube")
        return False

def close_software(software_name):
    """Enhanced software closing with better YouTube handling"""
    processes = {
        'chrome': "chrome.exe",
        'edge': "msedge.exe",
        'notepad': "notepad.exe",
        'calculator': "calc.exe"
    }

    software_name = software_name.lower()
    
    if software_name in processes:
        speak(f"Closing {software_name}")
        os.system(f"taskkill /f /im {processes[software_name]}")
    elif any(keyword in software_name for keyword in ['youtube', 'video']):
        close_youtube_tab()
    else:
        speak(f"Don't know how to close {software_name}")

def listen_for_wake_word():
    """Wake word detection with energy threshold adjustment"""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Waiting for wake word...")
        while True:
            try:
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
                text = recognizer.recognize_google(audio, language='en-in').lower()
                if 'jarvis' in text:
                    speak("Yes sir? How can I help?")
                    return True
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Wake word error: {e}")
                continue

def command_mode():
    """Main command processing loop with improved feedback"""
    while True:
        query = listen_command()
        if query == "none":
            continue
            
        # Exit conditions
        if any(word in query for word in ["stop","goodbye","thankyou"]):
            speak("Goodbye sir! Have a great day!")
            sys.exit()
            
        # Special commands
        if "open" in query:
            target = query.replace("open", "").strip()
            open_software(target)
        elif "close" in query:
            target = query.replace("close", "").strip()
            close_software(target)
        elif "time" in query:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {current_time}")
        else:
            response = generate_response(query)
            print(f"AI: {response}")
            speak(response)

if __name__ == "__main__":
    speak("System initialized and ready")
    while True:
        if listen_for_wake_word():
            command_mode()