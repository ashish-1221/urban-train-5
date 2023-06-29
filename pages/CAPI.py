from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os
import streamlit as st
import numpy as np
import webbrowser
import os.path
import pickle
import pandas as pd
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tabulate import tabulate


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


class drive_api:

    def main(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        self.self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.self.creds or not self.self.creds.valid:
            if self.self.creds and self.self.creds.expired and self.self.creds.refresh_token:
                self.self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.self.creds = self.flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.self.creds.to_json())

    # Connect to EDM_DB Master folder

    def connect_EDM_DB(self,folder_id='14kxgIm70A7uPmg_XSB1C2I3_3z2YQv9O'):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        try:
            self.service = build('drive', 'v3', credentials=self.self.creds,cache_discovery=False)
            self.folders = {}
            self.page_token = None
            while True:
                self.response = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and parents in '{}'".format(
                    folder_id),
                spaces="drive",
                fields='nextPageToken,'
                'files(id,name,parents)',
                pageToken=self.page_token
            ).execute()
                for self.file in self.response.get('files',[]):
                    print(F'Found file: {self.file.get("name")}, {self.file.get("id")}')
                    self.folders[self.file.get("name")] = {'id':self.file.get("id"),'parent':self.file.get("parents")[0]}
                self.page_token = self.response.get('nextPageToken', None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(f"An error occured:{error}")
            self.folders = None
        return self.folders

    # Function for returning sub_folders info(id,name,parent) inside a  parent folder based on parent_folder_id
    def search_a_folder(self,parent_id):
        if os.path.exists('token.json'):
            self.self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        try:
            self.service = build('drive', 'v3', credentials=self.self.creds,cache_discovery=False)
            self.temp_list = {}
            self.page_token = None
            while True:
                self.response = self.service.files().list(
                    q="mimeType='application/vnd.google-apps.folder' and parents in '{}'".format(
                        parent_id),
                    spaces='drive',
                    fields='nextPageToken,'
                    'files(id,name,parents)',
                    pageToken=self.page_token
                ).execute()
                for self.file in self.response.get('files', []):
                    print(f"\nFiles Found:{self.file.get('name')}")
                    self.temp_list[self.file.get("name")] = {'id':self.file.get("id"),'parents':self.file.get('parents')[0]}
                self.page_token = self.response.get('nextPageToken', None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(F'An Error Occured:{error}', error)
            self.temp_list = None
        return self.temp_list

    


def start_point():
    name = st.text_input("Enter the State Full Name/Abbreviation","")
    return name


def state_name_abbvs(name):
    # Read the csv file containing the name of the states and their respective abbreviations
    state = pd.read_csv(r"data\stateList_abbv.csv")
    for ind in state.index:
        if name.lower() == state['dict'][ind].split("_")[0].lower() or \
            name.upper() == state['dict'][ind].split("_")[1].upper():
            return state['dict'][ind]



st_name = start_point()
state_dict = state_name_abbvs(st_name)

capi  = drive_api()
capi.main()
edm_db_folder = capi.connect_EDM_DB()
folder_name = 'CAPI'
# Taking all the info of CAPI folder in a dictionary
capi_info = {}

for folder_key,folder_info in edm_db_folder.items():
    if folder_key == folder_name:
        capi_info = folder_info
        capi_info['name'] = folder_key
st.write(capi_info)
# Search for subfolder inside a folder and return its info
print(f"\n{capi_info['id']}")
sub_folder = capi.search_a_folder(str(capi_info['id']))
st.write(sub_folder)

