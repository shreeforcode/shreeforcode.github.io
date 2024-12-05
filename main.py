from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import logging
import os
from config import *
from pathlib import Path
import re
from functools import wraps
from typing import Callable
from datetime import datetime
import json

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
AWAITING_IMAGE = 1
AWAITING_CAPTION = 2

# Store temporary user data
user_data_store = {}


def authorized(func: Callable) -> Callable:
    """Decorator to check if user is authorized"""
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            update.message.reply_text(
                "⛔ You are not authorized to use this bot.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def validate_blog_id(blog_id: str) -> bool:
    """Validate if blog ID exists"""
    return blog_id in VALID_BLOGS


def update_blog_file(blog_id: str, new_content: str) -> bool:
    """Update blog file with new content"""
    try:
        file_path = BLOGS_DIR / f"{blog_id}.html"

        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        # Find micro-blog section
        micro_blog_section = soup.find("div", class_="micro-blog-section")
        if not micro_blog_section:
            logger.error(f"Micro-blog section not found in {blog_id}")
            return False

        # Add new content at the top
        micro_blog_section.insert(0, BeautifulSoup(new_content, 'html.parser'))

        # Save updated file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))

        return True
    except Exception as e:
        logger.error(f"Error updating blog file: {str(e)}")
        return False


@authorized
def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when /start is issued."""
    help_text = """
🤖 *Blog Update Bot*

Available commands:
/post blog\-id Your content \- Add a new micro\-blog update
/image blog\-id \- Start process to add image with caption
/link blog\-id url \- Add link with preview
/list \- Show available blog IDs

Available blogs:
""" + "\n".join([f"• `{blog}`" for blog in VALID_BLOGS])

    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)


@authorized
def list_blogs(update: Update, context: CallbackContext) -> None:
    """List available blog IDs"""
    blogs_list = "\n".join([f"• {blog}" for blog in VALID_BLOGS])
    update.message.reply_text(f"Available blogs:\n{blogs_list}")


@authorized
def handle_post(update: Update, context: CallbackContext) -> None:
    """Handle /post command"""
    try:
        # Extract blog_id and content
        parts = update.message.text.split(' ', 2)
        if len(parts) < 3:
            update.message.reply_text("❌ Format: /post blog-id your content")
            return

        blog_id = parts[1]
        content = parts[2]

        if not validate_blog_id(blog_id):
            update.message.reply_text("❌ Invalid blog ID")
            return

        # Create HTML content
        html_content = MICRO_BLOG_TEMPLATE.format(
            date=datetime.now().strftime("%b %d, %Y"),
            content=content
        )

        # Update blog file
        if update_blog_file(blog_id, html_content):
            update.message.reply_text("✅ Blog updated successfully!")
        else:
            update.message.reply_text("❌ Failed to update blog")

    except Exception as e:
        logger.error(f"Error in handle_post: {str(e)}")
        update.message.reply_text(f"❌ Error: {str(e)}")


@authorized
def start_image_upload(update: Update, context: CallbackContext) -> int:
    """Start the image upload process"""
    try:
        # Extract blog_id
        parts = update.message.text.split()
        if len(parts) != 2:
            update.message.reply_text("❌ Format: /image blog-id")
            return ConversationHandler.END

        blog_id = parts[1]

        if not validate_blog_id(blog_id):
            update.message.reply_text("❌ Invalid blog ID")
            return ConversationHandler.END

        # Store blog_id in user data
        user_data_store[update.effective_user.id] = {"blog_id": blog_id}

        update.message.reply_text(
            "📤 Please send the image you want to upload.")
        return AWAITING_IMAGE

    except Exception as e:
        logger.error(f"Error in start_image_upload: {str(e)}")
        update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END


@authorized
def handle_image(update: Update, context: CallbackContext) -> int:
    """Handle image upload"""
    try:
        user_id = update.effective_user.id
        if user_id not in user_data_store:
            update.message.reply_text(
                "❌ Please start over with /image command")
            return ConversationHandler.END

        # Get the largest photo
        photo = update.message.photo[-1]

        # Download and save photo
        file = context.bot.get_file(photo.file_id)
        file_path = IMAGES_DIR / f"{photo.file_id}.jpg"
        file.download(str(file_path))

        # Store file path in user data
        user_data_store[user_id]["image_path"] = str(
            file_path.relative_to(BASE_DIR))

        update.message.reply_text("📝 Please send a caption for the image.")
        return AWAITING_CAPTION

    except Exception as e:
        logger.error(f"Error in handle_image: {str(e)}")
        update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END


@authorized
def handle_caption(update: Update, context: CallbackContext) -> int:
    """Handle image caption and complete the upload"""
    try:
        user_id = update.effective_user.id
        if user_id not in user_data_store:
            update.message.reply_text(
                "❌ Please start over with /image command")
            return ConversationHandler.END

        user_data = user_data_store[user_id]
        caption = update.message.text

        # Create HTML content
        html_content = IMAGE_TEMPLATE.format(
            date=datetime.now().strftime("%b %d, %Y"),
            image_path=user_data["image_path"],
            caption=caption
        )

        # Update blog file
        if update_blog_file(user_data["blog_id"], html_content):
            update.message.reply_text(
                "✅ Image uploaded and blog updated successfully!")
        else:
            update.message.reply_text("❌ Failed to update blog")

        # Clean up user data
        del user_data_store[user_id]
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error in handle_caption: {str(e)}")
        update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END


@authorized
def handle_link(update: Update, context: CallbackContext) -> None:
    """Handle /link command"""
    try:
        # Extract blog_id and URL
        parts = update.message.text.split(' ', 2)
        if len(parts) < 3:
            update.message.reply_text("❌ Format: /link blog-id url")
            return

        blog_id = parts[1]
        url = parts[2]

        if not validate_blog_id(blog_id):
            update.message.reply_text("❌ Invalid blog ID")
            return

        # Fetch page metadata
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else url
        description = (
            soup.find('meta', {'name': 'description'})['content']
            if soup.find('meta', {'name': 'description'})
            else "No description available"
        )

        # Create HTML content
        html_content = LINK_PREVIEW_TEMPLATE.format(
            date=datetime.now().strftime("%b %d, %Y"),
            url=url,
            title=title,
            description=description
        )

        # Update blog file
        if update_blog_file(blog_id, html_content):
            update.message.reply_text("✅ Link preview added successfully!")
        else:
            update.message.reply_text("❌ Failed to update blog")

    except Exception as e:
        logger.error(f"Error in handle_link: {str(e)}")
        update.message.reply_text(f"❌ Error: {str(e)}")


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the current operation"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]

    update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


# States for blog creation
AWAITING_TITLE = 3
AWAITING_CATEGORY = 4
AWAITING_CONTENT = 5


def sanitize_blog_id(title: str) -> str:
    """Convert title to valid blog ID"""
    # Convert to lowercase and replace spaces with hyphens
    blog_id = title.lower().replace(' ', '-')
    # Remove special characters
    blog_id = re.sub(r'[^a-z0-9-]', '', blog_id)
    return blog_id


@authorized
def start_new_blog(update: Update, context: CallbackContext) -> int:
    """Start the process of creating a new blog"""
    update.message.reply_text(
        "Let's create a new blog! First, send me the title of your blog."
    )
    return AWAITING_TITLE


def handle_title(update: Update, context: CallbackContext) -> int:
    """Handle the blog title"""
    title = update.message.text
    user_id = update.effective_user.id

    # Store title and generate blog_id
    blog_id = sanitize_blog_id(title)
    user_data_store[user_id] = {
        "title": title,
        "blog_id": blog_id
    }

    update.message.reply_text(
        f"Great! Blog ID will be: {blog_id}\n\n"
        "Now, send me the category for this blog (e.g., Technology, Experience, Project)"
    )
    return AWAITING_CATEGORY


def handle_category(update: Update, context: CallbackContext) -> int:
    """Handle the blog category"""
    category = update.message.text
    user_id = update.effective_user.id
    user_data_store[user_id]["category"] = category

    update.message.reply_text(
        "Perfect! Now send me the main content of your blog. "
        "You can use basic markdown:\n"
        "*bold text* = **bold**\n"
        "_italic text_ = *italic*\n"
        "`code` = single backticks\n"
        "```code block``` = triple backticks"
    )
    return AWAITING_CONTENT


def handle_content(update: Update, context: CallbackContext) -> int:
    """Handle the blog content and create the blog"""
    try:
        content = update.message.text
        user_id = update.effective_user.id
        user_data = user_data_store[user_id]

        # Convert markdown to HTML
        content_html = convert_markdown_to_html(content)

        # Create new blog file
        blog_html = NEW_BLOG_TEMPLATE.format(
            title=user_data["title"],
            date=datetime.now().strftime("%b %d, %Y"),
            category=user_data["category"],
            content=content_html
        )

        blog_path = BLOGS_DIR / f"{user_data['blog_id']}.html"
        with open(blog_path, 'w', encoding='utf-8') as f:
            f.write(blog_html)

        # Update valid blogs list
        update_valid_blogs(user_data["blog_id"])

        # Update main page to include new blog
        update_main_page(user_data)

        update.message.reply_text(
            f"✅ Blog created successfully!\n\n"
            f"Title: {user_data['title']}\n"
            f"ID: {user_data['blog_id']}\n"
            f"Category: {user_data['category']}\n\n"
            f"You can now use /post, /image, and /link commands with this blog ID."
        )

        # Clean up
        del user_data_store[user_id]
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error creating blog: {str(e)}")
        update.message.reply_text("❌ Failed to create blog. Please try again.")
        return ConversationHandler.END


def convert_markdown_to_html(content: str) -> str:
    """Convert basic markdown to HTML"""
    # Bold
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    # Italic
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    # Code blocks
    content = re.sub(
        r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
    # Inline code
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
    # Paragraphs
    content = '<p>' + content.replace('\n\n', '</p><p>') + '</p>'
    return content


def update_valid_blogs(new_blog_id: str) -> None:
    """Add new blog to valid blogs list"""
    global VALID_BLOGS
    if new_blog_id not in VALID_BLOGS:
        VALID_BLOGS.append(new_blog_id)
        # Optionally save to a file
        with open(BASE_DIR / 'valid_blogs.json', 'w') as f:
            json.dump(VALID_BLOGS, f)


def update_main_page(blog_data: dict) -> None:
    """Update main page with new blog entry"""
    try:
        index_path = BASE_DIR / 'index.html'
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Find the journey section
        journey_section = soup.find('section', id='journey')
        if not journey_section:
            return

        # Create new journey item
        new_item = create_journey_item(blog_data)

        # Add to the beginning of the journey items
        journey_items = journey_section.find('div', class_='space-y-12')
        if journey_items:
            journey_items.insert(0, BeautifulSoup(new_item, 'html.parser'))

        # Save updated index file
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    except Exception as e:
        logger.error(f"Error updating main page: {str(e)}")


def create_journey_item(blog_data: dict) -> str:
    """Create HTML for new journey item"""
    return f"""
    <div class="relative">
        <div class="absolute left-0 top-0">
            <span class="text-sm font-semibold text-blue-400 block">{datetime.now().year}</span>
            <div class="bg-blue-500 rounded-full p-2 mt-1">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                    stroke-linejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
            </div>
        </div>
        <div class="ml-20">
            <h3 class="text-xl font-bold text-white journey-title relative" 
                onclick="window.location.href='/blogs/{blog_data['blog_id']}.html'">
                {blog_data['title']} &#128279;
            </h3>
            <p class="text-gray-300">Category: {blog_data['category']}</p>
        </div>
    </div>
    """


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler for image upload
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('image', start_image_upload)],
        states={
            AWAITING_IMAGE: [MessageHandler(Filters.photo, handle_image)],
            AWAITING_CAPTION: [MessageHandler(Filters.text & ~Filters.command, handle_caption)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    blog_creation_handler = ConversationHandler(
        entry_points=[CommandHandler('newblog', start_new_blog)],
        states={
            AWAITING_TITLE: [MessageHandler(Filters.text & ~Filters.command, handle_title)],
            AWAITING_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, handle_category)],
            AWAITING_CONTENT: [MessageHandler(Filters.text & ~Filters.command, handle_content)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(blog_creation_handler)

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list", list_blogs))
    dp.add_handler(CommandHandler("post", handle_post))
    dp.add_handler(CommandHandler("link", handle_link))
    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop
    updater.idle()


if __name__ == '__main__':
    main()
