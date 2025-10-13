import os
import vertexai
from vertexai.generative_models import GenerativeModel
import warnings
from flask import jsonify, request 

# --- Core Logic: Summarize Code using Gemini ---
def get_llm_summary(raw_tf_code):
    """Initializes Vertex AI and calls the Gemini model to summarize the code."""
    warnings.filterwarnings("ignore", category=UserWarning)
    
    try:
        # GOOGLE_CLOUD_PROJECT is set by the 'auth' action in the workflow 
        # or by the Cloud Function runtime environment.
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        if not project_id:
            return "LLM Summarization Failed: GOOGLE_CLOUD_PROJECT environment variable is not set.", False

        # Initialize Vertex AI client
        vertexai.init(
            project=project_id,
            location='us-east4'
        )
        model = GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        You are a cloud infrastructure expert. Your task is to generate a concise summary of the following Terraform code. The summary must be easy for a human to understand and **must highlight all resources being created and their key configuration details.**

        Here is the raw Terraform code to analyze:

        ```terraform
        {raw_tf_code}
        ```

        Generate the summary in a clear, bulleted list format.
        """

        response = model.generate_content(prompt)
        return response.text.strip(), True
        
    except Exception as e:
        # Include traceback for debugging in the logs
        import traceback
        traceback.print_exc()
        return f"LLM summarization failed: {type(e).__name__}: {e}", False

# --- Entry Point for Cloud Run/Functions (HTTP Trigger) ---
def sfmc_user_check(request):
    """
    HTTP-triggered Cloud Function/Run entry point.
    It expects the raw Terraform code in the request body (JSON or text).
    """
    raw_code = None
    
    # 1. Try to get JSON data (expected for most webhooks)
    try:
        request_json = request.get_json(silent=True)
        if request_json and 'terraform_code' in request_json:
            raw_code = request_json['terraform_code']
        # 2. Fallback to raw text data
        elif request.data:
            raw_code = request.data.decode('utf-8')
    except Exception:
        pass

    if not raw_code or not raw_code.strip():
        # Return a 400 Bad Request
        return jsonify({"error": "No Terraform code found in the request body. Expected JSON key 'terraform_code' or raw text."}), 400
    
    llm_summary, success = get_llm_summary(raw_code)
    
    if not success:
        return jsonify({"error": llm_summary}), 500
        
    # Return the summary in a structured JSON response
    return jsonify({
        "status": "success",
        "summary": llm_summary
    })

# --- Local Utility Function for GitHub Actions ---
def read_all_terraform_code(base_path="."):
    """Recursively reads all .tf files for local script execution."""
    all_code = ""
    found_tf = False
    
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith('.tf'):
                filepath = os.path.join(root, file)
                found_tf = True
                try:
                    with open(filepath, 'r') as f:
                        all_code += f.read() + "\n\n"
                except Exception:
                    continue

    return all_code.strip() if found_tf else None

# --- Entry Point for Local Execution (GitHub Actions) ---
if __name__ == "__main__":
    
    raw_code = read_all_terraform_code(base_path=".")
    
    if not raw_code:
        llm_summary = "No valid Terraform code was found in the repository to summarize."
    else:
        llm_summary, _ = get_llm_summary(raw_code)

    # CRITICAL: Print only the summary for the workflow to capture
    print(llm_summary)
