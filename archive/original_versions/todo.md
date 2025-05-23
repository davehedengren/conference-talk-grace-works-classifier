# Todo List: Conference Talk Grace-Works Classifier

- [x] **Project Setup**
    - [x] Initialize project structure (e.g., create main script file, `conference_talks` directory).
    - [x] Set up virtual environment and install necessary libraries (e.g., for LLM interaction, CSV handling, data analysis). (Created `requirements.txt`)
- [x] **File Handling & Data Extraction**
    - [x] Implement function to read conference talk files from the `conference_talks` folder. (Implemented in `classifier.py`)
    - [x] Implement function to extract the conference date (year and month) from the talk's filename. (Implemented assuming filename pattern `YYYY_MM_ConferenceName_...` in `classifier.py`)
    - [x] Implement function to extract the body text from each talk file. (Implemented basic file read in `classifier.py`, actual parsing might need more work depending on file content)
- [x] **LLM Interaction**
    - [x] Define clear guidelines for the LLM to classify the talk's grace-works balance (-3 to +3). (Placeholder guideline string in `classifier.py`)
    - [x] Implement function to send the talk text and guidelines to the LLM API. (Implemented dummy/placeholder function in `classifier.py`)
    - [x] Implement function to parse the LLM's JSON response to get the integer score. (Dummy function returns int directly)
    - [x] Add error handling for LLM API calls (e.g., network issues, invalid responses). (Basic structure, actual LLM error handling pending real implementation)
- [x] **CSV Generation**
    - [x] Implement function to create a CSV file. (Implemented in `classifier.py`)
    - [x] Write headers to the CSV: `filename`, `year`, `month`, `conference_name`, `text_preview`, `score`. (Implemented in `classifier.py`)
    - [x] Append data for each talk to the CSV. (Implemented in `classifier.py`)
- [x] Use BeautifulSoup to extract speaker's name from HTML and add to CSV.
- [x] **Data Analysis**
    - [x] Implement function to read the generated CSV. (Implemented in `classifier.py`)
    - [x] Calculate the average grace-works score for each conference. (Implemented in `classifier.py`)
    - [x] Implement logic to show how the balance between grace and works changes over time. (Printed to console; Matplotlib example code provided in comments in `classifier.py`)
- [ ] **Main Program Logic**
    - [x] Create the main script to orchestrate all the steps: read files, extract data, classify, write CSV, analyze. (Implemented in `classifier.py`)
- [ ] **Testing & Refinement**
    - [ ] Test with a few sample talk files. (Script includes creating dummy files for basic testing)
    - [ ] Refine LLM prompts/guidelines if classification results are not as expected. (Pending real LLM integration)
    - [ ] Test edge cases (e.g., empty files, files with missing metadata, LLM API errors). (Some basic handling, more needed for robustness)
- [x] **Documentation**
    - [x] Update `README.md` with final usage instructions and classification guidelines.
    - [ ] Add comments to the code where necessary. (Initial comments added)
- [x] **Batch API Management**
  - [x] Create Python script (`batch_manager.py`) for managing OpenAI Batch API jobs (upload, create, status, list, retrieve results).
- [x] Update filename parsing regex to support new formats (e.g., YYYY-MM-Identifier.html).
- [ ] **Reporting & Visualization**
  - [x] Create script (`generate_report.py`) to read output CSV.
  - [x] Implement functions in `generate_report.py` to create multiple charts (e.g., score over time, score distribution).
  - [x] Save generated charts as image files.
  - [x] Generate a markdown document in `generate_report.py` explaining trends and embedding charts.
- [x] Update `classifier.py` to extract speaker name (from HTML and/or filename) and add it to the CSV output.
- [x] Create `generate_report.py` script:
    - [x] Takes an output CSV file as input.
    - [x] Generates multiple charts (e.g., score by year, score distribution, average score per speaker).
    - [x] Saves charts to an `output/reports/` directory.
    - [x] Creates a markdown report in `output/reports/` embedding the charts and providing text explanations of trends.
- [x] Fix filename parsing in `classifier.py` for new formats (e.g., `2025-04-14johnson.html`) - DONE
- [x] Create `batch_manager.py` to handle OpenAI Batch API operations (upload, create, status, list, download results) - DONE
- [x] Investigate and fix `token_counter.py` - DONE
- [x] Switch to `o4-mini-2025-04-16` model in `classifier.py` - DONE
- [x] Add model name to CSV output in `classifier.py` - DONE
- [x] Resolve pandas/numpy version issue - DONE
- [x] Provide Seaborn code for score by year plot - DONE
- [x] **Streamlit App**
    - [x] Create `streamlit_app.py`.
    - [x] Load data from `output/labeled_conference_talks_with_speaker_names_20250517.csv`. (Now uses cleaned data)
    - [x] Implement time series analysis: P25, Mean, P75 of 'score' per conference session.
    - [x] Implement speaker analysis: List most 'works-focused' and 'most grace-focused' speakers.
    - [x] Implement overall score distribution chart.
    - [x] Add section for further analysis ideas.
    - [x] Add sidebar with 'About' and data source info.
- [x] **Data Cleaning / Validation**
    - [x] Create `find_similar_speakers.py` to identify near-duplicate speaker names using fuzzy matching.
    - [x] Create `clean_data.py` standalone script to clean speaker names (remove 'Â', normalize whitespace) and save to a new CSV.
    - [x] Update `streamlit_app.py` to use the cleaned CSV.
    - [x] Update `find_similar_speakers.py` to use the cleaned CSV and remove redundant cleaning. 