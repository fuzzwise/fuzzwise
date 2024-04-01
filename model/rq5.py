import os, time, re, random, ast, json
from openai import AzureOpenAI
from collections import Counter
import utils, execution

tgt_exception_prompt_path = "prompts/tgt_coverage_prompt.txt"
tgt_coverage_prompt_path = "prompts/tgt_coverage_prompt.txt"
cvg_prompt_path = "prompts/cvg_prompt.txt"
tgt_exception_prompt_instructions = "prompts/tgt_exception_prompt_instructions.txt"
tgt_coverage_prompt_instructions = "prompts/tgt_coverage_prompt_instructions.txt"
cvg_prompt_instructions = "prompts/cvg_prompt_instructions.txt"
json_result_path = "test_coverage_result.json"
code_txt_path = "prompts/code.txt"
codepilot_cvg_prompt_path = "prompts/codepilot_main-oneshot-plan-prompt.txt"
codepilot_cvg_instructions = "prompts/codepilot_oneshot-plan-prompt.txt"
input_json_file = f"../final_dataset.json"
output_folder = "../responses" 


def save_cycle_response(json_filepath, response):
    with open(json_filepath, 'a', encoding='utf-8') as json_file:
        json.dump(response, json_file)
        json_file.write('\n')

def extract_symbols(code):
    lines = code.split('\n')
    symbols = [re.match(r'^\s*([>!]+)', line).group(1) for line in lines if re.match(r'^\s*([>!]+)', line)]
    return symbols

def read_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
    return code

all_responses = []
def tgt_chatgpt_interaction(prompt_path, max_iterations=10):
    client = AzureOpenAI(
        api_key="OPENAI_KEY",
        api_version="OPENAI_VERSION",
        azure_endpoint="OPENAI_ENDPOINT"
    )
    temporary_storage = []
    generated_test_inputs = []  # List to store all generated test inputs
    for _ in range(max_iterations):
        user_prompt = read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        response = client.chat.completions.create(
            model="gpt-35",
            messages=messages,
            temperature=0.7,
            n=10  # Generate multiple completions
        )
        assistant_responses = [choice.message.content for choice in response.choices]
        all_responses.extend(assistant_responses)
        temporary_storage.extend(assistant_responses)
        generated_test_inputs.extend(assistant_responses)  # Add all generated test inputs to the list
        if check_test_cases_generated(assistant_responses[0]):
            break
    return generated_test_inputs, all_responses, temporary_storage


def check_test_cases_generated(response):
    return "test case" in response.lower()

def ccp_chatgpt_interaction(prompt_path, test_input):
    client = AzureOpenAI(
        api_key="OPENAI_KEY",
        api_version="OPENAI_VERSION",
        azure_endpoint="OPENAI_ENDPOINT"
    )
    messages = []
    for _ in range(1):  # Perform a single iteration
        user_prompt = read_code(prompt_path)
        messages = [{'role': 'user', 'content': user_prompt}]
        # Add the test input to the prompt
        messages.append({'role': 'assistant', 'content': test_input})
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
    coverage_symbols = extract_symbols(response)
    return all(symbol == '>' for symbol in coverage_symbols)

