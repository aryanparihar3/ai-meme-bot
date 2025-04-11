from flask import Flask, render_template, request, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import uuid
import random

app = Flask(__name__)

UNSPLASH_ACCESS_KEY = "3wXRvqV_JolN7kWaCXG5OG0jPa83lOeKyClGaSi0teQ"
search_terms = ["funny", "cat", "meme", "coding", "awkward", "sarcastic"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if "make a meme" in user_message.lower():
        # ✂️ Split for custom caption
        parts = user_message.lower().split("make a meme", 1)[-1].strip()
        
        query = None
        custom_caption = None

        if ":" in parts:
            topic, caption = parts.split(":", 1)
            query = topic.strip() or None
            custom_caption = caption.strip() or None
        else:
            query = parts.strip() or None

        meme_url = generate_meme(query=query, caption=custom_caption)
        if meme_url:
            return jsonify({"reply": f'<img src="{meme_url}" alt="meme" width="300">'})
        else:
            return jsonify({"reply": "⚠️ Failed to generate meme."})
    else:
        return jsonify({"reply": f"You said: {user_message}"})


def generate_meme(query=None, caption=None):
    try:
        if not query:
            query = random.choice(search_terms)

        print(f"🔍 Searching Unsplash for: {query}")
        url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
        response = requests.get(url)
        response.raise_for_status()

        img_url = response.json().get("urls", {}).get("regular")
        if not img_url:
            return None

        img_response = requests.get(img_url)
        img_response.raise_for_status()
        img = Image.open(BytesIO(img_response.content)).convert("RGB")

        width, height = img.size
        new_height = height + 120
        new_img = Image.new("RGB", (width, new_height), color=(255, 255, 255))
        new_img.paste(img, (0, 120))

        draw = ImageDraw.Draw(new_img)

        # Use bold font, larger size
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font = ImageFont.truetype(font_path, size=36)
        except:
            font = ImageFont.load_default()

        # Use custom caption or random fallback
        if not caption:
            caption = random.choice([
                "Debugging: Where the bugs hide in plain sight.",
                "When your AI writes better code than you.",
                "This code works, don't touch it.",
                "99 little bugs in the code... fix one, 127 to go."
            ])

        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]

        # Draw bold white text with black outline
        x = (width - text_width) / 2
        y = 40

        # Black outline
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x + dx, y + dy), caption, font=font, fill="black")

        # White text
        draw.text((x, y), caption, font=font, fill="white")

        # Save the image
        static_dir = os.path.join(os.getcwd(), "static")
        os.makedirs(static_dir, exist_ok=True)

        filename = f"meme_{uuid.uuid4().hex[:8]}.jpg"
        output_path = os.path.join(static_dir, filename)
        new_img.save(output_path)

        return f"/static/{filename}"

    except Exception as e:
        print("❌ Meme generation error:", e)
        return None


if __name__ == "__main__":
    app.run(debug=True)
