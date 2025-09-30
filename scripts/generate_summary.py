import os
import json
import vertexai 
from vertexai.generative_models import GenerativeModel
import traceback 
import warnings 

def read_terraform_code(path="."):
    filepath = os.path.join(path, filename)
    print(f"--- Attempting to read raw file: {filepath} ---")
    
    all_code = ""
    found_tf = False
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.tf'):
                filepath = os.path.join(root, file)
                print(f"--- Reading: {filepath} ---")
                found_tf = True
                try:
                    with open(filepath, 'r') as f:
                        all_code += f.read() + "\n\n"
                except Exception as e:
                    print(f"\n!!! FILE READ FAILED FOR {filepath} !!!")
                    traceback.print_exc() 
                    continue

    if not found_tf:
        print("!!! NO .tf FILES FOUND !!!")
        return None
    
    return all_code.strip()


def get_llm_summary(raw_tf_code):
    
    warnings.filterwarnings("ignore", category=UserWarning)
    
    try:
        vertexai.init(
            project=os.environ['GOOGLE_CLOUD_PROJECT'],
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
        return response.text.strip()
        
    except Exception as e:
        return f"LLM summarization failed: {type(e).__name__}: {e}"

def main():

    print("Starting Terraform analysis...")
    # Read all .tf files in the parent directory
    raw_code = read_terraform_code(path="..") 
    
    if not raw_code:
        print("Skipping LLM summary because no valid code was read.")
        llm_summary = "No valid Terraform code was found to summarize. Please ensure your configuration files are present."
    else:
        print("Contacting Vertex AI for summary...")
        llm_summary = get_llm_summary(raw_code)

    print(f"\nsummary={llm_summary}")

if __name__ == "__main__":
    main()
