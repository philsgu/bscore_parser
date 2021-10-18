import streamlit as st
import pandas as pd
import re
import pdfplumber as pf
import time 
import plotly.express as px
from random import randint


choice = st.sidebar.selectbox("Please select", ("Home", "USMLE/COMLEX"))

if 'key' not in st.session_state:
    st.session_state.key = str(randint(1000, 100000000))

if choice == "Home":
  local_time = time.localtime() 
  time_string = time.strftime("%m/%d/%Y", local_time)

  f"""
  # EXTRACT AAMC ERAS BOARD SCORES
  This beta web app is intended for U.S. residency programs to quickly determine TOTAL FAIL attempts on either USMLE
  or COMLEX board examinations.  Unfortunately, current ERAS only posts PASS board scores into the applicant's
  viewable profile dashboard as means to reduce any biases.  It is up to the reviewer however to click on the applicant's
  files section to download and view further of any FAIL attempts that is not readily shown.  This can be labarious and 
  presents challenges to the program when applicant pools are in the thousands. 

  Please consider this as a tool to guage the program's applicant pool but NOT as means to determine final outcome to 
  interview and ranking decisions.

  &#8594Select from the **left menu option** USMLE/COMLEX to parse PDF(s). 
  #
  ### What does the Web App do? 
  Allows residency programs to upload Board PDFs and receive CSV file output of Fails
  ### Is my data safe? 
  Yes, it is a front end web app without any server sided data collection.  Allows upload, parse, and download sequentially
  ### How is this Web App useful?
  Sole purpose is to reduce burden of manually counting from PDFs any Fail attempts by residency programs
  ### Is there a guarantee that the Web App is 100% accurate in parsing the PDFs? 
  No, the Web App is only a tool and it is up to the program/individual to cross check the CSV output for any inaccuracies
  ### Is this free? 
  Yes, no strings attached.  Developed by a physician involved in resident recruitment.  
  ### Will there be any updates?
  Based on changes in USMLE/COMLEX reporting PDF formats, parsing techniques will need to be adjusted.  
  #
  #
  Developed and created by [Phillip Kim, MD, MPH](https://www.doximity.com/pub/phillip-kim-md-8dccc4e4)  \nFor documentation 
  and contribution details are at [GitHub Repository](https://github.com/philsgu/bscore_parser.git)  \nLast update: {time_string}
  """
 

if choice == "USMLE/COMLEX":
  """
  # USMLE/COMLEX Parser
  This is a beta web app to upload and receive in CSV file for total FAILS per applicant. Please NOTE that no data is saved into any cloud platforms and it is at your discretion to save output file locally.
  
  ### Step 1
  Log into [ERAS PDWS](https://auth.aamc.org/account/#/login?gotoUrl=http:%2F%2Fpdws.aamc.org%2Feras-pdws-web%2F). 
  ### Step 2
  **View Current Results**  &#8594 check **Select Page**  &#8594 at bottom **Action to perform on selected applicants** select **View/Print Application**
  NOTE:  ERAS only allows 100 applicants at a time for bulk PDF requests
  ### Step 3
  Select **USMLE Transcript** and/or **COMLEX Transcript**  &#8594 checkbox **Print each application to a separate PDF**  &#8594 type in **Print Job name**  &#8594 click **Request Print**
  ### Step 4 
  In submenu, click **Bulk Print Requests**  &#8594 select <print job name> in Files once Status shows COMPLETE and download to local drive
  ### Step 5
  Locate downloaded zipped folder and decompress to a specified location    
  ### Step 6
  """


  @st.cache
  def convert_df(df):
    # IMPORTANT:  Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

  #parse out AAMC ID
  def find_num(text):
      num = re.findall(r'[0-9]+', text)
      return "".join(num)
  
    
  upload_files = st.file_uploader("Choose PDF files to upload (Shift-Click for multiples)", accept_multiple_files=True, type=['pdf'], key=st.session_state.key)
  st.write('Total files uploaded: ' + str(len(upload_files)))
  # for f in upload_files: 
  #   st.write(str(f).split(','))

  #look for duplicate files
  duplicates = [str(dfile).split(',')[1] for dfile in upload_files]
  if len (duplicates) != len(set(duplicates)):
    st.warning(f"Duplicate file(s) {set(duplicates)} uploaded. ERROR in analysis will be encountered!")

  

  if upload_files is not None:
    
    df = pd.DataFrame(columns = ['Applicant ID', 'Total USMLE Fails', 'Total COMLEX Fails'])
    status = []

    if st.button ("Analyze") and len(upload_files) > 0:
      latest_iteration = st.text('hang on...')
      my_bar = st.progress(0)
      for percent_complete in range(100):
        time.sleep(0.05)
        latest_iteration.text(f'{percent_complete + 1}%')
        my_bar.progress(percent_complete + 1)

      for file in upload_files: 
        with pf.open(file) as pdf:
          page = pdf.pages[0]
          text = page.chars[0]
          text_data = page.extract_text()
          comlex_fail = re.compile(r'Fail\s\d{2}/\d{2}/\d{4}')
          usmle_fail = re.compile(r'\d{2}/\d{2}/\d{4}\s+\bFail\b')
          if "COMLEX-USA" in text_data:
              ctext_list = text_data.split('COMLEX-USA')
              #print(text_list[0])
              cfail_list = comlex_fail.findall(text_data)
              if cfail_list:
                df = df.append({'Applicant ID': ctext_list[0], 'Total COMLEX Fails': len(cfail_list)}, ignore_index=True)   
          elif "USMLE" in text_data: 
              utext_list = text_data.split('USMLE')
              ufail_list = usmle_fail.findall(text_data)
              if ufail_list:
                df = df.append({'Applicant ID': utext_list[0], 'Total USMLE Fails': len(ufail_list)}, ignore_index=True)
          else:
              status.append(str(file))

      csv = convert_df(df)
      if not df.empty: 
         #df.drop_duplicates(keep=False, inplace=True)
        aamc_id = df['Applicant ID'].apply(lambda x: find_num(x))
        df.insert(1, "AAMC ID", aamc_id)

        st.markdown(f"Total applicants with 1 or more FAILED USMLE/COMLEX attempts: **{str(df.shape[0])}**")

        usmle_histo = px.histogram(
          df, x=['Total USMLE Fails', 'Total COMLEX Fails'], cumulative=False, 
          labels={
          "value": "Fail Attempts",
          "variable": "Types"
          },
          title = 'USMLE/COMLEX',
        )
        usmle_histo.update_xaxes(type='category')
        usmle_histo.update_layout(title_x=0.5)
        st.plotly_chart(usmle_histo)
        
        st.download_button(
          label='Download CSV file', 
          data = csv, 
          mime='text/csv', 
          file_name ='failed_applicants.csv'
          )
      else:
        st.markdown(f"Total applicants with 1 or more FAILED USMLE/COMLEX attempts: **{str(df.shape[0])}**")
    
    if status:
      st.warning(f'The following PDFs were deemed indeterminate: {status}') 

    
      
  if st.button('Clear Uploaded File(s)', help='click twice to clear ALL'):
    for key in st.session_state.keys():
        del st.session_state[key] 
        
  #st.session_state






