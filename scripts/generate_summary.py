import os
import json
import hcl2
import vertexai 
from vertexai.generative_models import GenerativeModel
import traceback 

# GCP_PROJECT_ID = 'cp-sandbox-rohitvyankt-jagt904'
# GCP_REGION = 'us-east4'
# # ---------------------

def parse_terraform_code(path="."):
    resources = []
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.tf'):
                filepath = os.path.join(root, file)
                print(f"--- Attempting to parse: {filepath} ---")
                
                try:
                    with open(filepath, 'r') as f:
                        parsed_content = hcl2.load(f)
                        
                        if 'resource' in parsed_content:
                            for resource_block in parsed_content.get('resource', []):
                                for resource_type, resource_blocks in resource_block.items():
                                    for resource_name, attributes in resource_blocks.items():
                                        
                                        # Safely check if 'attributes' is a non-empty list before accessing index 0.
                                        if isinstance(attributes, list) and len(attributes) > 0:
                                            final_attributes = attributes[0]
                                        else:
                                            # Fallback to an empty dictionary if the structure is unexpected
                                            final_attributes = {} 
                                            
                                        resources.append({
                                            'type': resource_type,
                                            'name': resource_name,
                                            'attributes': final_attributes
                                        })
                
                except Exception as e:
                    print(f"\n!!! HCL PARSING FAILED FOR {filepath} !!!")
                    traceback.print_exc() 
                    print(f"------------------------------------------\n")
                    continue
                    
    return resources

def get_llm_summary(resources):
    try:
        vertexai.init(
            project=os.environ['GOOGLE_CLOUD_PROJECT'],
            location='us-east4'
        )
        model = GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        You are a cloud infrastructure expert. Your task is to generate a concise summary of the following Terraform resources. The summary should be easy for a human to understand and should highlight the resources being created and their key configuration details.

        Here is the structured data from the Terraform code:

        {json.dumps(resources, indent=2)}

        Generate the summary in a clear, bulleted list format.
        """

        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"LLM summarization failed: {type(e).__name__}: {e}"

def main():

    print("Starting Terraform parsing...")
    resources_data = parse_terraform_code(path="..")
    print(f"Found {len(resources_data)} resources after parsing.")
    
    if not resources_data:
        print("Skipping LLM summary because no resources were successfully parsed.")
        llm_summary = "No valid Terraform resources were found to summarize. Please ensure your 'main.tf' contains valid resources."
    else:
        print("Contacting Vertex AI for summary...")
        llm_summary = get_llm_summary(resources_data)

    print(f"\nsummary={llm_summary}")

if __name__ == "__main__":
    main()
