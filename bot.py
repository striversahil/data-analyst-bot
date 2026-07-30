import os
import json
import asyncio
from pathlib import Path
from aiohttp import web
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from dotenv import load_dotenv

from agent import DataAnalystAgent
from logger import JSONLLogger

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_PUBLIC_BASE_URL = os.getenv("LOG_PUBLIC_URL", "https://your-deployed-host.com/logs")
LOG_SERVER_PORT = int(os.getenv("PORT", "8080"))
ENABLE_LOG_SERVER = os.getenv("ENABLE_LOG_SERVER", "false").lower() == "true"


class DataAnalystBot:
    def __init__(self):
        self.logger = None
        self.agent = None
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome = (
            "🤖 Data Analyst Bot\n\n"
            "Send me a data analysis question and I'll reply with a JSON answer.\n\n"
            "Example questions:\n"
            "• Which state has the highest maternal mortality rate based on MOSPI data?\n"
            "• Forecast flow rate for these inputs: [10.5, 20.3, 30.1]\n"
            "• Build a model to forecast flow rate\n\n"
            "I'll reply with exactly one JSON object containing 'answer' and 'log_url'."
        )
        await update.message.reply_text(welcome)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages."""
        if not update.message or not update.message.text:
            return
        
        question = update.message.text.strip()
        chat_id = update.message.chat_id
        
        # Create logger for this run
        self.logger = JSONLLogger("logs")
        await self.logger.__aenter__()
        self.agent = DataAnalystAgent(self.logger)
        
        await self.logger.log("message_received", {
            "chat_id": chat_id,
            "question": question
        })
        
        try:
            # Process question
            answer = await self.agent.analyze(question)
            
            # Get log URL
            log_url = self.logger.get_public_url(LOG_PUBLIC_BASE_URL)
            
            # Final response: EXACTLY one JSON object
            response = {
                "answer": answer,
                "log_url": log_url
            }
            
            await self.logger.log("response_sent", {
                "response": response,
                "chat_id": chat_id
            })
            
            # Close logger
            await self.logger.__aexit__(None, None, None)
            
            # Send ONLY the JSON - nothing else!
            await update.message.reply_text(json.dumps(response))
            
        except Exception as e:
            await self.logger.log("error", {"error": str(e)})
            error_response = {
                "answer": {"error": str(e)},
                "log_url": self.logger.get_public_url(LOG_PUBLIC_BASE_URL)
            }
            await update.message.reply_text(json.dumps(error_response))
            await self.logger.__aexit__(None, None, None)


async def serve_logs(request):
    """Serve log files publicly."""
    filename = request.match_info.get('filename', 'latest.jsonl')
    log_dir = Path("logs")
    
    if filename == "latest.jsonl":
        log_files = sorted(log_dir.glob("run_*.jsonl"))
        if not log_files:
            return web.Response(text="No logs found", status=404)
        file_path = log_files[-1]
    else:
        file_path = log_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        return web.Response(text="Not found", status=404)
    
    try:
        file_path.resolve().relative_to(log_dir.resolve())
    except ValueError:
        return web.Response(text="Forbidden", status=403)
    
    return web.FileResponse(file_path)


def run_bot():
    """Run the bot locally (polling) - synchronous, handles its own event loop."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_from_botfather_here":
        raise ValueError("BOT_TOKEN not set in .env file")
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()
    bot = DataAnalystBot()
    application.add_handler(CommandHandler("start", bot.handle_start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    )
    
    print("🤖 Data Analyst Bot starting...")
    print(f"📝 Logs will be available at: {LOG_PUBLIC_BASE_URL}")
    
    # Run polling - THIS handles its own event loop internally
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def run_deployment():
    """Run bot + log server for deployment (Fly.io, Railway, Render)."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_from_botfather_here":
        raise ValueError("BOT_TOKEN not set in .env file")
    
    # Setup log server
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/logs/{filename}', serve_logs)
    app.router.add_get('/logs', serve_logs)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', LOG_SERVER_PORT)
    await site.start()
    print(f"📂 Log server running on port {LOG_SERVER_PORT}")
    
    # Setup bot
    application = Application.builder().token(BOT_TOKEN).build()
    bot = DataAnalystBot()
    application.add_handler(CommandHandler("start", bot.handle_start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    )
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    print("🤖 Bot + Log server running...")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await runner.cleanup()


def main():
    if ENABLE_LOG_SERVER:
        asyncio.run(run_deployment())
    else:
        # For local testing, run_polling handles its own event loop
        run_bot()


if __name__ == "__main__":
    main()