import os
import json
import hcl2
from google import genai
from google.genai import types
from subprocess import run, CalledProcessError, PIPE

def parse_terraform_code(path="."):
    resources = []
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

def get_llm_summary(resources):
    try:
        # *** INITIALIZATION FOR GOOGLE-GENAI ***
        client = genai.Client()
        
        model_name = "gemini-pro"

        prompt = f"""
        You are a cloud infrastructure expert. Your task is to generate a concise summary of the following Terraform code changes. The summary should be easy for a human to understand and should highlight the resources being created and their key configuration details.

        Here is the structured data from the Terraform code:

        {json.dumps(resources, indent=2)}

        Generate the summary in a clear, bulleted list format.
        """

        # Generate content using the new client method
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
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
