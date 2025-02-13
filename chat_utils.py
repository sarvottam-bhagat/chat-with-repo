def streamer(gemini_resp):
    """Stream response chunks from Gemini"""
    for chunk in gemini_resp:
        yield chunk.text

def transform_stlit_to_genai_history(transform_history, is_entire_code_loaded, entire_code):
    """Convert Streamlit chat history to GenAI format"""
    genai_history = []
    for message in transform_history:
        role = 'user' if message['role'] == 'user' else 'model'
        genai_history.append({
            'role': role,
            'parts': [{'text': message['content']}]
        })
    
    if is_entire_code_loaded == 1:
        prompt_to_use_codebase = "Use the above code if necessary. Preferably answer the question by citing the filepath and code."
        first_user_query = genai_history[0]['parts'][0]['text']
        first_user_query_modfied = f"'''\n{entire_code}\n'''\n {prompt_to_use_codebase}. {first_user_query}?"
        genai_history[0]['parts'][0]['text'] = first_user_query_modfied

    return genai_history