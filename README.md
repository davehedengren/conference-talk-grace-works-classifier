# Conference Talk Grace-Works Classifier

This program analyzes conference talks to determine their balance between grace and works on a scale of -3 to +3. A score of +3 indicates the talk is heavily focused on works (following commandments to become like Heavenly Father and Jesus Christ), while a score of -3 indicates the talk is heavily focused on grace (the Savior's atoning sacrifice redeeming us from sin). A score of 0 indicates a balanced talk that equally emphasizes both aspects.

## Program Steps

The program performs the following steps:

1. **Read Conference Talks**: It reads talk files from a specified folder (e.g., `conference_talks`).
2. **Extract Metadata**: For each talk, it extracts the conference date (year and month) and conference name from the filename.
3. **Extract Text**: It extracts the main body text of the talk.
4. **Classify Talk**: The extracted text, along with specific guidelines, is sent to a Large Language Model (LLM). The LLM classifies the talk based on its balance between grace and works.
5. **Store Score**: The LLM returns a JSON object containing a single integer field representing the grace-works score (-3 to +3).
6. **Generate CSV**: A CSV file is created, listing each conference talk's filename, metadata, text preview, and its assigned grace-works score.
7. **Analyze Trends**: After processing all talks, the program conducts an analysis to show how the balance between grace and works in talks changes over time.

## Classification Guidelines

- **+3**: Talk heavily emphasizes works, commandments, and following Christ through our actions
- **+2**: Talk primarily focuses on works but acknowledges grace
- **+1**: Talk leans toward works but maintains some balance
- **0**: Talk equally balances grace and works
- **-1**: Talk leans toward grace but maintains some balance
- **-2**: Talk primarily focuses on grace but acknowledges works
- **-3**: Talk heavily emphasizes grace, the Atonement, and Christ's redeeming power

## Usage

(To be filled in once the program is developed)

## Contributing

(To be filled in once the program is developed) 