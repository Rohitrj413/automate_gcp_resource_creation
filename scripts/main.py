import os
import vertexai
from vertexai.generative_models import GenerativeModel
import traceback
import warnings
from flask import jsonify # Required for HTTP-triggered functions

def read_terraform_code_from_request(request):
    """
    Retrieves the raw Terraform code from the HTTP request body.
    For a Cloud Function, we don't scan the file system; we read the payload.
    """
    try:
        # Check if the request body is JSON
        request_json = request.get_json(silent=True)
        if request_json and 'terraform_code' in request_json:
            return request_json['terraform_code']

        # Check if the request body is plain text (e.g., raw 'Content-Type: text/plain')
        return request.data.decode('utf-8')
        
    except Exception:
        # If decoding or getting JSON fails, return None
        return None


def get_llm_summary(raw_tf_code):
    """
    Uses the Gemini model on Vertex AI to summarize the raw Terraform code.
    """
    warnings.filterwarnings("ignore", category=UserWarning)
    
    try:
        # The Cloud Function environment provides the project ID automatically
        project_id = os.environ.get('GCP_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        if not project_id:
            # This should ideally not happen in GCF, but it's a good safeguard
            raise EnvironmentError("GOOGLE_CLOUD_PROJECT environment variable is not set.")

        vertexai.init(
            project=os.environ['GOOGLE_CLOUD_PROJECT'],
            location='us-east4'
        )

        model = GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        You are a cloud infrastructure expert. Your task is to generate a concise summary of the following Terraform code. The summary must be easy for a human to understand and **must highlight all resources being created and their key configuration details, including machine types, images, zones, locations, and any variable usage.**

        Here is the raw Terraform code to analyze:

        ```terraform
        {raw_tf_code}
        ```

        Generate the summary in a clear, bulleted list format.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        # Return a structured error message
        return f"LLM summarization failed: {type(e).__name__}: {e}"

# --------------------------------------------------------------------
# CLOUD FUNCTION ENTRY POINT
# The entry point you specified in your deployment command was 'sfmc_user_check', 
# so we use that name here.
# --------------------------------------------------------------------
def sfmc_user_check(request):
    """
    Main entry point for the HTTP-triggered Cloud Function.
    Generates a Terraform summary based on code provided in the request body.
    """
    
    raw_code = read_terraform_code_from_request(request)
    
    if not raw_code:
        return jsonify({"error": "No Terraform code found in the request body."}), 400
    
    if len(raw_code.strip()) < 10:
        llm_summary = "No valid Terraform code was provided in the payload."
    else:
        llm_summary = get_llm_summary(raw_code)

    # Return the summary in a structured JSON response
    return jsonify({
        "status": "success",
        "summary": llm_summary
    })

# The original main/read_terraform_code is no longer needed in this structure.
# The original read_terraform_code is omitted here as it's not used 
# in the Cloud Function context (which doesn't access the local file system).
