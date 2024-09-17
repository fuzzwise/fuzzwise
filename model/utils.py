import json, re, os, yaml
import gpt


def load_paths_from_config(config_path):
    """
    Loads the language-specific paths from the YAML configuration file.

    Args:
        config_path (str): The path to the YAML configuration file.

    Returns:
        dict: A dictionary containing all the required paths based on the selected language.
    """
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    language = config['language'].lower()  # Get the chosen language (python or java)
    
    # Select the correct paths based on the language
    if language == "python":
        paths = config['paths']['python_prompts']
    elif language == "java":
        paths = config['paths']['java_prompts']
    else:
        raise ValueError(f"Unsupported language: {language}")
    
    # Add other common paths
    paths['output_folder'] = config['paths']['output_folder']
    paths['dataset'] = config['paths']['dataset']
    return paths


# Load paths from config.yaml
config_path = "config.yaml"
paths = load_paths_from_config(config_path)

# Paths are now sourced from the config.yaml
tgt_exception_prompt_path = paths['tgt_exception_prompt']
tgt_coverage_prompt_path = paths['tgt_coverage_prompt']
cvg_prompt_path = paths['cvg_prompt']
tgt_exception_prompt_instructions = paths['tgt_exception_instructions']
tgt_coverage_prompt_instructions = paths['tgt_coverage_instructions']
cvg_prompt_instructions = paths['cvg_instructions']
code_txt_path = paths['code_txt']
codepilot_cvg_prompt_path = paths['codepilot_cvg_prompt']
codepilot_cvg_instructions = paths['codepilot_cvg_instructions']
output_folder = paths['output_folder']

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_language_specific_paths(config):
    language = config.get('language', 'python').lower()  # Default to python if not specified
    if language == 'java':
        return config['paths']['java_prompts']
    else:
        return config['paths']['python_prompts']


