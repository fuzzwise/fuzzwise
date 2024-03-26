import json, re, os
import gpt_interaction

tgt_exception_prompt_path = "../tgt_exception_prompt.txt"
tgt_coverage_prompt_path = "../tgt_coverage_prompt.txt"
cvg_prompt_path = "../cvg_prompt.txt"
tgt_exception_prompt_instructions = "../tgt_exception_prompt_instructions.txt"
tgt_coverage_prompt_instructions = "../tgt_coverage_prompt_instructions.txt"
cvg_prompt_instructions = "../cvg_prompt_instructions.txt"
json_result_path = "../test_coverage_result.json"
code_txt_path = "../code.txt"
codepilot_cvg_prompt_path = "../codepilot_main-oneshot-plan-prompt.txt"
codepilot_cvg_instructions = "../codepilot_oneshot-plan-prompt.txt"
input_json_file = f"../final_dataset.json"
output_folder = "../fuzzwise_outputs/responses" 


def read_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
    return code

def extract_symbols(code):
    lines = code.split('\n')
    symbols = [re.match(r'^\s*([>!]+)', line).group(1) for line in lines if re.match(r'^\s*([>!]+)', line)]
    return symbols

def remove_comments_and_blank_lines(code):
    code = re.sub(r'#.*', '', code)
    code = re.sub(r"'''(.*?)'''", '', code, flags=re.DOTALL)
    code = re.sub(r'"""(.*?)"""', '', code, flags=re.DOTALL)
    lines = code.split('\n')
    clean_lines = [line for line in lines if line.strip() != '' and not re.match(r'^\s*[>!]+\s*$', line)]
    code = '\n'.join(clean_lines)
    return code

def add_updated_code(existing_text, covered_code, generated_test_cases):
    updated_code_prompt = f'{existing_text}\nPREVIOUSLY GENERATED TEST CASES\n{generated_test_cases}\n\nJAVA PROGRAM:\n{covered_code}\n'
    return updated_code_prompt

def insert_code_and_testcase_in_prompt(existing_text, initial_code, test_case):
    prompt_with_code_and_testcase = f'{existing_text}\n{test_case}\nJAVA PROGRAM:\n{initial_code}'
    return prompt_with_code_and_testcase

def check_test_cases_generated(response):
    # Add your condition here to check if test cases are generated
    # For example, you can check for specific keywords or patterns in the response
    return "test case" in response.lower()

def check_all_coverage_symbols(new_coverage, old_coverage):
    min_length = min(len(new_coverage), len(old_coverage))
    for i in range(min_length):
        new_symbol = new_coverage[i]
        old_symbol = old_coverage[i]
        if new_symbol == '!' and old_symbol == '!':
            return False #coverage increasing prompt
        elif new_symbol == '>' and old_symbol == '!':
            return True #exception raising prompt
    return all(s == '>' for s in old_coverage)

def check_existing_responses(prompt_path, test_case):
    test_case = gpt_interaction.tgt_chatgpt_interaction(prompt_path)
    test_case = test_case.replace('"', '')
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as tgt_file:
            existing_responses = tgt_file.read()
            #ADD REMOVE "" AROUND TEST CASES FUNCTION HERE TO GIVE CLEAN TEST CASE
            if test_case in existing_responses:
                test_case = check_existing_responses(prompt_path, test_case)
    return test_case

def prepend_exclamation_mark(code):
    lines = code.split('\n')
    modified_lines = ["!" + line for line in lines]
    modified_code = '\n'.join(modified_lines)
    return modified_code

def add_coverage_symbols_to_code(clean_altered_code, coverage_symbols):
    lines = clean_altered_code.split('\n')
    result_code = []
    for line, symbol in zip(lines, coverage_symbols):
        if re.match(r'^\s*([^\s])', line):  # Check if the line is not empty or only spaces
            result_line = symbol+ ' ' + line.lstrip()
            result_code.append(result_line)
        else:
            result_code.append(line)  # Append empty lines or lines with only spaces
    return '\n'.join(result_code)

def remove_duplicates(raw_input):
    unique_input = list(set(raw_input))
    unique_input.sort()  # Sort to maintain order
    return unique_input

def extract_initial_code(submission_id, json_data):
    for submission in json_data:
        if submission['submission_id'] == submission_id:
            return submission['code_tokens']
    return None

def create_json_file(submission_id):
    json_filename = f"{submission_id}.json"
    json_filepath = os.path.join(output_folder, json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump({'submission_id': submission_id, 'cycles': []}, json_file, indent=2)
    return json_filepath

def save_cycle_response(json_filepath, response):
    with open(json_filepath, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        data['cycles'].append(response)
    with open(json_filepath, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=2)

def save_java_execution_output(submission_id, output):
    output_filepath = f"../fuzzwise_outputs/{submission_id}_output.txt"
    with open(output_filepath, 'w', encoding='utf-8') as output_file:
        output_file.write(output)
