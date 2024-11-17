from aiohttp import web
import logging

logger = logging.getLogger(__name__)

# HTML for the modern status page
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Status</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 0; }
        header { background-color: #1f1f1f; padding: 20px; text-align: center; font-size: 1.5em; color: #ffffff; }
        #log-container { padding: 20px; max-height: 80vh; overflow-y: auto; background-color: #1a1a1a; border: 1px solid #333; }
        footer { text-align: center; padding: 10px; font-size: 0.8em; background-color: #1f1f1f; color: #ffffff; }
    </style>
</head>
<body>
    <header>Discord Bot Status</header>
    <div id="log-container">
        <pre id="log-content">{log}</pre>
    </div>
    <footer>Powered by Render</footer>
    <script>
        const logContainer = document.getElementById("log-container");
        setInterval(() => {
            fetch('/logs').then(response => response.text()).then(data => {
                document.getElementById('log-content').textContent = data;
                logContainer.scrollTop = logContainer.scrollHeight;
            });
        }, 5000); // Fetch logs every 5 seconds
    </script>
</body>
</html>
"""

async def start_http_server(log_buffer):
    app = web.Application()

    async def status_page(request):
        try:
            log_buffer.seek(0)  # Move to the beginning of the buffer
            logs = log_buffer.read()[-10000:]  # Read the last 10,000 characters
            return web.Response(text=HTML_PAGE.format(log=logs), content_type="text/html")
        except Exception as e:
            logger.error(f"Error serving status page: {e}")
            return web.Response(text="An error occurred.", status=500)

    async def fetch_logs(request):
        try:
            log_buffer.seek(0)
            logs = log_buffer.read()[-10000:]
            return web.Response(text=logs, content_type="text/plain")
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return web.Response(text="An error occurred.", status=500)

    app.router.add_get("/", status_page)
    app.router.add_get("/logs", fetch_logs)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("HTTP server running on port 8080.")
