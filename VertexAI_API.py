from google import genai

client = genai.Client(
    vertexai=True,
    project="gen-lang-client-0605794434",
    location="asia-northeast1",
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?",
)
print(response.text)
