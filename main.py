import streamlit as st
import time
import uuid
import os
import google.generativeai as genai
import random
from repo_utils import (
    is_valid_repolink, 
    get_reponame, 
    clone_github_repo, 
    create_file_content_dict, 
    delete_directory,
    get_default_branch_code  # 🆕
)
from search_utils import (
    make_files_prompt, 
    parse_arr_from_gemini_resp, 
    content_str_from_dict, 
    make_all_files_content_str,
    format_agent_response  # 🆕
)
from chat_utils import streamer, transform_stlit_to_genai_history
from agents import (  # 🆕
    CodebaseQA, 
    LowLevelDesignAgent, 
    CodeGenerationAgent, 
    CodeChangesAgent
)

# --- App Config ---
st.set_page_config(
    page_title='RepoChat - Multi-Agent Code Analysis',
    page_icon="🤖",
    layout="wide"
)

# --- Constants ---
DATA_DIR = './repo'
AGENT_ICONS = {  # 🆕
    "Codebase Q&A": "❓",
    "Low-Level Design": "📐",
    "Code Generation": "👨💻",
    "Code Changes": "🔄"
}

# --- Initialize Session State ---
session_defaults = {
    "repo_details": {
        'name': '',
        'files2code': {},
        'is_entire_code_loaded': -1,
        'entire_code': ''
    },
    "messages": [],
    "title": '🔗 Enter GitHub Repository URL in Sidebar',
    "button_msg": 'Submit',
    "selected_agent": "Codebase Q&A"  # 🆕
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Configure Model ---
key_num = random.randint(1, 5)
genai.configure(api_key=st.secrets[f'GOOGLE_API_KEY_{str(key_num)}'])
model = genai.GenerativeModel('gemini-exp-1206')

# --- Sidebar ---
with st.sidebar:
    st.title("RepoChat Settings")
    
    # Agent Selection 🆕
    st.session_state.selected_agent = st.selectbox(
        "Select Agent Mode",
        options=list(AGENT_ICONS.keys()),
        format_func=lambda x: f"{AGENT_ICONS[x]} {x}",
        help="Choose the type of analysis you need"
    )
    
    # Repo Input
    repolink = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repo/tree/branch"
    )
    
    if st.button(st.session_state.button_msg, type="primary"):
        if is_valid_repolink(repolink):
            with st.spinner("🔄 Initializing repository..."):
                try:
                    # Reset state for new repo
                    st.session_state.repo_details = session_defaults["repo_details"]
                    st.session_state.messages = []
                    
                    # Clone and process repo
                    clone_folder = get_reponame(repolink)
                    reponame = clone_folder.replace('+', '/')
                    repo_clone_path = f"{DATA_DIR}/{clone_folder}"

                    if os.path.exists(repo_clone_path):
                        delete_directory(repo_clone_path)
                
                # Add unique identifier to prevent conflicts
                    unique_id = str(uuid.uuid4())[:8]
                    repo_clone_path = f"{DATA_DIR}/{clone_folder}-{unique_id}"
                    
                    clone_github_repo(repolink, repo_clone_path)
                    repo_dict = create_file_content_dict(repo_clone_path)
                    max_retries = 3
                    for _ in range(max_retries):
                        try:
                            delete_directory(repo_clone_path)
                            break
                        except Exception as e:
                            print(f"Retrying deletion: {str(e)}")
                            time.sleep(1)
                    
                    # Update session state
                    st.session_state.repo_details.update({
                        'name': reponame,
                        'files2code': repo_dict,
                        'code': make_all_files_content_str(repo_dict)
                    })
                    
                    st.session_state.title = f"🤖 Chatting with {reponame}"
                    st.session_state.button_msg = 'Change Repo'
                    st.success("✅ Repository loaded successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error processing repository: {str(e)}")
                    st.stop()
        else:
            st.error("⚠️ Invalid GitHub URL format")
            st.stop()
def get_input_placeholder():
    """Return dynamic input placeholder based on agent"""
    agent = st.session_state.selected_agent
    return {
        "Codebase Q&A": "Ask about the codebase...",
        "Low-Level Design": "Describe the feature to design...", 
        "Code Generation": "Describe the feature/bug to implement...",
        "Code Changes": "Analyze changes (automatic)"
    }.get(agent, "Ask about the repository...")
# --- Main Interface ---
st.title(st.session_state.title)
st.caption(f"Current Agent: {AGENT_ICONS[st.session_state.selected_agent]} {st.session_state.selected_agent}")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input(get_input_placeholder()):  # 🆕
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate agent-specific prompt 🆕
    try:
        agent_type = st.session_state.selected_agent
        repo_code = st.session_state.repo_details['code']
        repo_dict = st.session_state.repo_details['files2code']
        
        if agent_type == "Low-Level Design":
            input_to_LLM = LowLevelDesignAgent.generate_prompt(repo_code, prompt)
        elif agent_type == "Code Generation":
            input_to_LLM = CodeGenerationAgent.generate_prompt(repo_code, prompt)
        elif agent_type == "Code Changes":
            with st.spinner("🔍 Comparing with default branch..."):
                default_branch_code = get_default_branch_code(repolink)
                input_to_LLM = CodeChangesAgent.analyze_changes(repo_dict, default_branch_code)
        else:
            input_to_LLM = CodebaseQA.generate_prompt(repo_code, prompt)
            
        # Generate response
        genai_hist = transform_stlit_to_genai_history(
            st.session_state.messages,
            st.session_state.repo_details['is_entire_code_loaded'],
            st.session_state.repo_details['code']
        )
        chat = model.start_chat(history=genai_hist)
        gemini_resp = chat.send_message(input_to_LLM, stream=True)
        
        # Display formatted response
        with st.chat_message("assistant"):
            try:
                raw_response = st.write_stream(streamer(gemini_resp))
                formatted_response = format_agent_response(raw_response, agent_type)
                st.markdown(formatted_response)
            except Exception as e:
                error_msg = f"⚠️ Response Error: {str(e)}"
                st.markdown(error_msg)
                raw_response = error_msg
                
        st.session_state.messages.append({"role": "assistant", "content": raw_response})

    except Exception as e:
        st.error(f"🚨 Agent Processing Error: {str(e)}")
        st.stop()

# --- Helper Functions --- 🆕


# --- Main Execution ---
if __name__ == "__main__":
    pass