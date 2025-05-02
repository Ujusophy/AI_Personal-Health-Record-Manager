# 🏥 Personal Health Record Manager  
*An AI-powered dashboard for analyzing and visualizing medical reports*
  
*Example: Trend visualization and AI summary of lab results*

---

## 🚀 Features  
- **Multi-format support**: Extract data from PDFs and scanned images (OCR)  
- **Health tracking**: Visualize trends for 8+ parameters (hemoglobin, glucose, etc.)  
- **AI summaries**: Get plain-language explanations of medical reports (Groq/Llama-3)  
- **Smart search**: Find records by symptoms, test names, or dates  
- **Privacy-focused**: Local processing + encrypted file storage  

---

## ⚙️ Setup  

### Prerequisites  
- Python 3.10+  
- Tesseract OCR (for image support)  
- llama Locally

### Installation  
1. Clone the repository:  
   ```bash
   git clone https://github.com/Ujusophy/personal-health-record.git
   cd personal-health-record
   ```

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

3. Install Tesseract for OCR & llama

---

## 🖥️ Usage  
1. Launch the app:  
   ```bash
   streamlit run app.py
   ```

2. In your browser:  
   - **Upload** PDFs or images of lab reports  
   - **View** extracted health metrics and trends  
   - **Generate** AI summaries of complex reports  
   - **Search** across all documents  

---

## 🛠️ Tech Stack  
| Component          | Technology Used                 |
|--------------------|---------------------------------|
| Document Processing| PyPDFLoader, Tesseract OCR      |
| NLP / AI           | Llama          |
| Vector Search      | FAISS + HuggingFace Embeddings  |
| Visualization      | Plotly             |
| UI Framework       | Streamlit                       |
| Security           | Fernet encryption               |

---

## 📂 Project Structure  
```
.
├── app.py                 
├── requirements.txt      
│── dataset
│── .gitignore   
└── assets/               
```
