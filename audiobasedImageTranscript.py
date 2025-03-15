import requests
import re
from translate import Translator
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
import speech_recognition as sr
import threading
import queue

# Translate text to English
def translate_to_english(text, src_lang='en'):
    translator = Translator(from_lang=src_lang, to_lang="en")
    temp = translator.translate(text)
    print(temp)
    return temp

# Extract keywords
def extract_keywords(sentence):
    words = sentence.split()
    stopwords = {'the', 'is', 'and', 'of', 'to', 'in', 'on', 'with', 'a', 'an'}
    return [word for word in words if word.lower() not in stopwords]



def fetch_image(query):
    search_url = f"https://www.google.com/search?tbm=isch&q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    image_urls = re.findall(r"\"(https://encrypted-tbn0\.gstatic\.com/images\?[^\"<>]+)\"", response.text)

    if image_urls:
        img_url = image_urls[0]
        img_response = requests.get(img_url)
        img_response.raise_for_status()
        img = Image.open(BytesIO(img_response.content))
        return img
    return None

# Display images in the main thread
def display_images(image_list):
    cv2.namedWindow("Visual Transcript", cv2.WINDOW_NORMAL)

    for img in image_list:
        if img is None:
            continue
        try:
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (600, 600))
            cv2.imshow("Visual Transcript", img)
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error displaying image: {e}")

    cv2.destroyAllWindows()

# Queue to pass data between threads
image_queue = queue.Queue()

# Listen for audio input
def listen_for_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("Listening for a sentence...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                sentence = recognizer.recognize_google(audio)
                print(f"You said: {sentence}")

                translated = translate_to_english(sentence)
                print(f"Translated: {translated}")

                keywords = extract_keywords(translated)
                print(f"Keywords: {keywords}")

                images = []
                for word in keywords:
                    img = fetch_image(word)
                    if img:
                        images.append(img)
                print(images)
                image_queue.put(images)

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            print("Didn't catch that, try again...")
        except Exception as e:
            print(f"Error: {e}")

# Main loop for GUI
def main():
    listener_thread = threading.Thread(target=listen_for_audio, daemon=True)
    listener_thread.start()

    print("Press 'q' in the image window to quit.")
    while True:
        if not image_queue.empty():
            images = image_queue.get()
            display_images(images)

if __name__ == "__main__":
    main()
