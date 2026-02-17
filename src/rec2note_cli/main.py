from app.config import Settings

settings = Settings()

def main():
    print("Hello from rec2note!")
    print(f"Google Gemini API Key: {settings.google_gemini_api_key}")


if __name__ == "__main__":
    main()
