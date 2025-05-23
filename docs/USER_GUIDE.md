# Conference Talk Grace-Works Classifier - User Guide

Welcome to the comprehensive user guide for the Conference Talk Grace-Works Classifier! This guide will walk you through everything you need to know to effectively use this enterprise-grade application.

## 📖 Table of Contents

1. [Getting Started](#-getting-started)
2. [Understanding Grace-Works Classification](#-understanding-grace-works-classification)
3. [Basic Usage](#-basic-usage)
4. [Advanced Features](#-advanced-features)
5. [Dashboard Guide](#-dashboard-guide)
6. [Performance Optimization](#-performance-optimization)
7. [Troubleshooting](#-troubleshooting)
8. [Best Practices](#-best-practices)

## 🚀 Getting Started

### What is this tool?

The Conference Talk Grace-Works Classifier is an AI-powered tool that analyzes religious conference talks (particularly LDS General Conference talks) and classifies them on a theological spectrum from **Grace** (-3) to **Works** (+3). This helps researchers, scholars, and interested individuals understand the theological emphasis of different talks over time.

### Quick Setup Checklist

- [ ] Python 3.9+ installed
- [ ] OpenAI API key obtained
- [ ] Project dependencies installed
- [ ] Conference talk files prepared
- [ ] Environment configured

For detailed setup instructions, see our [README.md](../README.md).

## 🎯 Understanding Grace-Works Classification

### The Scale Explained

Our classification system uses a **7-point scale** from -3 to +3:

| Score | Category | Description | Example Themes |
|-------|----------|-------------|----------------|
| **-3** | **Strong Grace** | Heavily emphasizes God's grace and Christ's atonement | "Saved by grace alone", "Christ's sacrifice sufficient" |
| **-2** | **Grace Focus** | Primarily focuses on grace with some balance | "Grace enables our efforts", "Mercy covers our shortcomings" |
| **-1** | **Grace Leaning** | Leans toward grace but maintains balance | "Faith in Christ", "Trust in the Savior" |
| **0** | **Balanced** | Equal emphasis on both grace and works | "Faith and works together", "Grace enables obedience" |
| **+1** | **Works Leaning** | Leans toward works but maintains balance | "Following commandments", "Personal righteousness" |
| **+2** | **Works Focus** | Primarily focuses on works with some grace | "Obedience brings blessings", "Perfecting ourselves" |
| **+3** | **Strong Works** | Heavily emphasizes human effort and obedience | "Earn your salvation", "Merit through obedience" |

### Key Theological Concepts

**Grace (Negative Scores):**
- Divine mercy and forgiveness
- Christ's atonement and sacrifice
- Salvation as a gift from God
- Unmerited divine favor
- God's love despite human weakness

**Works (Positive Scores):**
- Personal obedience to commandments
- Righteous living and moral behavior
- Self-improvement and perfection
- Earning blessings through actions
- Personal responsibility for salvation

**Balanced (Zero Score):**
- Integration of divine grace and human effort
- Faith manifested through works
- Grace that enables righteous action
- Cooperative salvation (God and human working together)

## 💻 Basic Usage

### 1. Process Your First Talk

Start with a small test to ensure everything is working:

```bash
# Process just 5 talks to test your setup
python classifier_production.py --num-talks 5

# Process a specific file
python classifier_production.py --file conference_talks/2021-04-example.html
```

### 2. Process All Available Talks

Once you've confirmed everything works:

```bash
# Process all talks with default settings
python classifier_production.py

# Process with custom model
python classifier_production.py --model gpt-3.5-turbo
```

### 3. Resume from Previous Session

If processing was interrupted:

```bash
# Resume from your last CSV output
python classifier_production.py --resume-from-csv output/labeled_conference_talks_20241201.csv
```

### 4. Launch the Dashboard

Explore your results interactively:

```bash
streamlit run streamlit_app_typed.py
```

## 🔬 Advanced Features

### Batch Processing for Cost Efficiency

Generate a batch file for OpenAI's batch API (50% cost savings):

```bash
# Generate batch input file
python classifier_production.py --generate-batch-input batch_requests.jsonl --num-talks 100

# Submit to OpenAI's batch API (separate process)
# Process the results when complete
```

### Performance Optimization

Enable caching and rate limiting for better performance:

```bash
# Slow but careful processing
python classifier_production.py --rate-limit 1.0

# Fast processing (watch your rate limits!)
python classifier_production.py --rate-limit 0.05

# Disable progress bars for production
python classifier_production.py --no-progress --log-json
```

### Production Monitoring

For production environments:

```bash
# JSON logging for monitoring systems
python classifier_production.py --log-json --log-level INFO

# Debug mode for troubleshooting
python classifier_production.py --log-level DEBUG
```

### Custom Configuration

Set environment variables for consistent behavior:

```bash
# Set via environment
export OPENAI_MODEL=gpt-4-turbo
export LOG_LEVEL=WARNING
export RATE_LIMIT_SECONDS=0.5

# Or use .env file (copy from env.example)
cp env.example .env
# Edit .env with your settings
```

## 📊 Dashboard Guide

### Navigation

The Streamlit dashboard provides several views:

1. **Overview Tab**: Summary statistics and key metrics
2. **Time Series**: Trends over time
3. **Speaker Analysis**: Individual speaker patterns
4. **Score Distribution**: Overall classification patterns

### Interactive Features

**Filtering Options:**
- **Date Range**: Filter by conference dates
- **Score Range**: Focus on specific theological emphases
- **Speaker Selection**: Analyze specific speakers
- **Conference Sessions**: Filter by session type

**Visualization Types:**
- **Line Charts**: Score trends over time
- **Bar Charts**: Speaker comparisons
- **Histograms**: Score distributions
- **Scatter Plots**: Relationship analysis

### Exporting Data

From the dashboard you can:
- Download filtered data as CSV
- Export charts as images
- Copy data to clipboard
- Generate summary reports

## ⚡ Performance Optimization

### Understanding Processing Time

**Factors affecting speed:**
- Number of talks to process
- Talk length and complexity
- OpenAI API response time
- Rate limiting settings
- Network connectivity

**Typical processing times:**
- 10 talks: ~2 minutes
- 100 talks: ~15 minutes  
- 1000 talks: ~2.5 hours

### Optimization Strategies

**1. Use Caching**
```bash
# Enable caching (default)
python classifier_production.py
# Classification cache prevents duplicate API calls
```

**2. Adjust Rate Limiting**
```bash
# Faster (higher risk of rate limits)
python classifier_production.py --rate-limit 0.05

# Safer for large batches
python classifier_production.py --rate-limit 0.5
```

**3. Batch Processing**
```bash
# Process in smaller chunks
python classifier_production.py --num-talks 50
# Then resume with remaining talks
python classifier_production.py --resume-from-csv output/previous_results.csv
```

**4. Choose Appropriate Model**
```bash
# Faster, cheaper (may be less accurate)
python classifier_production.py --model gpt-3.5-turbo

# Slower, more expensive (higher accuracy)
python classifier_production.py --model gpt-4
```

### Cost Management

**Monitor your usage:**
- Check OpenAI usage dashboard regularly
- Set up billing alerts
- Start with small batches to estimate costs

**Cost optimization:**
- Use `gpt-3.5-turbo` for initial exploration
- Use batch API for large processing jobs
- Cache results to avoid reprocessing

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. API Key Problems

**Error**: `Invalid API key`
```bash
# Check your API key
echo $OPENAI_API_KEY

# Verify in .env file
cat .env | grep OPENAI_API_KEY

# Test API connectivity
python test_openai_api.py
```

#### 2. Rate Limiting Issues

**Error**: `Rate limit exceeded`
```bash
# Increase delay between calls
python classifier_production.py --rate-limit 1.0

# Check your OpenAI usage dashboard
# Consider upgrading your OpenAI plan
```

#### 3. File Processing Issues

**Error**: `No files found`
```bash
# Check directory structure
ls conference_talks/

# Verify file format (should be HTML)
file conference_talks/*.html

# Check permissions
ls -la conference_talks/
```

#### 4. Memory Issues

**Error**: `Memory error` or slow processing
```bash
# Process in smaller batches
python classifier_production.py --num-talks 50

# Clear Python cache
rm -rf __pycache__ .mypy_cache .pytest_cache

# Restart your terminal/environment
```

#### 5. Network/Timeout Issues

**Error**: `Connection timeout`
```bash
# Check internet connectivity
ping api.openai.com

# Increase timeout (if supported)
export API_TIMEOUT=120

# Try processing a single file
python classifier_production.py --file conference_talks/single_file.html
```

### Getting Help

**Check logs:**
```bash
# View recent logs
tail -f logs/classifier_$(date +%Y%m%d).log

# Debug mode
python classifier_production.py --log-level DEBUG
```

**Verify setup:**
```bash
# Run tests
pytest

# Check type safety
mypy models.py processors/ utils/
```

## 💡 Best Practices

### Data Preparation

**File Organization:**
- Keep talk files in `conference_talks/` directory
- Use consistent naming conventions
- Ensure files are in HTML format
- Remove or handle corrupt files

**Backup Strategy:**
- Backup original talk files
- Save intermediate results frequently
- Keep multiple CSV outputs with timestamps

### Processing Strategy

**Start Small:**
1. Test with 5-10 talks first
2. Verify classification accuracy
3. Adjust settings if needed
4. Process larger batches

**Monitor Progress:**
- Use progress bars to track processing
- Check intermediate CSV files
- Monitor API usage and costs
- Watch for error patterns

### Quality Assurance

**Validate Results:**
- Manually review a sample of classifications
- Check for consistent scoring patterns
- Look for obvious misclassifications
- Compare similar talks by the same speaker

**Continuous Improvement:**
- Update prompt templates if needed
- Adjust model selection based on accuracy
- Refine processing parameters
- Document any issues and solutions

### Production Deployment

**Environment Setup:**
- Use production-grade logging
- Set appropriate rate limits
- Enable monitoring and alerting
- Use environment variables for configuration

**Monitoring:**
```bash
# Production logging
python classifier_production.py --log-json --log-level INFO

# Monitor costs and usage
# Set up alerts for unusual patterns
# Regular backup of results
```

## 📈 Understanding Your Results

### Interpreting Scores

**Individual Talk Analysis:**
- Look at both score and explanation
- Consider key phrases extracted
- Check for consistency with manual assessment
- Note any surprising classifications

**Aggregate Analysis:**
- Examine trends over time
- Compare speakers and sessions
- Look for seasonal patterns
- Identify theological shifts

**Statistical Patterns:**
- Most talks score between -1 and +1 (balanced)
- Extreme scores (-3, +3) are rare but significant
- Speaker consistency varies
- Conference sessions may have themes

### Data Export and Sharing

**CSV Format:**
The output CSV contains:
- Filename and metadata
- Speaker information
- Classification score and explanation
- Key phrases identified
- Model used for classification

**Dashboard Exports:**
- Charts as PNG/SVG images
- Filtered data as CSV
- Summary statistics
- Time-series data

## 🔧 Customization Options

### Prompt Engineering

Edit templates in `templates/` directory to customize:
- Classification criteria
- Output format
- Emphasis areas
- Cultural context

### Model Selection

Choose based on your needs:
- **GPT-4**: Highest accuracy, slower, more expensive
- **GPT-4-turbo**: Good balance of speed and accuracy
- **GPT-3.5-turbo**: Fastest, cheapest, adequate for most uses

### Custom Scoring Scales

While the default is -3 to +3, you can modify the system for:
- Different theological frameworks
- Alternative emphasis areas
- Custom analytical dimensions
- Comparative studies

## 📚 Further Reading

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [Conference Talk Grace-Works Research Papers](https://example.com/research)

## 🤝 Community and Support

**Getting Help:**
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Documentation for detailed guides
- Contributing guidelines for improvements

**Contributing:**
- See [CONTRIBUTING.md](../CONTRIBUTING.md)
- Report bugs and suggest features
- Improve documentation
- Share your research findings

---

**Happy analyzing!** 🎉

This tool opens up fascinating possibilities for understanding theological emphasis in religious discourse. We're excited to see what insights you discover! 