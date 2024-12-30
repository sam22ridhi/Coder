
---

# Code Documentation AI

**Code Documentation AI** is an AI-powered tool designed to automatically generate precise documentation, improve code quality, and provide meaningful comments for your codebase. It helps developers streamline the documentation process, enhance code readability, and ensure security and efficiency. 

This application offers various features like:

- Automatic code analysis
- Commenting on Python code files
- Code refactoring suggestions
- Generation of detailed documentation
- Identification of dependencies and relationships
- Sanitization of sensitive information

## Features

### 1. **Code Analysis**
   - Analyzes the structure and functionality of Python code.
   - Identifies relationships between files and dependencies.
   - Provides insights into code organization, main entry points, and important modules.

### 2. **Code Commenting**
   - Adds detailed comments to Python code to improve developer readability.
   - Focuses on function, class, logic explanations, and variable descriptions.

### 3. **Code Refactoring**
   - Suggests and implements improvements to code structure and readability.
   - Enhances modularity, reduces duplication, and follows best practices.

### 4. **Error and Exception Handling**
   - Documents error-handling mechanisms, explaining scenarios for possible exceptions.

### 5. **Test Case Documentation**
   - Suggests and documents potential test cases for the codebase.

### 6. **Code Optimization**
   - Identifies potential optimizations and suggests improvements to enhance performance.

### 7. **Research Assistant**
   - Gathers additional information about libraries, dependencies, and tools identified in the code.
   - Researches libraries/tools that are not well-documented.

### 8. **Usage Guide Creator**
   - Generates a practical guide for using the provided Python code effectively.

### 9. **Directory Support**
   - Supports analysis of an entire directory and its contents, not just individual files.
   - Creates documentation and comments for all code files in a directory.

## Prerequisites

Before running the application, make sure you have the following installed:

- Python 3.x
- Streamlit
- CrewAI
- dotenv
- Dependencies as mentioned in `requirements.txt`

## Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/code-documentation-ai.git
   ```

2. Navigate to the project folder:

   ```bash
   cd code-documentation-ai
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file for environment variables and add necessary configurations.

## How to Use

1. Launch the application:

   ```bash
   streamlit run app.py
   ```

2. Choose one of the input methods:
   - **Upload a Python file**: Upload a single `.py` file for documentation and commenting.
   - **Enter Directory Path**: Enter the path to a directory containing Python code to analyze, comment, and generate documentation for all files.

3. The application will process the files, providing:
   - Commented Python files.
   - A comprehensive documentation file in markdown format.
   - Insights into the structure, dependencies, and functionality of the codebase.

## Tools Used

- **CrewAI**: A framework for managing multi-agent systems for complex tasks.
- **LLMs**: Large Language Models used for generating code comments, documentation, and insights.
- **Streamlit**: Web framework to build the user interface for this tool.
- **dotenv**: Manage environment variables for API keys and configurations.

## Example Workflow

1. **Input**: User uploads a Python file or provides a directory path.
2. **Processing**: The application analyzes the code and performs the following tasks:
   - Comment the code.
   - Refactor and optimize the code if necessary.
   - Generate documentation.
   - Provide insights into the code’s structure, dependencies, and key components.
3. **Output**: The output includes:
   - A newly commented file with meaningful comments.
   - A markdown documentation file describing the project, its structure, dependencies, and usage.

## Contributing

Contributions are welcome! Please feel free to fork the repository, submit issues, and send pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
