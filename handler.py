import sys, os, requests, environ, time
from services.scraping import ScrapingService
from services.s3 import S3
from utils import split_start_end

from multiprocessing import Process
from threading import Thread

env = environ.Env()
env.read_env()
s3 = S3()

BACKEND_URL = os.environ['BACKEND_URL'].strip("/")

WORKERS = 4

def run_service(sales_navigator_url, start_page, end_page, extraction_id):
    scraping_service = ScrapingService(sales_navigator_url, start_page, end_page, extraction_id)
    scraping_service.start_scraping()

if __name__ == "__main__":
    extraction_id = sys.argv[1]
    number_of_workers = sys.argv[2] if len(sys.argv) > 2 else WORKERS
    number_of_workers = int(number_of_workers)
    print(f"Extraction ID: {extraction_id}")

    r = requests.get(f"{BACKEND_URL}/extraction/detail/{extraction_id}/")
    if r.status_code != 200:
        print("Error: Extraction not found")
        sys.exit()
    
    data = r.json()
    sales_navigator_url = data["sales_navigator_url"]
    start_page = data["start_page"]
    end_page = data["end_page"]
    print("start_page: ", start_page)
    print("end_page: ", end_page)

    page_offset = (end_page - start_page)/number_of_workers

    start_time = time.time()
    workers = []
    for i, split in enumerate(split_start_end(start_page, end_page, number_of_workers)):
        start = split[0]
        end = split[1]
        print(f"Worker {i}: start_page: {start}, end_page: {end}")
        p = Process(target=run_service, args=(sales_navigator_url, start, end, extraction_id))
        workers.append(p)
        p.start()
    
    for worker in workers:
        worker.join()
    
    total_pages = end_page - start_page + 1
    total_time = round(time.time() - start_time, 2)
    time_per_page = round(total_time/total_pages, 2)
    
    print("All workers finished")
    print(f"Total time: {total_time} seconds for {total_pages} pages")
    print(f"Time per page: {time_per_page} seconds")
    