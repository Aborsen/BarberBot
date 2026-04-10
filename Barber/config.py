import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Snake Mini App settings
SNAKE_WEBAPP_URL = os.getenv("SNAKE_WEBAPP_URL", "https://yourdomain.com/snake_app.html")
SNAKE_API_PORT = int(os.getenv("SNAKE_API_PORT", "8080"))

# xAI / Grok API settings
XAI_BASE_URL = "https://api.x.ai/v1"
VISION_MODEL = "grok-4-1-fast-non-reasoning"

# OpenAI image generation settings
IMAGE_MODEL = "gpt-image-1"
NUM_HAIRSTYLES = 6

# Messages
WELCOME_MESSAGE = (
    "Welcome to the Barber Style AI Bot! \n\n"
    "Send me a clear photo of your face and I'll generate 6 personalized hairstyle options for you.\n\n"
    "Tips for best results:\n"
    "- Good lighting on your face\n"
    "- Front-facing photo\n"
    "- Hair clearly visible"
)

PROCESSING_MESSAGE = (
    "Analyzing your photo and generating 6 hairstyle options... \n"
    "This may take up to a minute."
)

ERROR_MESSAGE = (
    "Sorry, something went wrong while processing your photo. "
    "Please try again with a clear, well-lit photo of your face."
)

NO_FACE_MESSAGE = (
    "I couldn't clearly detect a face in the photo. "
    "Please send a clear, front-facing photo with good lighting."
)
