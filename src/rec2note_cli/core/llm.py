from google import genai

from rec2note_cli.config import get_settings

# client = genai.Client(settings.api_key)

# response = client.models.generate_content(
#     model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
# )
# print(response.text)

if __name__ == "__main__":
    settings = get_settings()

    client = genai.Client(api_key=settings.google_gemini_api_key)

    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
    )
    print(response.text)
