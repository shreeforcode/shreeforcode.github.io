import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = "7895221231:AAFXeILdn4UaQfJwA1ZXObwKoafbVQoaHt4"
ALLOWED_USERS = [927207777]  # Add your Telegram user ID

# Paths
BASE_DIR = Path(__file__).resolve().parent
BLOGS_DIR = BASE_DIR / "blogs"
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Valid blog IDs
VALID_BLOGS = [
    "iit-madras",
    "ai-butler",
    "open-source",
    "algorithmic-trading",
    "dropping-out",
    "iitm-nexus",
    "founded-insti"
]

# HTML templates
MICRO_BLOG_TEMPLATE = """
<div class="mb-4">
    <span class="text-sm text-gray-400">{date}</span>
    <p class="mt-2">{content}</p>
</div>
"""

IMAGE_TEMPLATE = """
<div class="mb-4">
    <span class="text-sm text-gray-400">{date}</span>
    <img src="{image_path}" alt="{caption}" class="mt-2 rounded-lg">
    <p class="mt-2">{caption}</p>
</div>
"""

LINK_PREVIEW_TEMPLATE = """
<div class="mb-4">
    <span class="text-sm text-gray-400">{date}</span>
    <a href="{url}" target="_blank" class="block mt-2 p-4 border border-gray-700 rounded-lg hover:bg-gray-800">
        <h4 class="text-blue-400 font-semibold">{title}</h4>
        <p class="text-gray-400 text-sm mt-1">{description}</p>
    </a>
</div>
"""

# Template for new blog
NEW_BLOG_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Shree Pandey</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{
            --bg-color: #000000;
            --text-color: #D1D5DB;
            --accent-color: #3B82F6;
            --hover-color: #60A5FA;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
        }}

        .blog-content img {{
            max-width: 100%;
            height: auto;
            border-radius: 0.5rem;
            margin: 1.5rem 0;
        }}
    </style>
</head>

<body class="min-h-screen text-gray-100">
    <nav class="bg-black/50 backdrop-blur-sm fixed w-full z-50 top-0">
        <div class="container mx-auto px-4 py-3">
            <a href="/" class="text-blue-400 hover:text-blue-300 font-bold">← Back to Home</a>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <header class="mt-16 mb-8">
            <h1 class="text-3xl font-bold text-white mb-2">{title}</h1>
            <div class="flex items-center text-gray-400">
                <span class="mr-4">{date}</span>
                <span>{category}</span>
            </div>
        </header>

        <article class="blog-content prose prose-invert max-w-none">
            <div class="text-gray-300">
                {content}
            </div>

            <!-- Micro Blog Updates Section -->
            <div class="mt-12">
                <h2 class="text-2xl font-bold text-white mb-6">Updates</h2>
                <div class="micro-blog-section">
                    <!-- Micro blog entries will be added here -->
                </div>
            </div>
        </article>
    </div>

    <footer class="text-center text-gray-500 mt-12 pb-8">
        <p>&copy; 2024 Shree Pandey. All rights reserved.</p>
    </footer>
</body>
</html>
"""
