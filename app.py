import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import os
import re
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Medical Report Analyzer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize encryption
if 'encryption_key' not in st.session_state:
    st.session_state.encryption_key = Fernet.generate_key()
cipher_suite = Fernet(st.session_state.encryption_key)

# Sidebar for file upload and settings
with st.sidebar:
    st.title("Medical Report Analyzer")
    st.image("https://cdn-icons-png.flaticon.com/512/2771/2771388.png", width=100)
    
    uploaded_files = st.file_uploader(
        "Upload Medical Reports", 
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    st.subheader("Analysis Settings")
    time_range = st.slider(
        "Time Range (months)",
        min_value=1,
        max_value=24,
        value=12
    )
    
    specialty_filter = st.selectbox(
        "Filter by Specialty",
        ["All", "Cardiology", "Radiology", "Endocrinology", "General Medicine", "Dental"]
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app helps analyze medical reports by:")
    st.markdown("- Extracting health parameters")
    st.markdown("- Visualizing trends over time")
    st.markdown("- Providing AI-powered summaries")
    st.markdown("- Identifying potential health alerts")

# Main content area
st.title("Medical Report Analysis Dashboard")

if uploaded_files:
    all_data = []
    document_tags = {}
    
    for uploaded_file in uploaded_files:
        # Encrypt and save the uploaded file
        encrypted_content = cipher_suite.encrypt(uploaded_file.getvalue())
        file_ext = uploaded_file.name.split('.')[-1]
        temp_filename = f"temp_{datetime.now().timestamp()}.{file_ext}"
        
        with open(temp_filename, "wb") as f:
            f.write(cipher_suite.decrypt(encrypted_content))
        
        # Tag documents
        with st.expander(f"Tag {uploaded_file.name}"):
            tags = st.multiselect(
                f"Select tags for {uploaded_file.name}",
                ["Cardiology", "Dental", "Lab Results", "Prescription", "Radiology"],
                key=f"tags_{uploaded_file.name}"
            )
            document_tags[uploaded_file.name] = tags
        
        # Process PDF files
        if file_ext.lower() == 'pdf':
            from langchain_community.document_loaders import PyPDFLoader
            pdf_loader = PyPDFLoader(temp_filename)
            pdf_docs = pdf_loader.load()
            
            # Extract health parameters
            def extract_health_parameters(text):
                # Corrected regex pattern with proper escaping and balanced parentheses
                pattern = r'\b(hemoglobin|glucose|CRP|blood\s?pressure|cholesterol|WBC|RBC|HbA1c)\b[\s:]*([\d.]+)(?:\s*(?:mg\/dL|g\/dL|mmol\/L|%|mmHg))?'
                try:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    return [(param.lower().replace(' ', '_'), float(value)) for param, value in matches]
                except Exception as e:
                    st.error(f"Error extracting parameters: {str(e)}")
                    return []
            
            for doc in pdf_docs:
                text = doc.page_content
                extracted_data = extract_health_parameters(text)
                date = datetime.now().strftime("%Y-%m-%d")  # In real use, extract from document
                all_data.extend([(date, param, float(value), uploaded_file.name) for param, value in extracted_data])
        
        # Process image files (OCR)
        elif file_ext.lower() in ['png', 'jpg', 'jpeg']:
            try:
                text = pytesseract.image_to_string(Image.open(temp_filename))
                def extract_health_parameters(text):
                    pattern = r"(\b(?:hemoglobin|glucose|CRP|blood pressure|cholesterol|WBC|RBC|HbA1c)\b)[\s:]*([\d.]+)(?:\s*(?:mg/dL|g/dL|mmol/L|%)?"
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    return matches
                
                extracted_data = extract_health_parameters(text)
                date = datetime.now().strftime("%Y-%m-%d")  # In real use, extract from document
                all_data.extend([(date, param, float(value), uploaded_file.name) for param, value in extracted_data])
                
                # Store OCR results
                if 'ocr_results' not in st.session_state:
                    st.session_state.ocr_results = {}
                st.session_state.ocr_results[uploaded_file.name] = text
            except Exception as e:
                st.error(f"Error processing image {uploaded_file.name}: {str(e)}")
        
        # Clean up
        os.remove(temp_filename)
    
    if all_data:
        df = pd.DataFrame(all_data, columns=["Date", "Parameter", "Value", "Source"])
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", "Trend Analysis", "AI Summary", "Search Records", "Document Timeline"
        ])
        
        with tab1:
            st.header("Report Overview")
            
            # Display basic stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Parameters Extracted", len(df))
            with col2:
                st.metric("Unique Parameters", df["Parameter"].nunique())
            with col3:
                st.metric("Documents Processed", len(uploaded_files))
            
            # Show extracted parameters with source
            st.subheader("Extracted Health Parameters")
            st.dataframe(df, use_container_width=True)
            
            # Reference ranges and alerts
            st.subheader("Parameter Reference Ranges")
            reference_ranges = {
                "hemoglobin": (12.0, 17.0),  # g/dL
                "glucose": (70, 100),  # mg/dL
                "CRP": (0, 10),  # mg/L
                "blood pressure": (90, 120),  # systolic
                "cholesterol": (0, 200),  # mg/dL
                "wbc": (4.5, 11.0),  # 10^3/μL
                "rbc": (4.5, 5.9),  # million/μL
                "hba1c": (4.0, 5.6)  # %
            }
            
            st.table(pd.DataFrame.from_dict(reference_ranges, orient='index', columns=['Min', 'Max']))
            
            # Check for alerts
            def check_for_alerts(row):
                parameter = row["Parameter"].lower()
                value = row["Value"]
                
                if parameter in reference_ranges:
                    min_val, max_val = reference_ranges[parameter]
                    if value < min_val or value > max_val:
                        return f"ALERT: {parameter} out of range! Value: {value}, Normal Range: ({min_val}, {max_val})"
                return None
            
            alerts = df.apply(check_for_alerts, axis=1)
            alerts = alerts.dropna()
            
            if not alerts.empty:
                st.warning("Health Alerts Detected!")
                for alert in alerts:
                    st.error(alert)
            else:
                st.success("No critical alerts detected")
        
        with tab2:
            st.header("Parameter Trends Over Time")
            
            # Parameter selection
            selected_param = st.selectbox(
                "Select Parameter to Visualize",
                df["Parameter"].unique()
            )
            
            # Filter data for selected parameter
            param_data = df[df["Parameter"].str.lower() == selected_param.lower()]
            
            if not param_data.empty:
                # Create interactive plot with Plotly
                fig = px.line(
                    param_data, 
                    x="Date", 
                    y="Value", 
                    color="Source",
                    title=f"{selected_param} Level Over Time",
                    markers=True,
                    hover_data={"Value": ":.2f"}
                )
                
                # Add reference range if available
                if selected_param.lower() in reference_ranges:
                    min_val, max_val = reference_ranges[selected_param.lower()]
                    fig.add_hline(
                        y=min_val, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text=f"Min Normal ({min_val})"
                    )
                    fig.add_hline(
                        y=max_val, 
                        line_dash="dash", 
                        line_color="green",
                        annotation_text=f"Max Normal ({max_val})"
                    )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title=f"{selected_param} Level",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show statistics
                st.subheader(f"{selected_param} Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Highest Value", round(param_data["Value"].max(), 2))
                with col2:
                    st.metric("Lowest Value", round(param_data["Value"].min(), 2))
                with col3:
                    st.metric("Average Value", round(param_data["Value"].mean(), 2))
            else:
                st.warning(f"No data available for {selected_param}")
        
        with tab3:
            st.header("AI-Powered Report Summary")
            
            # Let user select which document to summarize
            doc_to_summarize = st.selectbox(
                "Select document to analyze",
                [f.name for f in uploaded_files]
            )
            
            # Generate summary using LLM
            if st.button("Generate Summary"):
                with st.spinner("Analyzing report with AI..."):
                    from langchain_community.llms import LlamaCpp
                    from langchain.prompts import PromptTemplate
                    from langchain.chains import LLMChain
                    
                    llm = LlamaCpp(
                        model_path="llama-2-7b.Q4_K_M.gguf",
                        temperature=0.1,
                        n_ctx=2048
                    )
                    
                    # Get content based on file type
                    if doc_to_summarize.endswith('.pdf'):
                        pdf_loader = PyPDFLoader(doc_to_summarize)
                        content = pdf_loader.load()[0].page_content
                    else:
                        content = st.session_state.ocr_results.get(doc_to_summarize, "")
                    
                    if not content:
                        st.error("No content available for summarization")
                    else:
                        # Improved prompt with more structure
                        summary_template = """
                        You are a medical assistant helping a patient understand their health report.
                        Please analyze this document and provide:
                        
                        1. KEY FINDINGS: 2-3 most important medical findings
                        2. DIAGNOSES: Any diagnoses mentioned
                        3. MEDICATIONS: Prescribed medications with simple explanations
                        4. NEXT STEPS: Recommended follow-up actions
                        5. HEALTH ADVICE: General advice based on the findings
                        
                        Write in clear, simple language suitable for a patient.
                        
                        DOCUMENT:
                        {document}
                        
                        ANALYSIS:
                        """
                        prompt = PromptTemplate(input_variables=["document"], template=summary_template)
                        chain = LLMChain(prompt=prompt, llm=llm)
                        
                        summary = chain.run(content)
                        
                        st.subheader(f"Analysis of {doc_to_summarize}")
                        st.markdown(summary)
                        
                        # Generate reference links
                        def generate_reference_links(text):
                            medical_terms = {
                                "hypertension": "https://www.cdc.gov/bloodpressure/about.htm",
                                "diabetes": "https://www.cdc.gov/diabetes/basics/diabetes.html",
                                "cholesterol": "https://www.cdc.gov/cholesterol/about.htm",
                                "anemia": "https://www.nhlbi.nih.gov/health/anemia",
                                "infection": "https://www.cdc.gov/antibiotic-use/about.html"
                            }
                            
                            links = []
                            for term, url in medical_terms.items():
                                if term.lower() in text.lower():
                                    links.append(f"- [{term.capitalize()}]({url})")
                            
                            return "\n".join(links) if links else "No specific medical terms detected for additional resources."
                        
                        reference_material = generate_reference_links(summary)
                        
                        st.subheader("Learn More About These Topics")
                        st.markdown(reference_material)
        
        with tab4:
            st.header("Search Medical Records")
            
            # Initialize vector store if not already done
            if 'vector_store' not in st.session_state:
                from langchain.schema import Document
                from langchain.vectorstores import FAISS
                from langchain.embeddings import HuggingFaceBgeEmbeddings
                from langchain.text_splitter import CharacterTextSplitter
                
                try:
                    embeddings = HuggingFaceBgeEmbeddings(
                        model_name="BAAI/bge-small-en-v1.5",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    
                    documents_with_metadata = []
                    for file in uploaded_files:
                        if file.name.endswith('.pdf'):
                            pdf_loader = PyPDFLoader(file.name)
                            content = pdf_loader.load()[0].page_content
                        else:
                            content = st.session_state.ocr_results.get(file.name, "")
                        
                        metadata = {
                            'document_type': 'lab_report',
                            'specialty': document_tags.get(file.name, ["General"])[0],
                            'date': datetime.now().strftime("%Y-%m-%d"),
                            'source': file.name
                        }
                        
                        documents_with_metadata.append({
                            'content': content,
                            'metadata': metadata
                        })
                    
                    documents = [
                        Document(page_content=doc['content'], metadata=doc['metadata'])
                        for doc in documents_with_metadata
                    ]
                    
                    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                    documents_chunks = text_splitter.split_documents(documents)
                    
                    vector_store = FAISS.from_documents(documents_chunks, embeddings)
                    st.session_state.vector_store = vector_store
                except Exception as e:
                    st.error(f"Error initializing search: {str(e)}")
            
            # Search interface
            search_query = st.text_input("Search medical records", placeholder="e.g., MRI, blood pressure, medication")
            
            # Advanced filters
            with st.expander("Advanced Filters"):
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start date", datetime.now() - timedelta(days=365))
                with col2:
                    end_date = st.date_input("End date", datetime.now())
                
                doc_type = st.selectbox(
                    "Document Type",
                    ["All", "Lab Report", "Prescription", "Imaging Report"]
                )
            
            if search_query:
                with st.spinner("Searching records..."):
                    metadata_filters = {}
                    if specialty_filter != "All":
                        metadata_filters['specialty'] = specialty_filter.lower()
                    if doc_type != "All":
                        metadata_filters['document_type'] = doc_type.lower().replace(" ", "_")
                    
                    results = search_medical_documents(
                        search_query,
                        metadata_filters=metadata_filters if metadata_filters else None,
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.max.time())
                    )
                    
                    if results:
                        st.subheader(f"Search Results for '{search_query}'")
                        for i, result in enumerate(results, 1):
                            with st.expander(f"Document {i}: {result.metadata.get('source', 'Unknown')}"):
                                st.caption(f"Type: {result.metadata.get('document_type', 'N/A')}")
                                st.caption(f"Specialty: {result.metadata.get('specialty', 'N/A')}")
                                st.caption(f"Date: {result.metadata.get('date', 'N/A')}")
                                st.write(result.page_content[:500] + "...")
                    else:
                        st.warning("No matching records found")
        
        with tab5:
            st.header("Medical Timeline")
            
            # Create a timeline of documents and key events
            timeline_data = []
            for file in uploaded_files:
                timeline_data.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),  # Should extract from document
                    "Event": file.name,
                    "Type": document_tags.get(file.name, ["Unknown"])[0],
                    "Description": f"Uploaded {file.name.split('.')[-1].upper()} file"
                })
            
            # Add health alerts to timeline
            for _, row in df.iterrows():
                parameter = row["Parameter"]
                value = row["Value"]
                if parameter.lower() in reference_ranges:
                    min_val, max_val = reference_ranges[parameter.lower()]
                    if value < min_val or value > max_val:
                        timeline_data.append({
                            "Date": row["Date"].strftime("%Y-%m-%d"),
                            "Event": f"Alert: {parameter}",
                            "Type": "Alert",
                            "Description": f"{parameter} value {value} outside normal range ({min_val}-{max_val})"
                        })
            
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                timeline_df['Date'] = pd.to_datetime(timeline_df['Date'])
                timeline_df = timeline_df.sort_values('Date')
                
                fig = px.timeline(
                    timeline_df,
                    x_start="Date",
                    x_end="Date",
                    y="Event",
                    color="Type",
                    title="Medical Timeline",
                    hover_name="Description",
                    color_discrete_map={
                        "Cardiology": "#636EFA",
                        "Lab Report": "#EF553B",
                        "Alert": "#FFA15A",
                        "Prescription": "#00CC96"
                    }
                )
                
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    height=600,
                    showlegend=True,
                    hovermode="closest"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeline data available")

else:
    st.info("Please upload medical reports to begin analysis")
    st.image("https://www.pngitem.com/pimgs/m/146-1468479_my-medical-record-medical-records-clip-art-hd.png", width=300)

# Helper functions
def search_medical_documents(query, metadata_filters=None, start_date=None, end_date=None):
    if 'vector_store' not in st.session_state:
        return []
    
    search_results = st.session_state.vector_store.similarity_search(query, k=5)
    
    if metadata_filters:
        search_results = [
            result for result in search_results
            if all(result.metadata.get(key) == value for key, value in metadata_filters.items())
        ]
    
    if start_date and end_date:
        search_results = filter_by_date(search_results, start_date, end_date)
    
    return search_results

def filter_by_date(results, start_date, end_date):
    filtered = []
    for result in results:
        doc_date_str = result.metadata.get('date')
        if doc_date_str:
            try:
                doc_date = datetime.strptime(doc_date_str, "%Y-%m-%d")
                if start_date <= doc_date <= end_date:
                    filtered.append(result)
            except ValueError:
                continue
    return filtered
