import os
import json
import hcl2
# *** NEW IMPORTS FOR VERTEX AI ***
import vertexai 
from vertexai.generative_models import GenerativeModel, Content, Part, Tool, FunctionDeclaration, GenerationConfig
from subprocess import run, CalledProcessError, PIPE

def parse_terraform_code(path="."):
    resources = []
    # ... (rest of your parsing logic remains the same)
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.tf'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    try:
                        parsed_content = hcl2.load(f)
                        if 'resource' in parsed_content:
                            # Handling hcl2 structure to flatten resources
                            for resource_block in parsed_content.get('resource', []):
                                for resource_type, resource_blocks in resource_block.items():
                                    for resource_name, attributes in resource_blocks.items():
                                        resources.append({
                                            'type': resource_type,
                                            'name': resource_name,
                                            'attributes': attributes[0]
                                        })
                    except Exception as e:
                        # Improved error handling for parsing
                        print(f"Error parsing {filepath}: {e}")
    return resources

def get_llm_summary(resources):
    try:
        # 1. Initialize Vertex AI
        # This automatically uses the Service Account credentials provided by the GitHub Action
        vertexai.init(
            project=os.environ['GOOGLE_CLOUD_PROJECT'],
            location='us-east4'
        )
        
        # 2. Instantiate the Generative Model (using the correct import)
        model = GenerativeModel("gemini-2.0-flash")

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
        return f"LLM summarization failed: {type(e).__name__}: {e}"

def main():

    # 1. Parse Terraform files
    resources_data = parse_terraform_code()
    
    # 2. Get LLM summary
    llm_summary = get_llm_summary(resources_data)

    print(f"summary={llm_summary}")

if __name__ == "__main__":
    main()
