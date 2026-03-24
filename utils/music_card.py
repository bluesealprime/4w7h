from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
import io
import datetime
from typing import Optional

class MusicCard:
    def __init__(self):
        # Using workspace fonts
        try:
            self.title_font = ImageFont.truetype("e:/Imp/Boogey/games/assets/HelveticaNeuBold.ttf", 34)
            self.artist_font = ImageFont.truetype("e:/Imp/Boogey/games/assets/HelveticaNeuBold.ttf", 24)
            self.source_font = ImageFont.truetype("e:/Imp/Boogey/games/assets/ClearSans-Bold.ttf", 16)
            self.duration_font = ImageFont.truetype("e:/Imp/Boogey/games/assets/ClearSans-Bold.ttf", 18)
            self.brand_font = ImageFont.truetype("e:/Imp/Boogey/games/assets/ClearSans-Bold.ttf", 14)
        except:
            self.title_font = ImageFont.load_default()
            self.artist_font = ImageFont.load_default()
            self.source_font = ImageFont.load_default()
            self.duration_font = ImageFont.load_default()
            self.brand_font = ImageFont.load_default()

    async def generate(self, track_title: str, artist: str, artwork_url: Optional[str], duration_ms: int, position_ms: int, source: str, guild_name: str = "Discord Server"):
        width, height = 780, 260
        margin = 30
        artwork_size = 180

        # Create base canvas
        canvas = Image.new("RGBA", (width, height), (26, 31, 53, 255))
        
        # 1. Background (Artwork blurred)
        if artwork_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(artwork_url) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        artwork = Image.open(io.BytesIO(img_data)).convert("RGBA")
                        
                        # Scale and blur background
                        bg = artwork.resize((int(width*1.2), int(height*1.2)))
                        bg = bg.filter(ImageFilter.GaussianBlur(10))
                        
                        # Center crop
                        bg_x = (bg.width - width) // 2
                        bg_y = (bg.height - height) // 2
                        bg = bg.crop((bg_x, bg_y, bg_x + width, bg_y + height))
                        
                        canvas.paste(bg, (0,0))
                        
                        # Dark overlay
                        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 166))
                        canvas = Image.alpha_composite(canvas, overlay)
                    else:
                        artwork = None
        else:
            artwork = None

        draw = ImageDraw.Draw(canvas)

        # 2. Draw Artwork on the left
        artwork_x, artwork_y = margin, margin
        if artwork:
            # Round the corners of the artwork
            artwork_thumb = artwork.resize((artwork_size, artwork_size))
            mask = Image.new("L", (artwork_size, artwork_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, artwork_size, artwork_size), radius=18, fill=255)
            
            # Add a slight shadow/glow for the artwork
            canvas.paste(artwork_thumb, (artwork_x, artwork_y), mask)
            
            # Border for artwork
            draw.rounded_rectangle((artwork_x-1, artwork_y-1, artwork_x+artwork_size+1, artwork_y+artwork_size+1), radius=19, outline=(180, 200, 220, 102), width=2)
        else:
            # Frosted glass placeholder
            draw.rounded_rectangle((artwork_x, artwork_y, artwork_x + artwork_size, artwork_y + artwork_size), radius=18, fill=(30, 40, 60, 102), outline=(180, 200, 220, 102))

        # 3. Information Section
        info_x = artwork_x + artwork_size + 30
        content_width = width - info_x - margin
        current_y = artwork_y + 15

        # Source
        draw.text((info_x, current_y), f"Playing from {source}", font=self.source_font, fill=(160, 176, 192, 255))
        current_y += 30

        # Title (Truncated)
        title_text = track_title if len(track_title) < 30 else track_title[:27] + "..."
        draw.text((info_x, current_y), title_text, font=self.title_font, fill=(255, 255, 255, 255))
        current_y += 45

        # Artist
        artist_text = artist if len(artist) < 35 else artist[:32] + "..."
        draw.text((info_x, current_y), artist_text, font=self.artist_font, fill=(224, 232, 240, 255))
        current_y += 40

        # Progress bar
        def format_duration(ms):
            s = int(ms / 1000)
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            if h > 0: return f"{h}:{m:02}:{s:02}"
            return f"{m}:{s:02}"

        progress = position_ms / duration_ms if duration_ms > 0 else 0
        currentTime = format_duration(position_ms)
        totalTime = "LIVE" if duration_ms <= 0 else format_duration(duration_ms)
        
        draw.text((info_x, current_y), f"{currentTime} / {totalTime}", font=self.duration_font, fill=(160, 176, 192, 255))
        
        # Simple progress bar line
        pb_y = current_y + 30
        pb_width = content_width - 20
        pb_height = 6
        draw.rounded_rectangle((info_x, pb_y, info_x + pb_width, pb_y + pb_height), radius=3, fill=(30, 40, 60, 255))
        if progress > 0:
            draw.rounded_rectangle((info_x, pb_y, info_x + int(pb_width * progress), pb_y + pb_height), radius=3, fill=(100, 180, 255, 255))

        # 4. Branding (acp.xz)
        brand_text = "acp.xz"
        draw.text((width - margin - 60, height - margin - 5), brand_text, font=self.brand_font, fill=(224, 232, 240, 255))

        # Convert canvas to bytes
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
