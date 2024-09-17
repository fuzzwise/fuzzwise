import time
import gpt, utils

def interactive_testing_pipeline(submission_id, initial_code, config, config_path, time_limit_minutes=5):
    global coverage_status
    print("Submission ID ", submission_id)
    
    coverage_status = False
    generated_test_cases = ""
    generated_test_seeds = ""

    # Get language-specific paths
    paths = utils.get_language_specific_paths(config)
    
    # Read prompt instruction files
    tgt_exception_prompt_instructions_text = utils.read_code(paths['tgt_exception_instructions'])
    tgt_coverage_prompt_instructions_text = utils.read_code(paths['tgt_coverage_instructions'])
    clean_altered_code = utils.remove_comments_and_blank_lines(initial_code)
    updated_code = utils.prepend_exclamation_mark(clean_altered_code)
    coverage_symbols = utils.extract_symbols(updated_code)
    code_length = len(coverage_symbols)
    print("Initial Coverage: ", coverage_symbols)
    
    start_time = time.time()
    fuzzwise_logs_json_filepath = utils.create_json_file(submission_id)
    
    while True:
        old_symbols = coverage_symbols
        current_time = time.time()
        elapsed_time_minutes = (current_time - start_time) / 60.0
        print(elapsed_time_minutes)
        
        if elapsed_time_minutes >= time_limit_minutes:
            print(f"Execution stopped after {time_limit_minutes} minutes.")
            break

        # Get paths for the current language
        tgt_exception_prompt_path = paths['tgt_exception_prompt']
        tgt_coverage_prompt_path = paths['tgt_coverage_prompt']
        cvg_prompt_path = paths['cvg_prompt']

        open(tgt_exception_prompt_path, 'w').close()
        open(tgt_coverage_prompt_path, 'w').close()

        if coverage_status:
            print("Generating exception tests...")
            tgt_prompt_text = utils.add_updated_code(tgt_exception_prompt_instructions_text, clean_altered_code, generated_test_seeds)
            with open(tgt_exception_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            
            test_seed = gpt.tgt_chatgpt_interaction(tgt_exception_prompt_path, config_path)
            test_seed = test_seed.replace('"', '')
            print(test_seed)
            generated_test_seeds += f'{test_seed}\n'

            # Insert code and test case for coverage generation
            cvg_prompt_text = utils.read_code(paths['codepilot_cvg_instructions'])
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            
            coverage_prediction = gpt.ccp_chatgpt_interaction(cvg_prompt_path, config_path)
            coverage_symbols = utils.extract_symbols(coverage_prediction)
            
            # Update coverage
            result_coverage_symbols = coverage_symbols
            coverage_status = utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols)

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
        else:
            print("Prompt#2: Increase Coverage")
            updated_code = utils.add_coverage_symbols_to_code(clean_altered_code, coverage_symbols)
            tgt_prompt_text = utils.add_updated_code(tgt_coverage_prompt_instructions_text, updated_code, generated_test_seeds)
            
            with open(tgt_coverage_prompt_path, 'a', encoding='utf-8') as tgt_file:
                tgt_file.write(tgt_prompt_text)
            
            test_seed = gpt.tgt_chatgpt_interaction(tgt_coverage_prompt_path, config_path)
            test_seed = test_seed.replace('"', '')
            print(test_seed)
            generated_test_seeds += f'{test_seed}\n'

            # Repeat the same coverage checking logic
            cvg_prompt_text = utils.read_code(paths['codepilot_cvg_instructions'])
            cvg_prompt_text = utils.insert_code_and_testcase_in_prompt(cvg_prompt_text, initial_code, test_seed)
            
            with open(cvg_prompt_path, 'w', encoding='utf-8') as cvg_file:
                cvg_file.write(cvg_prompt_text)
            
            coverage_prediction = gpt.ccp_chatgpt_interaction(cvg_prompt_path, config_path)
            coverage_symbols = utils.extract_symbols(coverage_prediction)
            
            result_coverage_symbols = coverage_symbols
            coverage_status = utils.check_all_coverage_symbols(result_coverage_symbols, old_symbols)

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

        result = {
            'test_case': test_seed,
            'initial_code': initial_code,
            'covered_code': coverage_prediction,
            'test_seed_coverage': result_coverage_symbols,
            'cumulative_coverage': coverage_symbols
        }

        # Save and clean results
        utils.save_cycle_response(fuzzwise_logs_json_filepath, result)
        utils.clean_and_deduplicate_json(fuzzwise_logs_json_filepath)