def read_code(file_path):
    """
    Reads the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
    return code


def extract_symbols(code):
    """
    Extracts coverage symbols from code lines.

    Args:
        code (str): The code string containing coverage symbols.

    Returns:
        list: A list of coverage symbols.
    """
    lines = code.split('\n')
    symbols = [re.match(r'^\s*([>!]+)', line).group(1) for line in lines if re.match(r'^\s*([>!]+)', line)]
    return symbols


def remove_comments_and_blank_lines(code):
    """
    Removes comments and blank lines from the code.

    Args:
        code (str): The original code string.

    Returns:
        str: Cleaned code with comments and blank lines removed.
    """
    code = re.sub(r'#.*', '', code)
    code = re.sub(r"'''(.*?)'''", '', code, flags=re.DOTALL)
    code = re.sub(r'"""(.*?)"""', '', code, flags=re.DOTALL)
    lines = code.split('\n')
    clean_lines = [line for line in lines if line.strip() != '' and not re.match(r'^\s*[>!]+\s*$', line)]
    return '\n'.join(clean_lines)


def add_updated_code(existing_text, covered_code, generated_test_cases):
    """
    Adds the updated code and test cases to the prompt.

    Args:
        existing_text (str): The original text from the prompt.
        covered_code (str): The code that has been covered.
        generated_test_cases (str): The test cases that were generated.

    Returns:
        str: The updated prompt text with code and test cases.
    """
    updated_code_prompt = f'{existing_text}\nPREVIOUSLY GENERATED TEST CASES\n{generated_test_cases}\n\nPYTHON PROGRAM:\n{covered_code}\n'
    return updated_code_prompt


def insert_code_and_testcase_in_prompt(existing_text, initial_code, test_case):
    """
    Inserts the code and test case into the prompt text.

    Args:
        existing_text (str): The original prompt text.
        initial_code (str): The initial code to be included.
        test_case (str): The generated test case.

    Returns:
        str: The prompt text with code and test case inserted.
    """
    prompt_with_code_and_testcase = f'{existing_text}\n{test_case}\nPYTHON PROGRAM:\n{initial_code}'
    return prompt_with_code_and_testcase


def check_test_cases_generated(response):
    """
    Checks if the response contains a test case.

    Args:
        response (str): The GPT model response.

    Returns:
        bool: True if the response contains "test case", False otherwise.
    """
    return "test case" in response.lower()


def check_all_coverage_symbols(new_coverage, old_coverage):
    """
    Checks if the coverage symbols indicate increasing or decreasing coverage.

    Args:
        new_coverage (list): The new coverage symbols.
        old_coverage (list): The old coverage symbols.

    Returns:
        bool: True if coverage has increased, False if coverage is decreasing.
    """
    min_length = min(len(new_coverage), len(old_coverage))
    for i in range(min_length):
        new_symbol = new_coverage[i]
        old_symbol = old_coverage[i]
        if new_symbol == '!' and old_symbol == '!':
            return False  # Coverage is decreasing
        elif new_symbol == '>' and old_symbol == '!':
            return True  # Coverage is increasing
    return all(s == '>' for s in old_coverage)


def check_existing_responses(prompt_path, test_case):
    """
    Recursively checks if the test case exists in the existing responses.

    Args:
        prompt_path (str): The file path of the prompt.
        test_case (str): The generated test case.

    Returns:
        str: The clean test case if it doesn't exist in the responses, else a new test case.
    """
    test_case = gpt.tgt_chatgpt_interaction(prompt_path)
    test_case = test_case.replace('"', '')
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as tgt_file:
            existing_responses = tgt_file.read()
            if test_case in existing_responses:
                test_case = check_existing_responses(prompt_path, test_case)
    return test_case


def prepend_exclamation_mark(code):
    """
    Prepends an exclamation mark to each line of the code.

    Args:
        code (str): The original code.

    Returns:
        str: The code with '!' prepended to each line.
    """
    lines = code.split('\n')
    modified_lines = ["!" + line for line in lines]
    return '\n'.join(modified_lines)


def add_coverage_symbols_to_code(clean_altered_code, coverage_symbols):
    """
    Adds coverage symbols to the code.

    Args:
        clean_altered_code (str): The cleaned code without coverage symbols.
        coverage_symbols (list): The coverage symbols to be added.

    Returns:
        str: The code with coverage symbols added.
    """
    lines = clean_altered_code.split('\n')
    result_code = []
    for line, symbol in zip(lines, coverage_symbols):
        if re.match(r'^\s*([^\s])', line):  # Check if the line is not empty or only spaces
            result_line = symbol + ' ' + line.lstrip()
            result_code.append(result_line)
        else:
            result_code.append(line)  # Append empty lines or lines with only spaces
    return '\n'.join(result_code)


def remove_duplicates(raw_input):
    """
    Removes duplicate entries from the input list.

    Args:
        raw_input (list): The raw list of inputs.

    Returns:
        list: A deduplicated and sorted list.
    """
    unique_input = list(set(raw_input))
    unique_input.sort()
    return unique_input


def extract_initial_code(submission_id, json_data):
    """
    Extracts the initial code for a given submission ID from the JSON data.

    Args:
        submission_id (str): The ID of the submission.
        json_data (dict): The JSON data containing submissions.

    Returns:
        str: The initial code if found, otherwise None.
    """
    for submission in json_data:
        if submission['submission_id'] == submission_id:
            return submission['code_tokens']
    return None


def create_json_file(submission_id):
    """
    Creates a JSON file for the given submission ID.

    Args:
        submission_id (str): The ID of the submission.

    Returns:
        str: The path to the created JSON file.
    """
    json_filename = f"{submission_id}.json"
    json_filepath = os.path.join(output_folder, json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump({'submission_id': submission_id, 'cycles': []}, json_file, indent=2)
    return json_filepath


def save_cycle_response(json_filepath, response):
    """
    Saves the response of a cycle to a JSON file.

    Args:
        json_filepath (str): The path to the JSON file.
        response (str): The response to be saved.
    """
    with open(json_filepath, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        data['cycles'].append(response)
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=2)

def clean_test_case_content(test_case):
    """
    Clean the test case content by removing excessive content.
    Specifically, it removes any explanation or reasoning within 'test_case', 
    leaving only the essential input for the test case.
    """
    # Remove all content after the first occurrence of '\n\n'
    cleaned_test_case = re.split(r'\n\n', test_case, 1)[0]
    return cleaned_test_case.strip()  # Return cleaned test case, stripping any trailing/leading whitespace

def clean_and_deduplicate_json(file_path):
    """
    Read a JSON file, clean the test case content, remove duplicates, 
    and write the cleaned data to a new JSON file.
    """
    output_path = file_path
    # Read the input JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Ensure 'cycles' exists at the top level of the JSON
    if "cycles" not in data or not isinstance(data["cycles"], list):
        print(f"Error: 'cycles' key is missing or 'cycles' is not a list in file {file_path}.")
        return

    # List to hold cleaned data without duplicates
    cleaned_data = []

    for cycle in data['cycles']:
        # Ensure 'cycle' is a dictionary and has a 'test_case' key
        if isinstance(cycle, dict) and 'test_case' in cycle:
            # Clean the test case content
            cycle['test_case'] = clean_test_case_content(cycle['test_case'])
            
            # Append cleaned cycle to the cleaned_data list
            cleaned_data.append(cycle)
        else:
            print(f"Cycle entry doesn't have 'test_case' key or is not a dictionary in file {file_path}: {cycle}")

    # Remove duplicates based on 'test_case' and 'initial_code'
    cleaned_data = remove_duplicates(cleaned_data)

    # Write the cleaned data back to a new JSON file
    with open(output_path, 'w') as outfile:
        json.dump({"submission_id": data.get("submission_id", "unknown"), "cycles": cleaned_data}, outfile, indent=4)

def remove_duplicates(data):
    """
    Remove duplicate entries based on 'test_case' and 'initial_code'.
    """
    seen = set()
    unique_data = []
    
    for entry in data:
        key = (entry.get("test_case"), entry.get("initial_code"))
        if key not in seen:
            seen.add(key)
            unique_data.append(entry)
    
    return unique_data

def process_all_json_files_in_folder(input_folder, output_folder):
    """
    Process all JSON files in the specified input folder and save cleaned data to the output folder.
    """
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all JSON files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)
            print(f"Processing file: {input_file_path}")
            clean_and_deduplicate_json(input_file_path, output_file_path)
