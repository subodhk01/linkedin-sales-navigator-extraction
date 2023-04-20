import sys, os, csv, requests, environ
from services.scraping import ScrapingService
from services.s3 import S3

env = environ.Env()
env.read_env()

BACKEND_URL = os.environ['BACKEND_URL']
BACKEND_URL = BACKEND_URL.strip("/")
print(f"Backend URL: {BACKEND_URL}")

BUCKET_NAME = "emailer-backend-static"

OUTPUT_UPLOAD_PATH = "linkedin_data/{extraction_id}/output-{start_page}-to-{end_page}.csv"
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
    start_page = data["start_page"]
    end_page = data["end_page"]
    print("start_page: ", start_page)
    print("end_page: ", end_page)

    scraping_service = ScrapingService(sales_navigator_url, start_page, end_page, extraction_id)
    scraping_service.start_scraping()

    # output_path = OUTPUT_UPLOAD_PATH.format(
    #     extraction_id=extraction_id,
    #     start_page=start_page,
    #     end_page=end_page
    # )

    # s3.upload_object(
    #     BUCKET_NAME, output_path, "output.csv"
    # )
    # r = requests.post(
    #     f"{BACKEND_URL}/extraction/stage1/complete/",
    #     json={
    #         "uuid": extraction_id,
    #         "result_file_url": f"https://{BUCKET_NAME}.s3.amazonaws.com/{output_path}"
    #     }
    # )
    # print(r.json())


        