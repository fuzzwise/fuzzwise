import utils
import os, yaml
from openai import AzureOpenAI

def load_azure_config(config_path):
    """
    Loads the Azure OpenAI configuration from a YAML file.

    Args:
        config_path (str): The path to the configuration YAML file.

    Returns:
        dict: A dictionary containing the Azure OpenAI configurations for different services.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config['azure_openai']


def tgt_chatgpt_interaction(prompt_path, config_path, max_iterations=1):
    """
    Interacts with the Azure OpenAI GPT model to generate test cases based on the provided prompt.

    Args:
        prompt_path (str): The file path to the prompt text that will be used for generating test cases.
        config_path (str): The path to the YAML configuration file.
        max_iterations (int, optional): The maximum number of iterations to attempt generating valid test cases. Default is 1.

    Returns:
        str: The last generated test case from the GPT model.
    """
    azure_config = load_azure_config(config_path)
    tgt_config = azure_config['tgt']

    client = AzureOpenAI(
        api_key=tgt_config['api_key'],
        api_version=tgt_config['api_version'],
        azure_endpoint=tgt_config['azure_endpoint']
    )

    last_generated_test_case = ""
    for _ in range(max_iterations):
        user_prompt = utils.read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        
        response = client.chat.completions.create(
            model=tgt_config['model'],  # Fetch model name from config
            messages=messages,
            temperature=0.7
        )

        assistant_responses = [choice.message.content for choice in response.choices]
        last_generated_test_case = assistant_responses[-1]
        
        if check_test_cases_generated(assistant_responses[0]):
            break

    return last_generated_test_case


def check_test_cases_generated(response):
    """
    Checks if the response contains the phrase 'test case', indicating that a valid test case was generated.

    Args:
        response (str): The response from the GPT model.

    Returns:
        bool: True if the response contains 'test case', otherwise False.
    """
    return "test case" in response.lower()


def ccp_chatgpt_interaction(prompt_path, config_path, max_iterations=1):
    """
    Interacts with the Azure OpenAI GPT model to predict code coverage symbols based on the provided prompt.

    Args:
        prompt_path (str): The file path to the prompt text that will be used for predicting code coverage.
        config_path (str): The path to the YAML configuration file.
        max_iterations (int, optional): The maximum number of iterations to attempt generating valid coverage symbols. Default is 1.

    Returns:
        str: The assistant's response containing the predicted code coverage symbols.
    """
    azure_config = load_azure_config(config_path)
    ccp_config = azure_config['ccp']

    client = AzureOpenAI(
        api_key=ccp_config['api_key'],
        api_version=ccp_config['api_version'],
        azure_endpoint=ccp_config['azure_endpoint']
    )

    messages = []
    for _ in range(max_iterations):
        user_prompt = utils.read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        
        response = client.chat.completions.create(
            model=ccp_config['model'],  # Fetch model name from config
            messages=messages,
            temperature=0.7,
        )
        
        assistant_response = response.choices[0].message.content
        messages.append({'role': 'assistant', 'content': assistant_response})

        if check_all_coverage_symbols_gt(assistant_response):
            break

    return assistant_response


def check_all_coverage_symbols_gt(response):
    """
    Checks if all the coverage symbols in the response are greater-than (">") symbols.

    Args:
        response (str): The response containing code coverage symbols.

    Returns:
        bool: True if all coverage symbols are ">", otherwise False.
    """
    coverage_symbols = utils.extract_symbols(response)
    return all(symbol == '>' for symbol in coverage_symbols)
