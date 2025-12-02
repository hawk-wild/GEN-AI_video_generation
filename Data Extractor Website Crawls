import os
import json
import re
from PyPDF2 import PdfReader
from docx import Document
import openai

# --- USER CONFIGURATION ---
PARENT_DIRECTORY = "./"  # Replace with your main folder path
OUTPUT_DIR = "./extracted_data"          # Where to save results
# Hardcode your API key here for local use. Replace the placeholder with your real key.
OPENAI_API_KEY = "API_KEY"
# Use a Gemini model name here. Change if you have a different variant.
GEMINI_MODEL = "gemini-1.5"

# Initialize OpenAI client (uses `openai` package's OpenAI client wrapper)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- 1. ENHANCED CONTEXT (Loaded from your JSON structure) ---
# We combine keywords AND the specific semantic phrases for better matching.
SEARCH_CONTEXT = {
  "project_name": "100_Years_of_ISM_Dhanbad",
  "categories": [
    {
      "category_name": "Founding_and_Heritage",
      "match_phrases": [
        "Lord Irwin", "McPherson Committee Report", "Royal School of Mines", 
        "David Penman", "W.H. Berry", "Indian Mines Act", 
        "inauguration ceremony 1926", "architectural blueprint", 
        "Main Heritage Building", "World War II artillery base"
      ]
    },
    {
      "category_name": "Milestones_and_Evolution",
      "match_phrases": [
        "Deemed University Status", "UGC Act Section 3", "Institutes of Technology Act",
        "Gazette Notification 2016", "Prof. G.S. Marwaha", "ISM to IIT conversion",
        "Diamond Jubilee", "Golden Jubilee", "expansion of academic departments"
      ]
    },
    {
      "category_name": "Campus_Infrastructure",
      "match_phrases": [
        "Main Heritage Building", "Oval Garden", "Diamond Hostel", "Amber Hostel", 
        "Jasper Hostel", "Ruby Hostel", "Penman Auditorium", "Longwall Mine Gallery", 
        "Seismological Observatory", "Golden Jubilee Lecture Theatre", "Ramdhani Tea Stall"
      ]
    },
    {
      "category_name": "Student_Culture",
      "match_phrases": [
        "Srijan", "Concetto", "Basant", "Khanan", "ISM Siren", "Fast Forward India",
        "Kartavya NGO", "Chayanika Sangh", "Manthan", "Bhokal", "Pothaa",
        "alumni reunion tradition", "student slang"
      ]
    },
    {
      "category_name": "Academic_Excellence",
      "match_phrases": [
        "Department of Petroleum Engineering", "Applied Geology", "Computer Science and Engineering",
        "NVCTI", "Centre for Tinkering and Innovation", "Coal India Limited", "ONGC partnership",
        "Atal Innovation Mission", "seismology research", "mining safety technology"
      ]
    },
    {
      "category_name": "Notable_Alumni",
      "match_phrases": [
        "Gulshan Lal Tandon", "Jaswant Singh Gill", "Raniganj Rescue", 
        "Harsh Gupta", "Rabi Narayan Bastia", "Waman Bapuji Metre", 
        "Shanti Swarup Bhatnagar Award", "Padma Awardees"
      ]
    }
  ]
}

# --- 2. FILE READING UTILITIES ---

def read_file_content(file_path):
    """Reads content from PDF, DOCX, or TXT."""
    text = ""
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"   [Error] Could not read {file_path}: {e}")
    return text

# --- 3. INTELLIGENT FILTERING ---

def llm_check_relevance(filename, folder_name, context_summary):
    """
    Decides if a file is relevant based on its Name AND Folder location.
    """
    prompt = f"""
    Context: We are mining data for a documentary on the history of IIT (ISM) Dhanbad.
    
    File Path: {folder_name}/{filename}
    
    Target Topics: {context_summary}
    
    Task: Return JSON {{ "decision": "KEEP" or "IGNORE", "reason": "Short explanation" }}
    Rule: IGNORE generic administrative docs (mess menus, leave forms). KEEP anything historical, academic, or cultural.
    """
    
    try:
        # Use the Responses API with a Gemini model. We instruct the model to output
        # a JSON string which we then parse. This keeps the call generic and avoids
        # depending on chat-specific response structures.
        resp = client.responses.create(
            model=GEMINI_MODEL,
            input=prompt,
            temperature=0
        )

        # Extract text output robustly from the responses object
        output_text = ""
        if hasattr(resp, 'output_text') and resp.output_text:
            output_text = resp.output_text
        else:
            # Fallback: inspect `resp.output` which is often a list of content blocks
            out = getattr(resp, 'output', None)
            if isinstance(out, list):
                for block in out:
                    if isinstance(block, dict) and 'content' in block:
                        for c in block['content']:
                            # content items sometimes have 'text' keys
                            text_piece = c.get('text') if isinstance(c, dict) else None
                            if text_piece:
                                output_text += text_piece
            # If still empty, as last resort stringify the response
            if not output_text:
                output_text = str(resp)

        # Parse JSON result returned by the model
        return json.loads(output_text)
    except Exception as e:
        print(f"   [LLM Error] llm_check_relevance failed: {e}")
        return {"decision": "KEEP", "reason": "Error safe-guard"}

