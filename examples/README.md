# Examples

Example scripts demonstrating Jazz RAG system capabilities.

## Scripts

### Basic Extraction
**demo_extraction.py**
- Demonstrates basic fact extraction from web content
- Shows how to use the main RAG pipeline
- Includes example queries and output formatting

### Enhanced Extraction
**demo_extraction_enhanced.py**
- Showcases the two-stage RAG enhancement pipeline
- Demonstrates adaptive research capabilities
- Shows improved fact extraction and synthesis

## Running Examples

```bash
# Run basic extraction demo
python demo_extraction.py

# Run enhanced extraction demo
python demo_extraction_enhanced.py
```

## Output

Each example will:
1. Accept a user query
2. Search the web and knowledge base
3. Extract relevant facts
4. Synthesize a comprehensive response
5. Display the results with confidence scores

## Learning Path

1. Start with **demo_extraction.py** to understand basic operation
2. Progress to **demo_extraction_enhanced.py** to see advanced features
3. Review the test suite in `../tests/` for more complex scenarios
4. Check the main README and documentation in `../docs/` for implementation details
