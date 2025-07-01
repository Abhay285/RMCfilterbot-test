from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.generate import database  # Fixed import
from config import RESULTS_PER_PAGE, MAX_RESULTS, CACHE_TIME
import re

# Search cache for pagination
search_cache = {}

def clean_query(query):
    """Remove special characters from search query"""
    return re.sub(r'[^\w\s]', '', query)

@Client.on_message(filters.command("search"))
async def handle_search(client: Client, message: Message):
    """Handle search requests with pagination"""
    query = message.text.split(" ", 1)
    if len(query) < 2:
        await message.reply("🔍 Please provide a search query after /search command")
        return
    
    query = clean_query(query[1].strip())
    if not query:
        await message.reply("❌ Please enter a valid search term")
        return
    
    # Perform search
    results = list(database.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort("score", -1).limit(MAX_RESULTS))
    
    if not results:
        await message.reply(f"❌ No results found for '{query}'")
        return
    
    # Store results in cache for pagination
    cache_key = f"{message.from_user.id}-{query}"
    search_cache[cache_key] = {
        "results": results,
        "query": query,
        "page": 1
    }
    
    # Show first page
    await show_results_page(client, message, cache_key)

async def show_results_page(client, message, cache_key):
    """Show a page of search results"""
    if cache_key not in search_cache:
        await message.reply("⌛ Search session expired. Please perform a new search")
        return
    
    cache = search_cache[cache_key]
    page = cache["page"]
    results = cache["results"]
    query = cache["query"]
    
    # Calculate pagination
    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    start_idx = (page - 1) * RESULTS_PER_PAGE
    end_idx = min(start_idx + RESULTS_PER_PAGE, len(results))
    
    # Build results message
    response = f"🔍 Search results for '{query}' (Page {page}/{total_pages}):\n\n"
    for i in range(start_idx, end_idx):
        post = results[i]
        caption_preview = post['caption'][:75] + "..." if post['caption'] else "No caption"
        response += f"{i+1}. {caption_preview}\n"
        response += f"   👉 [View Post](https://t.me/c/{post['chat']}/{post['id']})\n\n"
    
    # Build pagination buttons
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{cache_key}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{cache_key}"))
    
    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    
    # Send response
    await message.reply(
        response,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^(prev|next)_(.+)"))
async def handle_pagination(client, callback_query):
    """Handle pagination callback queries"""
    action, cache_key = callback_query.data.split("_", 1)
    cache = search_cache.get(cache_key)
    
    if not cache:
        await callback_query.answer("Session expired. Perform a new search.")
        return
    
    if action == "prev":
        if cache["page"] > 1:
            cache["page"] -= 1
    elif action == "next":
        total_pages = (len(cache["results"]) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
        if cache["page"] < total_pages:
            cache["page"] += 1
    
    await callback_query.answer()
    await show_results_page(client, callback_query.message, cache_key)
    await callback_query.message.delete()

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Welcome message with instructions"""
    welcome = (
        "👋 Welcome to the Post Search Bot!\n\n"
        "🔍 To search for posts, use:\n"
        "`/search query`\n\n"
        "Examples:\n"
        "• `/search python tutorial`\n"
        "• `/search important announcement`\n\n"
        "📚 Use pagination buttons to navigate through results."
    )
    await message.reply(welcome)
