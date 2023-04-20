import requests, asyncio, aiohttp, nameparser, time
from utils import format_name, fetch, add_to_file

class EmailVerify:
    def __init__(self, linkedin_data, extraction_id):
        self.linkedin_data = linkedin_data
        self.extraction_id = extraction_id

        self.company_names = []
        self.company_domains = {}

        self.verified_emails = []
    
    async def verify_using_abstactapi(self, email):
        url = f"https://emailvalidation.abstractapi.com/v1/?api_key=41645272c9a44a8aba470447449d231f&email={email}"
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task( fetch(url, session) )
            await asyncio.gather(task)
            task_result = task.result()
            return task_result
        # response = requests.get()
        # if response.status_code != 200:
        #     raise Exception("Error in email verification")
        # return response.json()

    async def get_company_domains(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for company in self.company_names:
                url = f'https://autocomplete.clearbit.com/v1/companies/suggest?query={company}'
                tasks.append(
                    asyncio.create_task( fetch(url, session), name=company )
                )
            await asyncio.gather(*tasks)
            for task in tasks:
                company_name = task.get_name()
                task_results = task.result()
                if task_results and len(task_results) > 0:
                    company_domain = task_results[0]["domain"]
                    self.company_domains[company_name] = company_domain

    def process_data(self):
        self.company_names = [ data_item["Company"] for data_item in self.linkedin_data if data_item["Company"] ]
        start_time = time.time()
        asyncio.run(self.get_company_domains())
        print("It took %s seconds to get all company domains" % (time.time() - start_time))
        print("company domains: ", self.company_domains)

        for data_item in self.linkedin_data:
            name = data_item["Name"]
            company_name = data_item["Company"]
            if not name or not company_name:
                continue
            
            person_name = nameparser.HumanName(name)
            first_name = format_name(person_name.first)
            middle_name = format_name(person_name.middle)
            last_name = format_name(person_name.last)
            company_domain = self.company_domains.get(company_name)

            if not first_name or not last_name:
                print(f"First name or last name not found for {name}")
                continue

            if not company_domain:
                print(f"Company domain not found for {company_name} in self.company_domains")
                continue
            
            # According to priority
            email_combinations = [
                f"{first_name}.{last_name}@{company_domain}",
                f"{first_name}@{company_domain}",
                f"{first_name}{last_name}@{company_domain}",
                f"{first_name[0]}{last_name}@{company_domain}",
                f"{first_name}{last_name[0]}@{company_domain}",
                f"{first_name[0]}.{last_name}@{company_domain}",
                f"{first_name}.{last_name[0]}@{company_domain}",
            ]

            for email in email_combinations:
                email_verification_result = asyncio.run(self.verify_using_abstactapi(email))
                # print("email_verification_result: ", email_verification_result)
                print("checking email: ", [first_name, last_name, company_domain, email, email_verification_result["deliverability"]])
                if email_verification_result["is_catchall_email"]["value"]:
                    print("email is catchall, skipping")
                    break
                if email_verification_result["deliverability"] == "DELIVERABLE":
                    print("email is verified, adding to output file: ", email)
                    add_to_file(f'{self.extraction_id}_emails.csv', name, email)
                    self.verified_emails.append(email)
                    break
            
        print("verified emails: ", self.verified_emails)
                

            
        
        

