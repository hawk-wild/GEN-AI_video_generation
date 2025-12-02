import json
import re
import requests
from collections import defaultdict

# ----------------------------
# GROQ API CONFIG
# ----------------------------

GROQ_API_KEY = "gsk_..."   # <-- your real key

def llm_finalize_script(raw_script):
    """
    Polish the final script with Llama-3-70B on Groq.
    Improves flow, removes redundancy, maintains correctness.
    """
    prompt = f"""
You are an expert documentary scriptwriter.

Below is a draft script for a 2-minute documentary about IIT(ISM) Dhanbad.
Improve it by:

- making narration smooth and cohesive
- improving sentence transitions
- removing redundancy
- tightening overly long lines
- keeping factual correctness
- keeping total length ~2 minutes
- DO NOT add fictional content

Return ONLY the improved script.

Draft Script:
---
{raw_script}
---
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
        )

        result = response.json()
        final_text = result["choices"][0]["message"]["content"]
        return final_text

    except Exception as e:
        print("[LLM ERROR]", e)
        return raw_script



# ----------------------------
# CATEGORY DEFINITIONS
# ----------------------------

SEARCH_CONTEXT = {
    "categories": [
        {
            "category_name": "Founding_and_Heritage",
            "match_phrases": [
                "Lord Irwin", "McPherson Committee Report", "Royal School of Mines",
                "David Penman", "W.H. Berry", "Indian Mines Act",
                "inauguration", "Main Heritage Building", "World War II"
            ]
        },
        {
            "category_name": "Milestones_and_Evolution",
            "match_phrases": [
                "Deemed University Status", "UGC Act", "Institutes of Technology Act",
                "Gazette Notification", "conversion", "Diamond Jubilee",
                "Golden Jubilee", "expansion"
            ]
        },
        {
            "category_name": "Campus_Infrastructure",
            "match_phrases": [
                "Main Heritage Building", "Oval Garden", "Diamond Hostel",
                "Amber Hostel", "Jasper Hostel", "Penman Auditorium",
                "Seismological Observatory", "Lecture Theatre", "Ramdhani"
            ]
        },
        {
            "category_name": "Student_Culture",
            "match_phrases": [
                "Srijan", "Concetto", "Basant", "Khanan", "ISM Siren",
                "Kartavya", "Manthan", "alumni"
            ]
        },
        {
            "category_name": "Academic_Excellence",
            "match_phrases": [
                "Petroleum Engineering", "Applied Geology", "Computer Science",
                "NVCTI", "innovation", "research", "Coal India",
                "seismology", "technology"
            ]
        },
        {
            "category_name": "Notable_Alumni",
            "match_phrases": [
                "Gulshan Lal Tandon", "Jaswant Singh Gill", "Raniganj Rescue",
                "Rabi Narayan Bastia", "Padma", "Bhatnagar"
            ]
        }
    ]
}



# ----------------------------
# FILE LOADERS
# ----------------------------

def load_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



# ----------------------------
# CLEAN + EXTRACT
# ----------------------------

def clean_paragraph(p):
    p = re.sub(r"\s+", " ", p)
    return p.strip() if len(p.strip()) >= 40 else ""

def paragraph_relevant(paragraph, phrases):
    return any(p.lower() in paragraph.lower() for p in phrases)

def extract_clean_data(website_text, news_json, categories):

    out = defaultdict(list)

    # Website text
    for para in website_text.split("\n"):
        p = clean_paragraph(para)
        if not p:
            continue

        for cat in categories:
            if paragraph_relevant(p, cat["match_phrases"]):
                out[cat["category_name"]].append(p)

    # News JSON
    for cat, items in news_json.items():
        for entry in items:
            p = clean_paragraph(entry["text_content"])
            if p:
                out[cat].append(p)

    return out



# ----------------------------
# RAW SCRIPT GENERATION
# ----------------------------

TEMPLATE = """
🎬 **VIDEO SCRIPT — "100 Years of IIT(ISM) Dhanbad"**

**INTRO**
For nearly a century, IIT(ISM) Dhanbad has stood as one of India’s most iconic institutions — evolving from a mining school into an IIT that shaped leaders, researchers, and pioneers.

---

**1️⃣ Founding & Heritage**
{Founding_and_Heritage}

---

**2️⃣ Milestones & Evolution**
{Milestones_and_Evolution}

---

**3️⃣ Campus Infrastructure**
{Campus_Infrastructure}

---

**4️⃣ Student Culture & Festivals**
{Student_Culture}

---

**5️⃣ Academic Excellence & Research**
{Academic_Excellence}

---

**6️⃣ Notable Alumni**
{Notable_Alumni}

---

**OUTRO**
A century later, IIT(ISM) continues to honour its heritage while driving innovation and national impact.
This is the legacy of ISM — an institution built on courage, knowledge, and exploration.
"""

def summarize_for_script(text_list, max_sentences=2):
    if not text_list:
        return "Data not available."

    combined = " ".join(text_list)
    sentences = re.split(r"(?<=[.!?])\s+", combined)
    clean = [s.strip() for s in sentences if len(s.strip()) > 30]

    return " ".join(clean[:max_sentences])

def generate_raw_script(cleaned):
    replace_map = {}

    for cat_obj in SEARCH_CONTEXT["categories"]:
        cat = cat_obj["category_name"]
        replace_map[cat] = summarize_for_script(cleaned.get(cat, []))

    return TEMPLATE.format(**replace_map)



# ----------------------------
# MAIN
# ----------------------------

def main():
    website_text = load_txt("website_extracted_data.txt")
    news_json = load_json("extracted_data/ism_news_extracted.json")

    cleaned_data = extract_clean_data(
        website_text,
        news_json,
        SEARCH_CONTEXT["categories"]
    )

    raw_script = generate_raw_script(cleaned_data)
    final_script = llm_finalize_script(raw_script)

    with open("FINAL_2_MIN_VIDEO_SCRIPT.txt", "w", encoding="utf-8") as f:
        f.write(final_script)

    print("\n🎉 FINAL SCRIPT GENERATED!\n")
    print(final_script)


if __name__ == "__main__":
    main()
