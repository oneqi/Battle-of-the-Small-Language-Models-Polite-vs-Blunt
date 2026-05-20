import os
import time
import gradio as gr
import requests

# Fetch internal Docker URLs
OLLAMA_ONE_URL = os.getenv("OLLAMA_ONE_URL", "http://ollama-1:11434")
OLLAMA_TWO_URL = os.getenv("OLLAMA_TWO_URL", "http://ollama-2:11434")

def query_ollama_chat(base_url, model_name, persona_prompt, user_message):
    """Sends a chat message to Ollama with a mandatory system persona."""
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": persona_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": False
            },
            timeout=45
        )
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "[Empty Response]")
        return f"[Error {response.status_code}: {response.text}]"
    except Exception as e:
        return f"[Connection Failed: {str(e)}]"

def start_debate(initial_prompt, model1_name, model2_name, persona1, persona2):
    """Runs a 5-round dialogue passing compliant dictionary elements to the chatbot."""
    history = []
    current_prompt = initial_prompt.strip()
    
    if not current_prompt:
        history.append({"role": "assistant", "content": "System: Please enter a valid starting prompt."})
        yield history
        return

    # Modern format payload: list containing explicit role and content dicts
    history.append({"role": "user", "content": f"Topic: {current_prompt}"})
    yield history
    
    m1_instruction = "Read this message and reply to it using your assigned persona: "
    m2_instruction = "Analyze this statement and respond sharply using your assigned persona: "

    for round_num in range(1, 6):
        # --- Model 1 Turn (Polite) ---
        input_to_m1 = f"{m1_instruction}\n\"{current_prompt}\""
        m1_response = query_ollama_chat(OLLAMA_ONE_URL, model1_name, persona1, input_to_m1)
        
        history.append({
            "role": "assistant", 
            "content": f"🌸 **Model 1 ({model1_name}) - Round {round_num}**:\n\n{m1_response}"
        })
        yield history
        
        current_prompt = m1_response
        time.sleep(0.8)
        
        # --- Model 2 Turn (Direct) ---
        input_to_m2 = f"{m2_instruction}\n\"{current_prompt}\""
        m2_response = query_ollama_chat(OLLAMA_TWO_URL, model2_name, persona2, input_to_m2)
        
        history.append({
            "role": "user",  # Using alternating roles changes bubble side layouts automatically
            "content": f"⚡ **Model 2 ({model2_name}) - Round {round_num}**:\n\n{m2_response}"
        })
        yield history
        
        current_prompt = m2_response
        time.sleep(0.8)

# Gradio Interface Setup
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Personified LLM Dialogue Controller")
    gr.Markdown("Watch a polite model and a direct model debate over 5 automated rounds.")
    
    with gr.Accordion("Model & Persona Configurations", open=False):
        with gr.Row():
            m1_input = gr.Textbox(label="Model 1 ID", value="llama3.2")
            m2_input = gr.Textbox(label="Model 2 ID", value="llama3.2")
        with gr.Row():
            p1_prompt = gr.Textbox(
                label="Model 1 Persona (System Prompt)", 
                value="You are an incredibly polite, formal, and diplomatic assistant. \
                       Use courteous language, acknowledge opposing views softly, \
                       concise and avoid harsh phrasing."
            )
            p2_prompt = gr.Textbox(
                label="Model 2 Persona (System Prompt)", 
                value="You are extremely direct, blunt, and highly analytical. \
                       Do not waste words on pleasantries. \
                       Get straight to the core flaws of the argument with objective reasoning \
                       and use bullet points to be objective."
            )
        
    with gr.Row():
        user_prompt = gr.Textbox(
            label="Topic / Starting Question", 
            placeholder="Is pineapple acceptable on pizza?",
            scale=4
        )
    
    with gr.Row():
        submit_btn = gr.Button("Start Discussion", variant="primary")
        stop_btn = gr.Button("Stop Discussion", variant="stop")
       
    # Reverted back to minimal parameter instantiation to satisfy standard rendering checks
    chatbot = gr.Chatbot(label="Conversation Log")
    
    click_event = submit_btn.click(
        fn=start_debate, 
        inputs=[user_prompt, m1_input, m2_input, p1_prompt, p2_prompt], 
        outputs=chatbot
    )
    
    stop_btn.click(fn=None, inputs=None, outputs=None, cancels=[click_event])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)