def extract_oriented_chunks(text, categories):
    """
    Scans text for the specific 'match_phrases'. 
    Returns chunks that contain these phrases with context.
    """
    extracted_chunks = []
    
    # Normalize text for easier matching
    text_lower = text.lower()
    
    # Split by paragraphs (keeping empty lines as delimiters)
    paragraphs = text.split('\n\n')
    
    for i, para in enumerate(paragraphs):
        para_clean = para.strip()
        if len(para_clean) < 30: continue 

        found_categories = []
        
        for cat in categories:
            # Check for any of the specific phrases
            matches = [phrase for phrase in cat['match_phrases'] if phrase.lower() in para_clean.lower()]
            
            if matches:
                found_categories.append({
                    "category": cat['category_name'],
                    "matched_terms": matches
                })
        
        if found_categories:
            # OPTIONAL: Grab previous paragraph for context if it exists
            context_para = ""
            if i > 0:
                context_para = paragraphs[i-1].strip() + "\n\n"
            
            extracted_chunks.append({
                "content": context_para + para_clean, # Combining context + hit
                "tags": found_categories
            })
            
    return extracted_chunks

# --- 4. MAIN ORCHESTRATOR ---

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"🚀 Starting Data Hunt in: {PARENT_DIRECTORY}")
    
    # Prepare summary for LLM
    context_summary = ", ".join([c['category_name'] for c in SEARCH_CONTEXT['categories']])
    
    final_knowledge_base = {} # Structure: { Category: [ {File, Text} ] }

    # OS.WALK for Recursive Directory Scanning
    for root, dirs, files in os.walk(PARENT_DIRECTORY):
        folder_name = os.path.basename(root)
        
        for file in files:
            if not file.endswith(('.pdf', '.docx', '.txt')):
                continue
                
            file_path = os.path.join(root, file)
            print(f"\nScanning: .../{folder_name}/{file}")
            
            # A. LLM GATEKEEPER
            decision = llm_check_relevance(file, folder_name, context_summary)
            
            if decision['decision'] == 'IGNORE':
                print(f"   ❌ Skipped: {decision['reason']}")
                continue
            
            print(f"   ✅ Reading: {decision['reason']}")
            
            # B. CONTENT EXTRACTION
            raw_text = read_file_content(file_path)
            if not raw_text: continue
            
            relevant_chunks = extract_oriented_chunks(raw_text, SEARCH_CONTEXT['categories'])
            
            if relevant_chunks:
                print(f"   Found {len(relevant_chunks)} relevant sections.")
                
                # C. ORGANIZE DATA
                for chunk in relevant_chunks:
                    for tag in chunk['tags']:
                        cat_name = tag['category']
                        if cat_name not in final_knowledge_base:
                            final_knowledge_base[cat_name] = []
                        
                        final_knowledge_base[cat_name].append({
                            "source_file": file,
                            "folder_context": folder_name,
                            "matched_terms": tag['matched_terms'],
                            "text_content": chunk['content']
                        })
            else:
                print("   (No specific phrases found in text)")

    # --- 5. SAVE OUTPUTS ---
    
    # Format 1: JSON for Code/GenAI
    json_path = os.path.join(OUTPUT_DIR, "ism_data_hunt_results.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(final_knowledge_base, f, indent=2)
        
    # Format 2: Markdown Report for Human Reading
    md_path = os.path.join(OUTPUT_DIR, "READABLE_REPORT.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# IIT (ISM) Dhanbad Data Hunt Report\n\n")
        for category, items in final_knowledge_base.items():
            f.write(f"## 📂 {category}\n")
            for item in items:
                f.write(f"**Source:** `{item['folder_context']}/{item['source_file']}`\n")
                f.write(f"**Keywords:** {', '.join(item['matched_terms'])}\n")
                f.write(f"> {item['text_content'].replace(chr(10), ' ')}\n\n") # Replace newlines for blockquote
            f.write("---\n")

    print(f"\n🎉 Extraction Complete!")
    print(f"1. Machine Data: {json_path}")
    print(f"2. Readable Report: {md_path}")

if __name__ == "__main__":
    main()
