## Enhancing Fuzzing Intelligence: A Coverage-Guided Approach with FuzzWise

The coverage-guided fuzz testing framework serves as a systematic approach for automating software defect identification, crucial for enhancing program security and stability. Despite its widespread use, the framework faces challenges such as inefficiency and an ineffective feedback loop, hindering its effectiveness in identifying high-quality test cases and improving code coverage. To address these challenges, we propose a novel code coverage-guided fuzz testing framework, named FUZZWISE. Our framework leverages a Large Language Model (LLM)-based code coverage prediction tool to assess test quality upfront, prioritizing the execution of high-coverage test cases. Additionally, instead of traditional test mutation techniques, we employ the LLM to automatically generate test cases. These test cases undergo a feedback loop, where those contributing to higher code coverage are retained, while others are reintroduced to the LLM for refinement. Our empirical evaluation shows that FUZZWISE performs better than the conventional fuzz testing framework in efficient test case generation with higher coverage to effectively detect more runtime errors/exceptions.

### Dataset
All data for reproducing the results is available in the dataset.json file.

### Folder Structure 
```

├── fuzzwise
│   ├── model
│   │    ├──prompts
│   │    │    ├──code.txt
│   │    │    ├──codepilot_main-oneshot-prompt.txt
│   │    │    ├──codepilot_oneshot-plan-prompt.txt
│   │    │    ├──cvg_prompt.txt
│   │    │    ├──cvg_prompt_instructions.txt
│   │    │    ├──tgt_coverage_prompt.txt
│   │    │    ├──tgt_coverage_prompt_instructions.txt
│   │    │    ├──tgt_exception_prompt.txt
│   │    │    ├──tgt_exeception_prompt_instructions.txt
│   │    ├──execution.py
│   │    ├──gpt_interaction.py
│   │    ├──pipeline.py
│   │    ├──utils.py
│   │    ├──rq5.py
│   ├── fuzzwise outputs
│   │    ├──responses
│   │    ├──executions logs
│   ├── jazzer outputs
│   ├── dataset.json
│   └── README.md
```

## Procedure to fuzz a the dataset using FuzzWise

1. Clone the official github repository for FuzzWise
```
git clone https://github.com/fuzzwise/fuzzwise.git
```
2. Add the necessary paths required for fuzzing
3. Run the 'pipeline.py' file 


