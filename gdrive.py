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
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
from dataclasses import dataclass
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']


def get_dataframe(s_id):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json',SCOPES)
    service = build('sheets','v4',credentials=creds)
    range_name = 'Sheet1'
    result = service.spreadsheets().values().get(spreadsheetId=s_id,range=range_name).execute()
    rows = result.get('values')
    df = pd.DataFrame(rows[1:],columns=rows[0])
    
    return df


    
def build_spreadsheet(s_id):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(
            'token.json', SCOPES)
    SAMPLE_RANGE_NAME = 'A1:AA1000'
    service = build('sheets','v4',credentials=creds)
    # calling the sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId = s_id,range= SAMPLE_RANGE_NAME).execute()
    values_input =result_input.get('values',[])
    if not values_input:
        print('No data found.')


def Export_Data_To_Sheets(s_id,df):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(
            'token.json', SCOPES)
    SAMPLE_RANGE_NAME = 'Sheet1'
    service = build('sheets','v4',credentials=creds)
    response_date = service.spreadsheets().values().update(
        spreadsheetId=s_id,
        valueInputOption='RAW',
        range=SAMPLE_RANGE_NAME,
        body=dict(
            majorDimension='ROWS',
            values=df.T.reset_index().T.values.tolist())
    ).execute()
    print('Sheet successfully Updated')
        
def write_dataframe(s_id,df):
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(
            'token.json', SCOPES)
    SAMPLE_RANGE_NAME = 'A1:AA1000'
    service = build('sheets','v4',credentials=creds)
    response_data = service.spreadsheets().values().update(
        spreadsheetId = s_id,
        valueInputOption = 'RAW',
        range = SAMPLE_RANGE_NAME,
        body = dict(
            majorDimension = 'ROWS',
            values = df.T.reset_index().T.values.tolist())
        ).execute()
    print('Successfully Updated')
    

