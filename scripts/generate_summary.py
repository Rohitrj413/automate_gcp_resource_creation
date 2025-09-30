import os
import sys # <-- Import sys to read command-line arguments
import vertexai 
from vertexai.generative_models import GenerativeModel
import traceback 
import warnings 

# --- Configuration for CI/CD ---
GCP_REGION = 'us-east4' 
# ---------------------

def read_terraform_code(file_list_raw):
    """
    Reads the content of ONLY the Terraform files specified in the file_list_raw 
    string (which comes from the 'git diff' command in the workflow).
    """
    # Split the raw string (newline-separated paths) into a list
    file_list = file_list_raw.strip().split('\n')
    
    all_code = ""
    found_tf = False
    
    print(f"--- Attempting to read {len(file_list)} changed Terraform file(s) ---")
    
    for filepath in file_list:
        # Check if the path is valid and ends with .tf
        if filepath and filepath.endswith('.tf') and os.path.exists(filepath):
            print(f"--- Reading changed file: {filepath} ---")
            found_tf = True
            try:
                with open(filepath, 'r') as f:
                    # Concatenate all content, separated by two newlines
                    all_code += f.read() + "\n\n"
            except Exception as e:
                print(f"\n!!! FILE READ FAILED FOR {filepath} !!!")
                traceback.print_exc() 
                continue

    if not found_tf:
        print("!!! NO VALID .tf FILES FOUND in PR changes !!!")
        return None
    
    return all_code.strip()


def get_llm_summary(raw_tf_code):
    """Uses the Gemini model to summarize the raw Terraform code."""
    warnings.filterwarnings("ignore", category=UserWarning)
    
    try:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise EnvironmentError("GOOGLE_CLOUD_PROJECT environment variable is not set.")

        vertexai.init(project=project_id, location=GCP_REGION)
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
        return f"LLM summarization failed: {type(e).__name__}: {e}"


def main():
    # ------------------------------------------------------------------
    # NEW: Read the list of files (as a single string) from the argument passed by the workflow
    # ------------------------------------------------------------------
    if len(sys.argv) < 2:
        file_list_raw = ""
    else:
        file_list_raw = sys.argv[1]

    print("Starting Terraform analysis...")
    
    # Define the delimiter for reliable multiline output capture
    DELIMITER = "EOF_SUMMARY_OUTPUT"

    if not file_list_raw:
        llm_summary = "No Terraform files were detected as changed in this Pull Request."
    else:
        raw_code = read_terraform_code(file_list_raw) 
        
        if not raw_code or len(raw_code) < 10: 
            llm_summary = "No valid Terraform code was found to summarize among the changed files."
        else:
            print("Contacting Vertex AI for summary...")
            llm_summary = get_llm_summary(raw_code)

    # CRITICAL: Print the output using the delimiter format for GHA
    print(f"SUMMARY_TOKEN_START::{DELIMITER}")
    print(llm_summary)
    print(f"SUMMARY_TOKEN_END::{DELIMITER}")


if __name__ == "__main__":
    main()
