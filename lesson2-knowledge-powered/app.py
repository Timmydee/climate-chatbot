# app.py - Enhanced with Document Loading
import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import google.generativeai as genai
from knowledge_base import ClimateKnowledgeBase, CLIMATE_SOURCES

# Configure the Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="Climate Helper v3 - Knowledge Enhanced", 
    layout="wide"
)

# Initialize knowledge base in session state
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ClimateKnowledgeBase()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hi! I'm your enhanced climate helper with access to real climate documents and research! Upload PDFs or let me fetch climate articles to give you more accurate, source-backed answers. What would you like to learn about?"
        }
    ]

def create_knowledge_enhanced_prompt(user_question: str, relevant_docs: list) -> str:
    """Create a prompt that includes relevant document context"""
    
    context = ""
    sources_used = []
    
    if relevant_docs:
        context = "\n\nRELEVANT CLIMATE KNOWLEDGE:\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\nSource {i} ({doc['source']}):\n{doc['content']}\n"
            sources_used.append(doc['source'])
    
    prompt = f"""You are a helpful climate and sustainability expert. Answer the user's question using your knowledge and the provided climate documents.

USER QUESTION: {user_question}
{context}

Please provide a helpful, accurate response that:
1. Answers the user's question thoroughly
2. References the provided sources when relevant
3. Cites specific source names when using information from documents
4. Is educational and encouraging
5. Suggests related topics they might want to explore

If using information from the provided sources, please mention them like: "According to [Source Name]..." or "The [Document Name] indicates..."
"""
    
    return prompt, sources_used

def display_knowledge_base_sidebar():
    """Display knowledge base management in sidebar"""
    with st.sidebar:
        st.markdown("## 📚 Knowledge Base")
        
        # Show current stats
        stats = st.session_state.knowledge_base.get_document_stats()
        
        if stats["total_chunks"] > 0:
            st.success(f"📊 Loaded: {stats['total_chunks']} chunks from {stats['sources']} sources")
            
            with st.expander("📋 Loaded Sources"):
                for source in stats["source_list"]:
                    st.write(f"• {source}")
        else:
            st.info("No documents loaded yet. Add some below!")
        
        st.markdown("### 📄 Upload PDF Documents")
        uploaded_file = st.file_uploader(
            "Upload climate reports, research papers, etc.",
            type=['pdf'],
            help="Upload IPCC reports, climate research papers, or sustainability documents"
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            os.makedirs("documents", exist_ok=True)
            file_path = os.path.join("documents", uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Process the PDF
            with st.spinner(f"Processing {uploaded_file.name}..."):
                documents = st.session_state.knowledge_base.load_pdf(file_path, uploaded_file.name)
                if documents:
                    st.success(f"✅ Loaded {len(documents)} chunks from {uploaded_file.name}")
                    st.rerun()
        
        st.markdown("### 🌐 Load Web Articles")
        
        # Predefined sources
        st.markdown("#### Quick Add Climate Sources:")
        selected_source = st.selectbox(
            "Choose a climate source",
            [""] + list(CLIMATE_SOURCES.keys())
        )
        
        if st.button("📥 Load Selected Source") and selected_source:
            with st.spinner(f"Loading {selected_source}..."):
                url = CLIMATE_SOURCES[selected_source]
                documents = st.session_state.knowledge_base.load_web_article(url, selected_source)
                if documents:
                    st.success(f"✅ Loaded {len(documents)} chunks from {selected_source}")
                    st.rerun()
        
        # Custom URL input
        st.markdown("#### Add Custom Article:")
        custom_url = st.text_input("Enter article URL")
        custom_name = st.text_input("Source name (optional)")
        
        if st.button("📥 Load Custom Article") and custom_url:
            with st.spinner("Loading article..."):
                documents = st.session_state.knowledge_base.load_web_article(
                    custom_url, 
                    custom_name if custom_name else None
                )
                if documents:
                    st.success(f"✅ Loaded {len(documents)} chunks")
                    st.rerun()
        
        # Clear knowledge base
        if st.button("🗑️ Clear Knowledge Base"):
            st.session_state.knowledge_base = ClimateKnowledgeBase()
            st.success("Knowledge base cleared!")
            st.rerun()

def friendly_wrap_with_sources(raw_text: str, sources_used: list) -> str:
    """Enhanced friendly wrapper that includes source information"""
    
    sources_section = ""
    if sources_used:
        unique_sources = list(set(sources_used))
        sources_section = f"\n\n📚 **Sources used in this response:**\n"
        for source in unique_sources:
            sources_section += f"• {source}\n"
    
    return f"Great question! 🌱\n\n{raw_text.strip()}{sources_section}\n\nWould you like me to elaborate on any part of this, or do you have other climate questions?"

def display_messages():
    """Display all messages in the chat"""
    for msg in st.session_state.messages:
        author = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(author):
            st.write(msg["content"])

# Create main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.title("🌱 Climate Helper v3.0")
    st.subheader("Enhanced with Real Climate Knowledge!")
    
    # Display messages
    display_messages()
    
    # Handle new user input
    prompt = st.chat_input("Ask me about climate topics (I can now reference documents!)...")
    
    if prompt:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Show user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Show thinking indicator
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # Search for relevant documents
            with st.spinner("Searching knowledge base..."):
                relevant_docs = st.session_state.knowledge_base.search_documents(prompt, max_results=3)
            
            if relevant_docs:
                placeholder.write("🔍 Found relevant documents, generating response...")
            else:
                placeholder.write("🤔 Thinking... (no specific documents found, using general knowledge)")
            
            try:
                # Create enhanced prompt with document context
                enhanced_prompt, sources_used = create_knowledge_enhanced_prompt(prompt, relevant_docs)
                
                # Generate response with Gemini
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(enhanced_prompt)
                
                answer = response.text
                friendly_answer = friendly_wrap_with_sources(answer, sources_used)
                
            except Exception as e:
                friendly_answer = f"I'm sorry, I encountered an error: {e}. Please try asking your question again."
            
            # Replace placeholder with actual response
            placeholder.write(friendly_answer)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": friendly_answer})
            
            # Show relevant document chunks if found
            if relevant_docs:
                with st.expander(f"📄 View {len(relevant_docs)} relevant document excerpts"):
                    for i, doc in enumerate(relevant_docs, 1):
                        st.markdown(f"**Source {i}: {doc['source']}** (Score: {doc['relevance_score']})")
                        st.markdown(f"```\n{doc['content'][:300]}...\n```")
                        st.markdown("---")

with col2:
    display_knowledge_base_sidebar()

# Footer
st.markdown("---")
stats = st.session_state.knowledge_base.get_document_stats()
st.markdown(f"💡 **Knowledge Enhanced**: {stats['total_chunks']} document chunks loaded from {stats['sources']} sources")