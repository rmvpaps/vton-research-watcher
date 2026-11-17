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
import os
import queue
from functools import partial

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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



# Create a clean format for our "terminal" console
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
queue_handler1 = QueueLogHandler(log_queue_w1)
queue_handler1.setFormatter(formatter)
logger1 = logging.getLogger("scraper")
logger1.addHandler(queue_handler1)
logger1.propagate = False

queue_handler2 = QueueLogHandler(log_queue_w2)
queue_handler2.setFormatter(formatter)
logger2 = logging.getLogger("processor")
logger2.addHandler(queue_handler2)
logger2.propagate = False



async def run_and_stream_alt(taskName,progress=gr.Progress(track_tqdm=True)):
    myq = None
    mylogger=None
    if taskName == "scrape":
        myq = log_queue_w1
        mylogger = logger1
    else:
       myq = log_queue_w2
       mylogger = logger2

    # 1. Clear stale logs
    while not myq.empty():
        try:
            myq.get_nowait()
        except queue.Empty:
            break

    log_history = f"--- {taskName} Session Started ---\n"
    yield f"Running {taskName}...", log_history

    mylogger.info(f"Logger for {taskName} setup!")
    if taskName == "scrape":

        ratelim = RateLimiterFactory.get_rate_limiter(
            "delay", delay=settings.scrape_delay_seconds
        )
        service = scraperService(ratelim)

        # 2. Run the async scraper in the background on the same event loop
        task = asyncio.create_task(service.run(pbar_flag=True))



    else:

        path = settings.embedding_path
        print(f"Checking path: {path}")
        if os.path.exists(path):
            print(f"Directory exists! Contents: {os.listdir(path)}")
        else:
            print(f"DIRECTORY MISSING. Current workdir ({os.getcwd()}) contents: {os.listdir('.')}")
            raise Exception("Missing models")
        ratelim = RateLimiterFactory.get_rate_limiter('delay',delay=settings.scrape_delay_seconds)
            
        service = ProcessingService(ratelim)
        task = asyncio.create_task(service.fetch_next_batch_and_process())


    # 3. Stream logs live while the task is running
    while not task.done():
        new_logs = False
        while not myq.empty():
            record = myq.get_nowait()
            # QueueHandler puts LogRecord objects unless formatted; handle both
            msg = record.getMessage() if hasattr(record, "getMessage") else str(record)
            log_history += msg + "\n"
            new_logs = True

        if new_logs:
            yield f"Running {taskName}...", log_history

        await asyncio.sleep(0.1)  # Non-blocking sleep!

    # 4. Await task to propagate any exceptions & flush remaining logs
    await task
    mylogger.info(f"--- {taskName} EXECUTION COMPLETED ---")

    while not myq.empty():
        record = myq.get_nowait()
        msg = record.getMessage() if hasattr(record, "getMessage") else str(record)
        log_history += msg + "\n"

    yield f"{taskName} PIPELINE SUCCESS!", log_history



# --- GRADIO INTERFACE LAYOUT ---
with gr.Blocks(title="ML Pipeline Control Center") as demo:
    gr.Markdown("# 🎛️ ML Pipeline Background Worker Control Center")
    gr.Markdown("Click a button to manually run the pipeline stage for  a batch, or trigger them via cron calls.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Worker 1 (Scraper)")
            btn1 = gr.Button("🚀 Run Worker 1 Batch", variant="primary")
            out1 = gr.Textbox(label="Worker 1 Log Status")
            log_console1 = gr.Code(
                label="Live Log Console (Python standard logging)", 
                language="python", # Python styling gives nice green/blue syntax highlights to logs
                lines=12,
                max_lines=20
            )
            # Exposes API name for cron job: /api/trigger_w1
            # btn1.click(fn=scrape_new_batch, outputs=[out1], api_name="trigger_w1")
            # btn1.click(fn=stream_logs_to_console, outputs=[log_console1], api_name="trigger_w1")
            btn1.click(
                #fn=run_and_stream_w1,
                fn=partial(run_and_stream_alt,taskName="scrape"),
                outputs=[out1, log_console1],
                api_name="trigger_w1",
                show_progress_on=out1,
            )
            
        with gr.Column():
            gr.Markdown("### Worker 2 (Processor)")
            btn2 = gr.Button("🧠 Run Worker 2 Batch", variant="secondary")
            out2 = gr.Textbox(label="Worker 2 Log Status")
            log_console2 = gr.Code(
                label="Live Log Console (Python standard logging)", 
                language="python", # Python styling gives nice green/blue syntax highlights to logs
                lines=12,
                max_lines=20
            )
            # Exposes API name for cron job: /api/trigger_w2
            btn2.click(
                #fn=run_and_stream_w2, 
                fn=partial(run_and_stream_alt,taskName="process"),
                outputs=[out2,log_console2], 
                api_name="trigger_w2",
                show_progress_on=out2,
                )


if __name__ == "__main__":
  demo.queue()
  demo.launch()