# 🎨 Media Editor

A professional, web-based media editing platform built with **Django**. This application offers a complete suite of tools for processing both images and videos, featuring a modern user interface and powerful Cloud integration.

## 🚀 Overview

Media Editor simplifies media manipulation by providing an intuitive web interface for complex editing tasks. Whether you need to apply filters to an image, watermark a video, or use AI to enhance your photos, this platform handles it all seamlessly.

### Key Features

#### 🖼️ Image Editing
Comprehensive toolset powered by **Pillow**:
- **Filters & Enhancements**: Grayscale, Invert, Sepia, Brightness, Contrast, Blur, Sharpen.
- **Transform**: Crop (Free & Presets), Rotate (Custom & Quick 90°/180°), Resize.
- **Overlays**: Add Text/Subtitles with custom fonts (Arial, Times, etc.) and PNG Logos.
- **Watermarking**: automated text or image watermarking.

#### 🤖 AI-Powered Editing
- **Google Gemini Integration**: Utilizing the **Nano Banana model** for advanced image generation and editing capabilities.
- Describe your desired checks or edits, and let the AI handle the rest.

#### 🎬 Video Editing
Robust video processing pipeline utilizing **MoviePy**:
- **Transitions & Effects**: Fade In/Out, Grayscale, Color Tint, Artistic Painting effects.
- **Adjustments**: Speed control (Slow 0.5x - Fast 2.0x), Loop, Mirror (Flip H/V).
- **Transform**: Crop, Resize, Rotate.
- **Watermarking**: Add text or image watermarks to your video content.
- **Color Correction**: Adjust Brightness, Contrast, and Intensity.

#### ☁️ Cloud & Storage
- **Cloudinary Integration**: Securely save and host user-edited photos and videos on the cloud.
- **Profile Management**: Each user has a dedicated profile to manage their uploaded and edited content.

## 🛠️ Architecture & Tech Stack

- **Backend**: Python, Django
- **Image Processing**: Pillow (PIL)
- **Video Processing**: MoviePy
- **Task Queue**: Celery (Async video processing)
- **AI Model**: Google Gemini (Nano Banana)
- **Database**: SQLite (Default) / Configurable
- **Frontend**: HTML5, CSS3, JavaScript
- **Storage**: Cloudinary

## ⚙️ Installation & Setup

### Prerequisites

Ensure you have Python 3.8+ installed.

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DNICK.git
   cd DNICK
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: You specifically need `google-genai` and `cloudinary` libraries.*

3. **Environment Configuration**
   
   Create a `.env` file or export the following environment variables:

   **Google Gemini (AI Features)**
   ```bash
   export GOOGLE_API_KEY=your_google_api_key
   ```

   **Cloudinary (Storage)**
   ```bash
   export CLOUDINARY_CLOUD_NAME=your_cloud_name
   export CLOUDINARY_API_KEY=your_api_key
   export CLOUDINARY_API_SECRET=your_api_secret
   ```

4. **Database Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Run the Server**
   ```bash
   python manage.py runserver
   ```
   Access the app at `http://127.0.0.1:8000/`

## 📸 Snapshots

Take a look at the modern user interface:

![Dashboard](editorproject/media/screenshots/Screenshot%202026-01-21%20at%2023.32.53.png)
*Modern Home Dashboard*

![Image Editor](editorproject/media/screenshots/Screenshot%202026-01-21%20at%2023.33.49.png)
*Rich Image Editing Tools*

![AI Editor](editorproject/media/screenshots/Screenshot%202026-01-21%20at%2023.35.33.png)
*AI Integration Panel*

![Profile](editorproject/media/screenshots/Screenshot%202026-01-21%20at%2023.37.21.png)
*Video Processing Interface*

![Video Editor](editorproject/media/screenshots/Screenshot%202026-01-21%20at%2023.35.53.png)
*User Profile & Gallery*

---

© 2026 DNICK Media Editor. All Rights Reserved.

