FROM python:3.9

# Install system packages and dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  libfontconfig \
  wget \
  unzip \
  && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN sudo apt-get install google-chrome-stable

# Install ChromeDriver for Selenium
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$(wget -O - -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
RUN ls /usr/local/bin/

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the source code
COPY . .

# Set the entry point
ENTRYPOINT ["python","handler.py"]

