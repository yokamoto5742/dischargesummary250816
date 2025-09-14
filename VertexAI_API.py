from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project='gen-lang-client-0605794434',
    location='global',
    http_options=types.HttpOptions(api_version='v1')
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?",
)
print(response.text)