def interactive_testing_pipeline(submission_id, initial_code, time_limit_minutes=5):
    global coverage_status
    coverage_status = False
    generated_test_cases = ""
    generated_test_seeds = ""
    tgt_exception_prompt_instructions_text = utils.read_code(tgt_exception_prompt_instructions)
    tgt_coverage_prompt_instructions_text = utils.read_code(tgt_coverage_prompt_instructions)
    clean_altered_code = utils.remove_comments_and_blank_lines(initial_code)
    updated_code = utils.prepend_exclamation_mark(clean_altered_code)
    coverage_symbols = utils.extract_symbols(updated_code)
    code_length = len(coverage_symbols)
    print("Initial Coverage : ", coverage_symbols)
    start_time = time.time()
    fuzzwise_logs_json_filepath = utils.create_json_file(submission_id)
    response_counter = 0  # Counter to track response number
    
    while True:
        old_symbols = coverage_symbols
        current_time = time.time()
        elapsed_time_minutes = (current_time - start_time) / 60.0
        print(elapsed_time_minutes)
        
        if elapsed_time_minutes >= time_limit_minutes:
            print(f"Execution stopped after {time_limit_minutes} minutes.")
            break
        
        open(tgt_exception_prompt_path, 'w').close()
        open(tgt_coverage_prompt_path, 'w').close()
        
        if coverage_status:
            print("Prompt#1 : Raise Exceptions")
            tgt_prompt_text = utils.add_updated_code(tgt_exception_prompt_instructions_text, clean_altered_code, generated_test_seeds)
            with open(tgt_exception_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            test_seed, test_mutations, temporary_test_case_storage = tgt_chatgpt_interaction(tgt_exception_prompt_path)
            print("TCG RESPONSE")
            print(test_seed)
            test_seed = utils.remove_duplicates(test_seed)
            print("FIltered: ", test_seed)
            generated_test_seeds += f'{test_seed}\n'
            generated_test_cases = f'{test_mutations}\n'
            cvg_prompt_text = utils.read_code(codepilot_cvg_instructions)
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            
            for test_input in test_seed:
                print(test_input)
                coverage_prediction = ccp_chatgpt_interaction(cvg_prompt_path, test_input)
                coverage_symbols = utils.extract_symbols(coverage_prediction)
                result_coverage_symbols = coverage_symbols
                if utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols):
                    coverage_status = True
                else:
                    coverage_status = False
                
                min_length = min(len(old_symbols), len(coverage_symbols))
                for i in range(min_length):
                    if old_symbols[i] == '>' and coverage_symbols[i] == '!':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '!' and coverage_symbols[i] == '>':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '>' and coverage_symbols[i] == '>':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '!' and coverage_symbols[i] == '!':
                        coverage_symbols[i] = '!'
                
                if min_length < code_length:
                    coverage_symbols[min_length:code_length] = ['>' for _ in range(min_length, code_length)]
                
                print("CCP RESPONSE")
                print("Result Coverage : ", result_coverage_symbols)
                print("New Cumulative Coverage : ", coverage_symbols)
                
                # Save the response to the JSON file
                response_counter += 1
                response = {
                    'test_case': test_input,
                    'test_mutations': test_seed,
                    'initial_code': initial_code,
                    'covered_code': coverage_prediction,
                    'test_seed_coverage': result_coverage_symbols,
                    'cumulative_coverage': coverage_symbols
                }
                save_cycle_response(fuzzwise_logs_json_filepath, response)
        
        else:
            print("Prompt#2 : Increase Coverage")
            updated_code = utils.add_coverage_symbols_to_code(clean_altered_code, coverage_symbols)
            tgt_prompt_text = utils.add_updated_code(tgt_coverage_prompt_instructions_text, updated_code, generated_test_seeds)
            with open(tgt_coverage_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            test_seed, test_mutations, temporary_test_case_storage = tgt_chatgpt_interaction(tgt_exception_prompt_path)
            print("TCG RESPONSE")
            print(test_seed)
            test_seed = utils.remove_duplicates(test_seed)
            print("Filtered : ", test_seed)
            generated_test_seeds += f'{test_seed}\n'
            generated_test_cases = f'{test_mutations}\n'
            cvg_prompt_text = utils.read_code(codepilot_cvg_instructions)
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            
            for test_input in test_seed:
                print(test_input)
                coverage_prediction = ccp_chatgpt_interaction(cvg_prompt_path, test_input)
                coverage_symbols = utils.extract_symbols(coverage_prediction)
                result_coverage_symbols = coverage_symbols
                if utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols):
                    coverage_status = True
                else:
                    coverage_status = False
                
                min_length = min(len(old_symbols), len(coverage_symbols))
                for i in range(min_length):
                    if old_symbols[i] == '>' and coverage_symbols[i] == '!':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '!' and coverage_symbols[i] == '>':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '>' and coverage_symbols[i] == '>':
                        coverage_symbols[i] = '>'
                    elif old_symbols[i] == '!' and coverage_symbols[i] == '!':
                        coverage_symbols[i] = '!'
                
                if min_length < code_length:
                    coverage_symbols[min_length:code_length] = ['>' for _ in range(min_length, code_length)]
                
                print("CCP RESPONSE")
                print("Result Coverage : ", result_coverage_symbols)
                print("New Cumulative Coverage : ", coverage_symbols)
                
                # Save the response to the JSON file
                response_counter += 1
                response = {
                    'test_case': test_input,
                    'test_mutations': test_seed,
                    'initial_code': initial_code,
                    'covered_code': coverage_prediction,
                    'test_seed_coverage': result_coverage_symbols,
                    'cumulative_coverage': coverage_symbols
                }
                save_cycle_response(fuzzwise_logs_json_filepath, response)
    
    generated_test_cases = ast.literal_eval(generated_test_cases)
    formatted_test_cases = execution.format_test_cases(generated_test_cases)
    converted_test_cases = execution.convert_to_desired_format(formatted_test_cases)
    print(type(converted_test_cases))
   


code_txt_path = "prompts/code.txt"

# Load the initial code from the 'code.txt' file
with open(code_txt_path, 'r', encoding='utf-8') as code_file:
    initial_code = code_file.read()
    submission_id = "rq5"
    if initial_code:
        print("code found")
        interactive_testing_pipeline(submission_id, initial_code)
    else:
        print(f"Initial code not found for submission ID: {submission_id}")