# Function to download a specific file and store in a specific path based on fileinfo
# StandAlone FUnction to prevent redownloading again and again
@st.cache_data
def export_the_file(fileinfo, folder_path):
    print(f"\n\n{fileinfo}")
    if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
    try:
            service = build('drive', 'v3', credentials=creds)
            request = service.files(
            ).get_media(fileId=fileinfo['id'])
            file_path = folder_path+"/"+fileinfo['name']
            with open(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download %d%%." % int(status.progress()*100))
    except HttpError as error:
            print(f"An Error Occured:{error}")
            st.info(error)
    # Return the dataframe after reading the file
    if '.xlsx' in fileinfo['name']:
            df = pd.read_excel(file_path)
            return df
    if '.csv' in fileinfo['name']:
            df = pd.read_csv(file_path)
            return df




class drive_api:

    def __init__(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = self.flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
    def __reduce__(self):
        return drive_api           
    # Connect to EDM_DB Master folder
    def connect_EDM_DB(self, folder_id='14kxgIm70A7uPmg_XSB1C2I3_3z2YQv9O'):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        try:
            self.service = build(
                'drive', 'v3', credentials=self.creds, cache_discovery=False)
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
                for self.file in self.response.get('files', []):
                    print(
                        F'Found file: {self.file.get("name")}, {self.file.get("id")}')
                    self.folders[self.file.get("name")] = {'id': self.file.get(
                        "id"), 'parent': self.file.get("parents")[0]}
                self.page_token = self.response.get('nextPageToken', None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(f"An error occured:{error}")
            self.folders = None
        return self.folders

    # Function for returning sub_folders info(id,name,parent) inside a  parent folder based on parent_folder_id
    def search_a_folder(self, parents_id):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        try:
            self.service = build(
                'drive', 'v3', credentials=self.creds, cache_discovery=False)
            self.temp_list = []
            self.page_token = None
            while True:
                self.response = self.service.files().list(
                    q="mimeType='application/vnd.google-apps.folder' and parents in '{}'".format(
                        parents_id),
                    spaces='drive',
                    fields='nextPageToken,'
                    'files(id,name,parents)',
                    pageToken=self.page_token
                ).execute()
                for self.file in self.response.get('files', []):
                    print(f"\nFiles Found:{self.file.get('name')}")
                    self.temp_list.append({'name':self.file.get("name"),'id': self.file.get(
                        "id"), 'parents': self.file.get('parents')[0]})
                self.page_token = self.response.get('nextPageToken', None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(F'An Error Occured:{error}', error)
            st.write(f'{error}')
            self.temp_list = None
        return self.temp_list
    # Finction to search a folder based on query parameters
    #@st.cache_data(persist="disk")
    def search_a_folder_q_param(self,query_parameters):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        try:
            self.service = build(
                'drive', 'v3', credentials=self.creds, cache_discovery=False)
            self.temp_list = []
            self.page_token = None
            while True:
                self.response = self.service.files().list(
                    q=query_parameters,
                    spaces='drive',
                    fields='nextPageToken,'
                    'files(id,name,parents,webViewLink)',
                    pageToken=self.page_token
                ).execute()
                for self.file in self.response.get('files', []):
                    print(f"\nFiles Found:{self.file.get('name')}")
                    self.temp_list.append({'name': self.file.get("name"), 'id': self.file.get(
                        "id"), 'parents': self.file.get('parents')[0],'webViewLink':self.file.get('webViewLink')})
                self.page_token = self.response.get('nextPageToken', None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(F'An Error Occured:{error}', error)
            st.write(f'{error}')
            self.temp_list = None
        return self.temp_list
    
    
    # Function to download a specific file and store in a specific path based on fileinfo
    @st.cache_data(persist=True)
    def export_a_file(self,fileinfo,folder_path):
        print(f"\n\n{fileinfo}")
        # if os.path.exists('token.json'):
        #     self.creds = Credentials.from_authorized_user_file('token.json',SCOPES)
        try:
            self.service = build('drive','v3',credentials=self.creds)
            self.request = self.service.files().get_media(fileId=fileinfo['id'])
            self.file_path = folder_path+"/"+fileinfo['name']
            with open(self.file_path, 'wb') as fh:
                self.downloader = MediaIoBaseDownload(fh, self.request)
                self.done = False
                while self.done is False:
                    self.status, self.done = self.downloader.next_chunk()
                    print("Download %d%%." %int(self.status.progress()*100))
        except HttpError as error:
            print(f"An Error Occured:{error}")
            st.info(error)
        # Return the dataframe after reading the file
        if '.xlsx' in fileinfo['name']:
            df = pd.read_excel(self.file_path)
            return df
        if '.csv' in fileinfo['name']:
            df = pd.read_csv(self.file_path)
            return df
            
    # Function to download all files inside a folder based on file_id
    @st.cache_data(show_spinner=True,persist=True)
    def export_all_files(self,folder_id,folder_path):
        # if os.path.exists('token.json'):
        #     self.creds = Credentials.from_authorized_user_file(
        #         'token.json', SCOPES)
        try:
            self.service = build(
                'drive', 'v3', credentials=self.creds, cache_discovery=False)
            self.temp_list = []
            self.page_token = None
            # Get all the files present in the folder
            while True:
                self.responses = self.service.files().list(
                    q=f"'{folder_id}' in parents and mimeType!='application/vnd.google-apps.folder'",
                    pageSize = 1000,
                    fields = "nextPageToken,files(id,name)",
                    pageToken =  self.page_token
                ).execute()
                self.items =  self.responses.get('files',[])
                
                if not self.items:
                    print("No Files Found in the Folder")
                else:
                    for self.item in self.items:
                        print(f"{self.item['name'],{self.item['id']}}")
                        
                        self.file_id = self.item['id']
                        
                        self.request = self.service.files().get_media(fileId=self.file_id)
                        
                        self.file_path = folder_path+"/"+self.item['name']
                        with open(self.file_path,'wb') as fh:
                            self.downloader = MediaIoBaseDownload(fh,self.request)
                            self.done = False
                            while self.done is False:
                                self.status,self.done = self.downloader.next_chunk()
                                print("Download %d%%."% int(self.status.progress()*100))
                self.page_token = self.responses.get('nextPageToken',None)
                if self.page_token is None:
                    break
        except HttpError as error:
            print(f"An Error Occured:{error}")
         
        
               
                
    # Function to read a spread sheet file using file Id and returning a pandas dataframe
    
                        
            