import sys, os, csv, requests, environ
from services.scraping import ScrapingService
from services.s3 import S3

env = environ.Env()
env.read_env()

BACKEND_URL = os.environ['BACKEND_URL']
BACKEND_URL = BACKEND_URL.strip("/")
print(f"Backend URL: {BACKEND_URL}")

BUCKET_NAME = "emailer-backend-static"

OUTPUT_UPLOAD_PATH = "extraction_data/{extraction_id}/stage1/output.csv"
OUTPUT_FILE_NAME = "output.csv"

s3 = S3()

if __name__ == "__main__":
    extraction_id = sys.argv[1]
    print(f"Extraction ID: {extraction_id}")

    r = requests.get(f"{BACKEND_URL}/extraction/detail/{extraction_id}/")
    if r.status_code != 200:
        print("Error: Extraction not found")
        sys.exit()
    
    data = r.json()
    sales_navigator_url = data["sales_navigator_url"]
    number_of_contacts = data["number_of_contacts"]

    scraping_service = ScrapingService(sales_navigator_url, number_of_contacts)
    scraping_service.start_scraping()

    s3.upload_object(
        BUCKET_NAME, OUTPUT_UPLOAD_PATH.format(extraction_id=extraction_id), OUTPUT_FILE_NAME
    )
    r = requests.post(
        f"{BACKEND_URL}/extraction/stage1/complete/",
        json={
            "uuid": extraction_id,
            "result_file_url": f"https://{BUCKET_NAME}.s3.amazonaws.com/{OUTPUT_UPLOAD_PATH.format(extraction_id=extraction_id)}"
        }
    )
    print(r.json())


        