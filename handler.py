import sys, os, requests, environ
from services.scraping import ScrapingService
from services.s3 import S3

from multiprocessing import Process

env = environ.Env()
env.read_env()
s3 = S3()

BACKEND_URL = os.environ['BACKEND_URL'].strip("/")
print(f"Backend URL: {BACKEND_URL}")

WORKERS = 4

def run_service(sales_navigator_url, start_page, end_page, extraction_id):
    scraping_service = ScrapingService(sales_navigator_url, start_page, end_page, extraction_id)
    scraping_service.start_scraping()

if __name__ == "__main__":
    extraction_id = sys.argv[1]
    number_of_workers = sys.argv[2] if len(sys.argv) > 2 else WORKERS
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

    workers = []
    for i in range(number_of_workers):
        start = int(start_page + i*page_offset)
        end = int(start_page + (i+1)*page_offset) - 1
        if i == number_of_workers - 1:
            end = end_page
        print(f"Worker {i}: start_page: {start}, end_page: {end}")
        p = Process(target=run_service, args=(sales_navigator_url, start, end, extraction_id))
        workers.append(p)
        p.start()
    
    for worker in workers:
        worker.join()
    
    print("All workers finished")