import openai
import requests
import os
import time
import speech_recognition as sr
import pygame
import hashlib
import re

# OpenAI API anahtarı
openai.api_key = "open_ai_key" # platform.openai.com in API Key Create (Subscribe the ChatGPT pricing)

# ElevenLabs API bilgileri
ELEVENLABS_API_KEY = "-" # https://elevenlabs.io/app/settings/api-keys 
VOICE_ID = "-"  # https://elevenlabs.io/app/voice-lab (For example Atlas - Global Human Expression)

# Ses dosyalarını saklamak için kullanılan klasör
VOICES_DIR = "voices"

# Ses dosyası saklama klasörü oluşturulması
if not os.path.exists(VOICES_DIR):
    os.makedirs(VOICES_DIR)

# Sesle klasör adı belirleme
def get_code_directory_by_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Klasör adını söyleyin...")
        try:
            audio = recognizer.listen(source, timeout=5)
            folder_name = recognizer.recognize_google(audio, language="tr-TR")
            print(f"Klasör adı algılandı: {folder_name}")
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Klasör oluşturuldu: {folder_name}")
            else:
                print(f"Klasör zaten mevcut: {folder_name}")
            return folder_name
        except sr.WaitTimeoutError:
            print("Klasör adı alınamadı, varsayılan 'developers' klasörü kullanılacak.")
            return "developers"
        except sr.UnknownValueError:
            print("Klasör adı anlaşılamadı, varsayılan 'developers' klasörü kullanılacak.")
            return "developers"

# Metni hash ile eşleştirerek dosya ismi oluşturma
def generate_audio_filename(text):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return os.path.join(VOICES_DIR, f"{text_hash}.mp3")

# ElevenLabs API'den Ses Dönüştürme veya Yerel Kullanım
def convert_or_play_text_to_speech(text):
    audio_file = generate_audio_filename(text)
    
    # Eğer dosya zaten varsa, doğrudan çal
    if os.path.exists(audio_file):
        print(f"Yerel ses dosyası bulunuyor: {audio_file}")
        play_audio(audio_file)
    else:
        print("Ses dosyası oluşturuluyor...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.9
            }
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(audio_file, "wb") as f:
                f.write(response.content)
            print(f"Yeni ses dosyası oluşturuldu ve saklandı: {audio_file}")
            play_audio(audio_file)
        else:
            print("Ses dönüştürme başarısız oldu:", response.status_code, response.text)

# Yerel Ses Dosyası Çalma
def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

# Ses Girişi Alımı
def transcribe_audio_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Dinliyorum...")
        try:
            audio = recognizer.listen(source, timeout=5)
            print("Ses alındı, işleniyor...")
            return recognizer.recognize_google(audio, language="tr-TR")
        except sr.WaitTimeoutError:
            print("Ses alınamadı, lütfen tekrar konuşun.")
        except sr.UnknownValueError:
            print("Ses anlaşılamadı.")
        return None

# ChatGPT'den Yanıt Alımı
def get_chatgpt_response(prompt):
    print("ChatGPT'den yanıt alınıyor...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Dosya uzantısını belirlemek için kod dilini tanıma
def get_language_extension(language):
    language_extensions = {
        "python": "py",
        "javascript": "js",
        "html": "html",
        "css": "css",
        "java": "java",
        "c++": "cpp",
        "c#": "cs",
        "php": "php",
        "ruby": "rb",
        "go": "go",
        "typescript": "ts",
        "bash": "sh"
    }
    return language_extensions.get(language.lower(), "txt")  # Tanınmayan diller için .txt

# Yanıttan Kod Çıkarma ve Kaydetme
def extract_and_save_code(response, directory):
    code_blocks = re.findall(r"```(.*?)\n(.*?)```", response, re.DOTALL)
    if code_blocks:
        for idx, (language, code) in enumerate(code_blocks):
            extension = get_language_extension(language.strip())
            filename = f"generated_code_{idx + 1}.{extension}"
            file_path = os.path.join(directory, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code.strip())
            print(f"Kod dosyası oluşturuldu: {file_path}")

# Dosya Yolu Belirtilen Dosyayı Okuma ve Özetleme
def summarize_file(file_path):
    if not os.path.exists(file_path):
        print(f"Belirtilen dosya bulunamadı: {file_path}")
        convert_or_play_text_to_speech(f"Belirtilen dosya bulunamadı: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        
        print(f"Dosya içeriği okundu: {file_path}")
        # İçeriği özetlemek için ChatGPT'ye gönder
        prompt = f"Bu Python dosyasını analiz et ve neye hitap ettiğini açıklayan bir özet yap:\n\n{file_content}"
        summary = get_chatgpt_response(prompt)
        
        print(f"Dosya Özeti:\n{summary}")
        convert_or_play_text_to_speech(summary)  # Özet seslendirme
    except Exception as e:
        print(f"Dosya okuma veya özetleme sırasında bir hata oluştu: {e}")
        convert_or_play_text_to_speech("Dosya okuma veya özetleme sırasında bir hata oluştu.")

# Sürekli Dinleme Fonksiyonu
def listen_to_user():
    print("Sesli Asistan Başladı. 'Çıkış' diyerek sonlandırabilirsiniz.")
    while True:
        user_input = transcribe_audio_to_text()
        if user_input:
            if "çıkış" in user_input.lower():
                print("Asistan kapatılıyor...")
                break
            
            # Kullanıcı dosya özetleme komutunu verdi mi?
            if "yorumla" in user_input.lower():
                match = re.search(r"(c:[\\/].*?)(\s|$)", user_input, re.IGNORECASE)
                if match:
                    file_path = match.group(1).replace("\\", "/")  # Dosya yolunu düzenle
                    print(f"Belirtilen dosya yolu: {file_path}")
                    summarize_file(file_path)
                    continue
                else:
                    print("Dosya yolu bulunamadı. Lütfen dosya yolunu tam olarak belirtin.")
                    convert_or_play_text_to_speech("Dosya yolu bulunamadı. Lütfen dosya yolunu tam olarak belirtin.")
                    continue
            
            # Normal ChatGPT işlemi
            chatgpt_response = get_chatgpt_response(user_input)
            print(f"Asistan: {chatgpt_response}")
            
            # Kod içeriği varsa kaydet
            if "```" in chatgpt_response:
                directory = get_code_directory_by_voice()
                extract_and_save_code(chatgpt_response, directory)
            
            # Yanıtı seslendir
            convert_or_play_text_to_speech(chatgpt_response)
        time.sleep(1)

# Main Fonksiyonu
def main():
    listen_to_user()

if __name__ == "__main__":
    main()
