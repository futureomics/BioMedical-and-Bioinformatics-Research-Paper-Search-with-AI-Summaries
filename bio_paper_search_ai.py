import streamlit as st
import requests
from dateutil import parser as date_parser
import datetime
import openai
import os

# --- Configuration ---
st.set_page_config(page_title="Bioinformatics Paper Search", layout="wide")
st.title("🔬 BioMedical and Bioinformatics Research Paper Search with AI Summaries")

# --- API Key Input ---
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
if openai_api_key:
    openai.api_key = openai_api_key

# --- Search Input ---
query = st.text_input("Enter keywords", placeholder="e.g., gene expression, RNA-seq")

# --- Filters ---
st.sidebar.header("🧬 Filters")
open_access_only = st.sidebar.checkbox("Open Access only", value=False)
journal_filter = st.sidebar.text_input("Journal name filter (optional)")
start_year = st.sidebar.number_input("Start year", min_value=1900, max_value=datetime.datetime.now().year, value=2015)
end_year = st.sidebar.number_input("End year", min_value=1900, max_value=datetime.datetime.now().year, value=datetime.datetime.now().year)

# --- Helper: Call CrossRef API ---
def search_papers(keyword, rows=10):
    url = "https://api.crossref.org/works"
    filters = ["type:journal-article"]
    if open_access_only:
        filters.append("license:*")
    if start_year:
        filters.append(f"from-pub-date:{start_year}-01-01")
    if end_year:
        filters.append(f"until-pub-date:{end_year}-12-31")
    if journal_filter:
        filters.append(f"container-title:{journal_filter}")

    params = {
        "query": keyword,
        "filter": ",".join(filters),
        "rows": rows,
        "sort": "relevance"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data["message"]["items"]
    except Exception as e:
        st.error(f"API error: {e}")
        return []

# --- Helper: GPT Abstract Summarization ---
def summarize_abstract(abstract):
    if not abstract or not openai_api_key:
        return "No abstract or API key provided."

    prompt = (
        "Summarize the following scientific abstract in simple terms:\n\n"
        f"{abstract.strip()}\n\nSummary:"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in bioinformatics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"⚠️ Error summarizing: {e}"

# --- Search Button ---
if st.button("🔍 Search") and query:
    with st.spinner("Searching..."):
        results = search_papers(query, rows=10)

    if results:
        st.success(f"Found {len(results)} results")

        for idx, paper in enumerate(results, 1):
            title = paper.get("title", ["No title"])[0]
            authors = ", ".join(f"{a.get('given', '')} {a.get('family', '')}" for a in paper.get("author", [])) or "Unknown authors"
            journal = paper.get("container-title", [""])[0] or "N/A"
            doi = paper.get("DOI", "")
            link = f"https://doi.org/{doi}" if doi else "#"
            abstract = paper.get("abstract", "")
            abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "").strip()
            date_parts = paper.get("published-print", {}).get("date-parts", [[None]])[0]
            year = date_parts[0] if date_parts else "Unknown"

            with st.expander(f"{idx}. {title}"):
                st.markdown(f"**Authors**: {authors}")
                st.markdown(f"**Journal**: {journal} ({year})")
                st.markdown(f"[View Paper ↗️]({link})", unsafe_allow_html=True)

                if abstract:
                    st.markdown("**Abstract:**")
                    st.markdown(abstract)

                    if openai_api_key:
                        with st.spinner("Generating AI summary..."):
                            summary = summarize_abstract(abstract)
                        st.markdown("**🔎 AI Summary:**")
                        st.success(summary)
                    else:
                        st.info("🔑 Enter your OpenAI API key in the sidebar to enable AI summaries.")
                else:
                    st.warning("No abstract available for this paper.")
    else:
        st.warning("No results found. Try refining your search or filters.")

# --- Footer ---
st.markdown("---")
st.caption("Powered by CrossRef API + OpenAI GPT · By 🤖 Future Omics · 🤖Bioinformatics made easy ❤️ using Streamlit")

