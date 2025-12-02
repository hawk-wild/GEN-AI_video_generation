import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document

# --- CONFIGURATION ---
FOLDER_PATH = "path/to/your/documents_folder"  # <--- REPLACE THIS
OUTPUT_CSV = "iit_ism_timeline.csv"

# Keywords that define "Relevant" information for your video
# We only keep sentences that contain at least one of these concepts
KEYWORDS = [
    "established", "founded", "inaugurated", "university", "IIT", "status", 
    "ranking", "research", "department", "campus", "mining", "petroleum", 
    "golden jubilee", "centenary", "president", "director", "notable"
]

def read_file(file_path):
    """Reads text from PDF, DOCX, or TXT files."""
    text = ""
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + " "
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + " "
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def extract_events(text):
    """Extracts sentences that have a Year AND a relevant Keyword."""
    extracted_events = []
    
    # Clean text: Remove extra newlines and spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Split text into sentences (Simple split by period)
    # For better results, use: nltk.tokenize.sent_tokenize(text)
    sentences = text.split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        # 1. FIND DATES: Regex for years between 1800 and 2099
        years = re.findall(r'\b(18\d{2}|19\d{2}|20\d{2})\b', sentence)
        
        # 2. FILTER RELEVANCE: Check if any keyword exists
        has_keyword = any(k.lower() in sentence.lower() for k in KEYWORDS)
        
        if years and has_keyword:
            # We take the first year found as the primary timestamp
            primary_year = int(years[0])
            
            # 3. GEN AI PREP: Create a basic prompt stub for the video generation
            prompt_stub = f"Historical cinematic shot from {primary_year}, {sentence[:100]}..."
            
            extracted_events.append({
                "Year": primary_year,
                "Event": sentence,
                "GenAI_Prompt": prompt_stub
            })
            
    return extracted_events

# --- MAIN EXECUTION ---
all_events = []

# Loop through all files in the folder
for filename in os.listdir(FOLDER_PATH):
    file_path = os.path.join(FOLDER_PATH, filename)
    if os.path.isfile(file_path):
        print(f"Processing: {filename}...")
        raw_text = read_file(file_path)
        events = extract_events(raw_text)
        all_events.extend(events)

# Create DataFrame and Sort Chronologically
df = pd.DataFrame(all_events)

if not df.empty:
    df = df.sort_values(by="Year").drop_duplicates(subset=["Event"])
    print("\n--- Extraction Complete ---")
    print(df.head())
    
    # Save to CSV for the next phase (Video Generation)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nData saved to {OUTPUT_CSV}")
else:
    print("No relevant events found. Check your keywords or document content.")
