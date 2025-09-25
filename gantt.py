import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.font_manager as fm
import numpy as np
from datetime import date
import matplotlib.dates as mdates
import pandas as pd
import io



# Name of Script
st.title('Gantt Chart Generator 📊')  # Replace with your script name

# Instructions
st.subheader("Instructions")
with st.expander("Quick instruction📝"): 
    st.markdown('''
            1. Download Template
            2. Fill in sheet with required information
            3. Drag and drop Gantt excel file to submit
            4. Generate your Gantt chart
            5. Copy and paste the generated image or click download button for higher quality 
            6. Any questions please speak with RJ
            ''')

#Applying font
font_path = "GOTHIC.TTF" #- for the actual script on github
font_prop = fm.FontProperties(fname=font_path)

# Apply the font globally for all plots
plt.rcParams['font.family'] = font_prop.get_name()

st.subheader("Download Template")
# Download a Template:
data = {
            "Group": [1, 2, 3, 3.1, 3.2, 4],
            "Task_Name": ["Ongoing Project Management", "Ongoing Analytical Support", "WP1", "WP1a", "WP1b", "WP2"],
            "Start_Date": ["05/01/2026", "05/01/2026", "05/01/2026", "05/01/2026", "02/02/2026", "09/03/2026"],
            "FTE_Days": [105, 105, 45, 20, 25, 40] ,
            "Completed_FTE_Days": [90, 3, 3, 15, 3, 35],
            "Milestone": ['', '', '', '', '', '']
        }  

excel_template = pd.DataFrame(data) # transformation of the data dictionary to a pandas data frame

excel_file = io.BytesIO() # in-memory binary stream to store the excel file - will be written into a stream rather than a file to be saved on a disk

with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer: # pd.ExcelWriter is a pandas function for converting data into an excel file
    excel_template.to_excel(writer, index=False, sheet_name='Sheet1') # converts the stream file to an excel file


excel_file.seek(0) #  resets pointer back to the beginning

st.download_button(
            label="Download Gantt Chart Template.xlsx ",
            data=excel_file,
            file_name="Gantt_Chart_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )  # Makes it so you can download the excel file with the streamlit widget



#Upload a File
st.subheader("Upload Excel file - Classic Gantt Chart")

file = st.file_uploader("Choose a '.xlsx' File", type = 'xlsx') # streamlit file uploader where the excel type is specified
if file:
    
    #----- Customisation ---------
    
    og = pd.read_excel(file)
    
    st.subheader("Excel Preview")
    st.write("Edit Data or Keep Original")
    df = st.data_editor(og, num_rows="dynamic", hide_index=True)
    
    st.subheader("Modify Gantt Chart Parameters")
    
    with st.container(border=True):
        st.write("Change Figure Size")
        col1, col2 = st.columns([1,1])
                
        with col1:
            width = st.number_input("Input Width:", max_value=100, min_value=0, value=16)  #figsize=(16,6)- Default size
        with col2:
            height = st.number_input("Input Height:", max_value=100, min_value=0, value=6)
            
        with col1:
            size = st.number_input("Input Font Size:", max_value=100, min_value=0, value=15)
    
    with st.container(border=True):
        st.write("Update Colour Scheme (if required)")
                
        variables = []
        df['group'] = np.floor(df['Group']) 
            
        num_variables = st.number_input("Number of Tasks", min_value=1, max_value=20, value=(df["group"].nunique()), step=1)
        default_colours = ['#F991B4', '#FFB379', '#0EC3EB', '#6CF2EC', '#005F78',  '#00ADB2', '#BABAFF', "#8080ff",]
        colour_dict = {}
        
        for i in range(0, num_variables, 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < num_variables:
                    default = default_colours[idx % len(default_colours)]
                    picked = cols[j].color_picker(f'Group {idx+1}', default)
                    colour_dict[idx+1] = picked
        

        
    st.subheader("Gantt Chart")
    
    if st.button("Generate Gantt Chart"):
        with st.container(border=True):
            #---- File Processing -----
            
            df = df.dropna(how="all") # drop any acidental empty rows
            df = df.sort_values(by ="Group", ascending=False) # sort data frame so Gantt chart is presented in the right way
            df["Start_Date"] = pd.to_datetime(df["Start_Date"], format="%d-%m-%Y")

            #----Ordering dataframe----
            # project start date
            proj_start = df.Start_Date.min()

            # caluculating actual end dates from number of days (including the weekend)
            df["Planned_End"] = np.busday_offset(df['Start_Date'].values.astype('datetime64[D]'), df['FTE_Days'] - 1, roll='forward', weekmask='1111100')

            df["Completed_end"] = np.busday_offset(df['Start_Date'].values.astype('datetime64[D]'), df['Completed_FTE_Days'] - 1, roll='forward', weekmask='1111100')

            # Calculating actual days

            df["Planned_days"] = (df["Planned_End"] - df["Start_Date"]).dt.days + 1

            df["Completed_days"] = (df["Completed_end"] - df["Start_Date"]).dt.days + 1

            # days between start and current progression of each task
            df['current_num'] = (df.Planned_days * df.Completed_days)


            #------ Colours for the Gantt Chart--------
            df['group'] = np.floor(df['Group'])

            def color(row):
                #color_dict = {1.0 :'#F991B4', 2.0:'#FFB379', 3.0:'#0EC3EB', 4.0:'#6CF2EC', 5.0:'#005F78', 6.0 : '#00ADB2', 7.0 : '#BABAFF', 8.0: "#8080ff", 9.0: "#FFB379"}
                return colour_dict[row['group']]

            df['color'] = df.apply(color, axis=1)

            
            #st.dataframe(df) #check df
            
            #-------Plotting---------

            fig, ax = plt.subplots(1, figsize=(width,height))

            # bars
            ax.barh(df.Task_Name, df.Completed_days, left=df.Start_Date, color=df.color)
            ax.barh(df.Task_Name, df.Planned_days, left=df.Start_Date, color=df.color, alpha=0.5)
            
            #plotting milestone
            if df["Milestone"].any():
                ax.scatter( df.Milestone, df.Task_Name, facecolors="none", edgecolors="#394042", marker="D", s=150, linewidth=1.5 )
            else: 
                pass
            
            #Labelling
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position('top')
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
            ax.tick_params(axis="both", labelsize=size)
    
            st.pyplot(fig)
            
        gantt_fig = io.BytesIO()
            
        fig.savefig(gantt_fig, format="png", dpi=600, bbox_inches="tight")
            
        st.download_button(
            label="Download Image",
            data=gantt_fig.getvalue(),
            file_name="Gantt_chart.png",
            mime="image/png"
            )






