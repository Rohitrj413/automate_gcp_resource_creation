import os
import json
import hcl2
from google.cloud import aiplatform
from subprocess import run, CalledProcessError, PIPE

# 1. Parse Terraform code from the current directory
def parse_terraform_code(path="."):
    resources = []
    # os.walk() is a great way to find all .tf files in a project
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.tf'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        parsed_content = hcl2.load(f)
                        if 'resource' in parsed_content:
                            for resource_type, resource_blocks in parsed_content['resource'][0].items():
                                for resource_name, attributes in resource_blocks.items():
                                    resources.append({
                                        'type': resource_type,
                                        'name': resource_name,
                                        'attributes': attributes[0]
                                    })
                    except Exception as e:
                        print(f"Error parsing {filepath}: {e}")
    return resources

# 2. Call the Vertex AI Gemini API for summarization
def get_llm_summary(resources):
    try:
        # Initialize the Vertex AI client
        aiplatform.init(
            project=os.environ['GOOGLE_CLOUD_PROJECT'],
            location='us-central1'  # Choose your desired region
        )
        
        # Use the GenerativeModel class for Gemini
        model = aiplatform.GenerativeModel("gemini-1.5-pro-preview-0409")

        # Create a detailed prompt for the LLM
        prompt = f"""
        You are a cloud infrastructure expert. Your task is to generate a concise summary of the following Terraform code changes. The summary should be easy for a human to understand and should highlight the resources being created and their key configuration details.

        Here is the structured data from the Terraform code:

        {json.dumps(resources, indent=2)}

        Generate the summary in a clear, bulleted list format.
        """
        
        # Generate the content and return the text
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"LLM summarization failed: {e}"

# Main function to run all steps
def main():
    # 1. Parse Terraform files
    resources_data = parse_terraform_code()
    
    # 2. Get LLM summary
    llm_summary = get_llm_summary(resources_data)
    
    # 3. Set GitHub Actions output
    # This value will be used by the GitHub Actions workflow to post a comment
    print(f"summary={llm_summary}")

if __name__ == "__main__":
    main()