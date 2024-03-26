import utils
import os, re, random
from openai import AzureOpenAI
from collections import Counter


all_responses = []
def tgt_chatgpt_interaction(prompt_path, max_iterations=10):
    client = AzureOpenAI(
        api_key="39f437052841449ca67577a17b1f04d2",
        api_version="2023-09-15-preview",
        azure_endpoint="https://tien.openai.azure.com/"
    )
    temporary_storage = []
    last_generated_test_case = ""
    for _ in range(max_iterations):
        user_prompt = utils.read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        response = client.chat.completions.create(
            model="gpt-35",  # Replace with the correct model name
            messages=messages,
            temperature=0.7,
            n=10
        )
        assistant_responses = [choice.message.content for choice in response.choices]
        all_responses.extend(assistant_responses)
        temporary_storage.extend(assistant_responses)
        last_generated_test_case = assistant_responses[-1]
        for i, assistant_response in enumerate(assistant_responses, start=1):
            print(f"{assistant_response}")
        if check_test_cases_generated(assistant_responses[0]):
            break
    return last_generated_test_case, all_responses, temporary_storage


def check_test_cases_generated(response):
    return "test case" in response.lower()

def ccp_chatgpt_interaction(prompt_path, max_iterations=10):
    client = AzureOpenAI(
        api_key="39f437052841449ca67577a17b1f04d2",
        api_version="2023-09-15-preview",
        azure_endpoint="https://tien.openai.azure.com/"
    )
    messages = []
    for _ in range(max_iterations):
        user_prompt = utils.read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        response = client.chat.completions.create(
            model="gpt-35",
            messages=messages,
            temperature=0.7,
        )
        assistant_response = response.choices[0].message.content
        messages.append({'role': 'assistant', 'content': assistant_response})
        if check_all_coverage_symbols_gt(assistant_response):
            break
    return assistant_response

def check_all_coverage_symbols_gt(response):
    coverage_symbols = utils.extract_symbols(response)
    return all(symbol == '>' for symbol in coverage_symbols)

if __name__ == "__main__":
    tgt_response_text = tgt_chatgpt_interaction("your_tgt_prompt_path.txt")  
    print("Target Response:", tgt_response_text)
    ccp_response_text = ccp_chatgpt_interaction("your_cvg_prompt_path.txt")  
    print("Coverage Response:", ccp_response_text)
