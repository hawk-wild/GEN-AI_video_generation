import os
import json
import re
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup
import requests

GROQ_API_KEY = "Enter_Your_Groq_API_Key_Here"


def llm_clean_article(paragraphs):
    """
    Takes a list of paragraphs extracted from HTML and returns a clean article-only text.
    Removes garbage, unrelated news, menus, ads, etc.
    """

    prompt = f"""
    You are cleaning raw web-scraped news article paragraphs.

    Input paragraphs:
    {json.dumps(paragraphs, indent=2)}

    Task:
    1. Identify ONLY the paragraphs that belong to the main article body.
    2. Remove:
       - Menus
       - Ads
       - Related articles
       - "Also read"
       - Comments
       - Category labels
       - Author bios
       - Navigation breadcrumbs
       - Dates / timestamps if not part of the story
    3. Return ONLY the clean article text in proper order.

    Output format:
    A single JSON object:
    {{
        "clean_text": "<cleaned article text>"
    }}
    """

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
        )

        data = response.json()
        cleaned = data["choices"][0]["message"]["content"]
        result = json.loads(cleaned)
        return result["clean_text"]

    except Exception as e:
        print(f"[LLM ERROR]: {e}")
        return "\n".join(paragraphs)

# --- USER CONFIGURATION ---
PARENT_DIRECTORY = "newsarticle/html"
OUTPUT_DIR = "./extracted_data"

# --- ENHANCED CONTEXT (UNCHANGED) ---
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

# ----------------------------------------------------
# FILE READERS (HTML + MHTML + Others)
# ----------------------------------------------------

def read_html_file(file_path):
    """Extract readable text from HTML."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        # Extract meaningful article paragraphs
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

        # Remove tiny junk paragraphs (< 30 chars)
        paragraphs = [p for p in paragraphs if len(p) > 30]

        # Apply LLM cleaning to get the real article content
        clean_text = llm_clean_article(paragraphs)

        return clean_text

    except Exception as e:
        print(f"   [Error] Could not read HTML {file_path}: {e}")
        return ""


def read_mhtml_file(file_path):
    """Extract readable text from MHTML."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return soup.get_text(separator=" ")
    except Exception as e:
        print(f"   [Error] Could not read MHTML {file_path}: {e}")
        return ""


def read_file_content(file_path):
    """Reads content from HTML/MHTML/PDF/DOCX/TXT."""
    try:
        if file_path.endswith(".html") or file_path.endswith(".htm"):
            return read_html_file(file_path)

        elif file_path.endswith(".mhtml") or file_path.endswith(".mht"):
            return read_mhtml_file(file_path)

        elif file_path.endswith('.pdf'):
            text = ""
            reader = PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            return text

        elif file_path.endswith('.docx'):
            text = ""
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text

        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

    except:
        pass

    return ""


# ----------------------------------------------------
# CATEGORY MATCHING (unchanged)
# ----------------------------------------------------

def extract_oriented_chunks(text, categories):
    extracted_chunks = []

    paragraphs = text.split('\n\n')

    for i, para in enumerate(paragraphs):
        para_clean = para.strip()

        if len(para_clean) < 30:
            continue

        found_categories = []

        for cat in categories:
            matches = [p for p in cat['match_phrases'] if p.lower() in para_clean.lower()]
            if matches:
                found_categories.append({
                    "category": cat['category_name'],
                    "matched_terms": matches
                })

        if found_categories:
            context_para = paragraphs[i - 1].strip() + "\n\n" if i > 0 else ""

            extracted_chunks.append({
                "content": context_para + para_clean,
                "tags": found_categories
            })

    return extracted_chunks


# ----------------------------------------------------
# MAIN — SIMPLIFIED (NO LLM, NO RECURSIVE DECISION)
# ----------------------------------------------------

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"🚀 Starting Extraction in: {PARENT_DIRECTORY}")

    final_knowledge_base = {}

    # Iterate through subdirectories in PARENT_DIRECTORY
    for foldername in os.listdir(PARENT_DIRECTORY):
        folder_path = os.path.join(PARENT_DIRECTORY, foldername)

        # Check if the folder contains an index.html file
        if not os.path.isdir(folder_path):
            continue

        index_file_path = os.path.join(folder_path, "index.html")
        if not os.path.exists(index_file_path):
            print(f"   ⚠️ Skipping {foldername}: No index.html found.")
            continue

        print(f"\n📄 Reading: {foldername}/index.html")

        text = read_file_content(index_file_path)
        if not text.strip():
            print("   ❌ Empty or unreadable.")
            continue

        chunks = extract_oriented_chunks(text, SEARCH_CONTEXT['categories'])

        if chunks:
            print(f"   ✅ Found {len(chunks)} relevant sections.")

            for chunk in chunks:
                for tag in chunk['tags']:
                    category = tag['category']
                    if category not in final_knowledge_base:
                        final_knowledge_base[category] = []
                    final_knowledge_base[category].append({
                        "source_file": f"{foldername}/index.html",
                        "matched_terms": tag['matched_terms'],
                        "text_content": chunk['content']
                    })
        else:
            print("   ⚠️ No category matches found.")

    # --- Save Outputs ---
    json_path = os.path.join(OUTPUT_DIR, "ism_news_extracted.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_knowledge_base, f, indent=2)

    md_path = os.path.join(OUTPUT_DIR, "REPORT.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Extracted IIT (ISM) Knowledge (News Articles)\n\n")
        for category, items in final_knowledge_base.items():
            f.write(f"## 📂 {category}\n")
            for item in items:
                f.write(f"**Source:** `{item['source_file']}`\n")
                f.write(f"**Matches:** {', '.join(item['matched_terms'])}\n")
                f.write(f"> {item['text_content'].replace(chr(10), ' ')}\n\n")
            f.write("---\n")

    print("\n🎉 Extraction Complete!")
    print(f"Saved JSON → {json_path}")
    print(f"Saved Markdown → {md_path}")

       
if __name__ == "__main__":
    main()
