import csv
import os
import pathlib
import requests
import shutil
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
import zipfile

def download_file(session, url, save_path):
    response = session.get(url, stream=True)
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def extract_file(zip_file_path, extract_folder_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder_path)

url = input("Please enter Financial Statements URL From https://market.sec.or.th/public/idisc/th/FinancialReport/ALL \n: ")
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

folder_path = pathlib.Path('./downloads')
folder_path.mkdir(parents=True, exist_ok=True)

error_files = []  # to store list of error files
file_status = []  # to store list of all files and their status

with requests.Session() as session:
    for link in tqdm(soup.find_all('a'), desc='Downloading zip files', unit='file'):
        href = link.get('href')
        if href.endswith('.zip'):
            zip_url = urljoin(url, href)  # construct full URL

            save_name = os.path.basename(os.path.dirname(zip_url))
            # Extract year and month from the string
            year = save_name[:4]
            month = save_name[4:]

            # Calculate the quarter - 1Q
            quarter = (int(month) - 1) // 3

            # Handle the case when quarter is 0
            if quarter == 0:
                quarter = "Year"
                year = str(int(year) - 1)
            else:
                quarter = "Q" + str(quarter)

            save_name = year + '_' + str(quarter)
            save_path = folder_path / (save_name + '.zip')

            # Download the file
            try:
                download_file(session, zip_url, save_path)
                file_status.append({'File': str(save_path), 'Status': 'OK'})
                
                # Extract the file
                extract_folder_path = folder_path / save_name
                extract_file(save_path, extract_folder_path)
                
            except Exception as e:
                error_files.append(str(save_path))
                file_status.append({'File': str(save_path), 'Status': 'Error'})

# print report of error files
if error_files:
    print("Error extracting the following files:")
    for file in error_files:
        print(file)

# save list of all files and their status in CSV file
csv_file = folder_path / 'file_status.csv'
with open(csv_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['File', 'Status'])
    writer.writeheader()
    writer.writerows(file_status)

# Delete all zip files from the download folder
for file in folder_path.glob('*.zip'):
    os.remove(file)
    
# Zip the downloads folder
zip_file_path = pathlib.Path('./downloads.zip')
shutil.make_archive(zip_file_path.stem, 'zip', folder_path)
print('Zip folder done !!')
