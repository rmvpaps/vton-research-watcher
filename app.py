import os
# MUST be set before any 'transformers' related imports
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1' # Good practice to include this too
from shared import RateLimiterFactory,settings
import gradio as gr
import asyncio
import logging
from processor import ProcessingService
from scraper import scraperService
logger = logging.getLogger("ArxivData Processor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
import os
import queue

class QueueLogHandler(logging.Handler):
    """Custom logging handler that routes logs directly into a thread-safe Queue."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        # Format the log message nicely
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

log_queue_w1 = queue.Queue()
log_queue_w2 = queue.Queue()
# Configure the root or a specific logger
logger = logging.getLogger("ml_pipeline_scraper")
logger.setLevel(logging.INFO)

logger2 = logging.getLogger("ml_pipeline_processor")
logger2.setLevel(logging.INFO)

# Create a clean format for our "terminal" console
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
queue_handler1 = QueueLogHandler(log_queue_w1)
queue_handler1.setFormatter(formatter)
logger.addHandler(queue_handler1)

queue_handler2 = QueueLogHandler(log_queue_w2)
queue_handler2.setFormatter(formatter)
logger2.addHandler(queue_handler2)

async def process_new_batch(progress=gr.Progress()):

    log_history = "--- Process Batch session Started ---\n"
    yield log_history  
    logger2.info("Logger for processor setup")


    while not log_queue_w2.empty():
        try: log_queue_w2.get_nowait()
        except queue.Empty: break

    def log_progress_callback(iterable, desc=None):
        for item in progress.tqdm(iterable, desc=desc):
            # Right before handing control back to the loop, flush all current logs to UI
            nonlocal log_history
            while not log_queue_w2.empty():
                log_history += log_queue_w2.get_nowait() + "\n"
            yield log_history 
            yield item

    path = settings.embedding_path
    print(f"Checking path: {path}")
    if os.path.exists(path):
        print(f"Directory exists! Contents: {os.listdir(path)}")
    else:
        print(f"DIRECTORY MISSING. Current workdir ({os.getcwd()}) contents: {os.listdir('.')}")
        raise Exception("Missing models")
    ratelim = RateLimiterFactory.get_rate_limiter('delay',delay=settings.scrape_delay_seconds)
        
    service = ProcessingService(ratelim)
    await  service.fetch_next_batch_and_process(progress_callback=log_progress_callback)
    # Final log flush
    while not log_queue_w2.empty():
        log_history += log_queue_w2.get_nowait() + "\n"
    yield log_history


def stream_logs_to_console():
    log_history = "--- Scraper Session Started ---\n"
    yield log_history

    while not log_queue_w1.empty():
        try: log_queue_w1.get_nowait()
        except queue.Empty: break


    logger.info("Logger for scraper setup!")


    # Every Gradio event runs on a worker. We can just loop and look at the queue.
    # We poll the queue dynamically. When the parallel pipeline event finishes, 
    # this generator loop will naturally exit because Gradio stops the worker group.
    while True:
        new_logs = False
        while not log_queue_w1.empty():
            log_history += log_queue_w1.get_nowait() + "\n"
            new_logs = True
        if new_logs:
            yield log_history
        if "--- SCRAPER EXECUTION COMPLETED ---" in log_history:
            break
        import time
        time.sleep(0.1)

    while not log_queue_w1.empty():
        try: log_queue_w1.get_nowait()
        except queue.Empty: break


async def scrape_new_batch(progress=gr.Progress()):


    ratelim = RateLimiterFactory.get_rate_limiter('delay',delay=settings.scrape_delay_seconds)
    
    service = scraperService(ratelim)
    await  service.run()
    logger.info("--- SCRAPER EXECUTION COMPLETED ---") 
    return f"✨ PIPELINE SUCCESS!\nProcessed: "

# --- GRADIO INTERFACE LAYOUT ---
with gr.Blocks(title="ML Pipeline Control Center") as demo:
    gr.Markdown("# 🎛️ ML Pipeline Background Worker Control Center")
    gr.Markdown("Click a button to manually run the pipeline stage for  a batch, or trigger them via cron calls.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Worker 1 (Scraper)")
            btn1 = gr.Button("🚀 Run Worker 1 Batch", variant="primary")
            #out1 = gr.Textbox(label="Worker 1 Log Status")
            log_console1 = gr.Code(
                label="Live Log Console (Python standard logging)", 
                language="python", # Python styling gives nice green/blue syntax highlights to logs
                lines=12,
                max_lines=20
            )
            # Exposes API name for cron job: /api/trigger_w1
            btn1.click(fn=scrape_new_batch, outputs=[log_console1], api_name="trigger_w1")
            btn1.click(fn=strea, outputs=[log_console1], api_name="trigger_w1")
            
        with gr.Column():
            gr.Markdown("### Worker 2 (Processor)")
            btn2 = gr.Button("🧠 Run Worker 2 Batch", variant="secondary")
            #out2 = gr.Textbox(label="Worker 2 Log Status")
            log_console2 = gr.Code(
                label="Live Log Console (Python standard logging)", 
                language="python", # Python styling gives nice green/blue syntax highlights to logs
                lines=12,
                max_lines=20
            )
            # Exposes API name for cron job: /api/trigger_w2
            btn2.click(fn=process_new_batch, outputs=[log_console2], api_name="trigger_w2")


if __name__ == "__main__":
  demo.queue()
  demo.launch()