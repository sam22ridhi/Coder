import streamlit as st
import asyncio
import os
from crewai.process import Process
from crewai_tools import FileReadTool, SerperDevTool, DirectoryReadTool,FileWriterTool
from tempfile import NamedTemporaryFile
from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv
import shutil

load_dotenv()
st.title("Code Documentation AI")
    
llm = LLM("groq/llama-3.3-70b-versatile")
documentation_llm = LLM(
    model="gemini/gemini-1.5-flash-latest",
    temperature=0.7
)
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory = DirectoryReadTool()
write = FileWriterTool()

def get_python_files(directory_path):
    """Get all files from the specified directory."""
    python_files = []
    extensions = [".py", ".js", ".html", ".css"]
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                python_files.append(os.path.join(root, file))
    return python_files

def save_commented_file(original_path, content):
    """Save the commented file back to the original directory with '_commented' suffix."""
    directory = os.path.dirname(original_path)
    filename = os.path.basename(original_path)
    name, ext = os.path.splitext(filename)
    new_path = os.path.join(directory, f"{name}_commented{ext}")
    
    with open(new_path, 'w') as f:
        f.write(content)
    return new_path

def CodeCrew(directory_path=None,file_path=None):

    code_analyzer = Agent(
        role="Code Analyzer",
        goal="Understand the structure and functionality of the given Python code file",
        backstory="Experienced software architect with expertise in reading and interpreting code.",
        verbose=True,
        llm=documentation_llm,
        tools = [directory]
    )

    entity_cleaner = Agent(
        role="Named Entity Cleaner",
        goal="Identify named entities (e.g., personal names, organizations, IDs) in the code and redact or anonymize them to ensure privacy and security.",
        backstory="Security-focused code cleaner specializing in identifying sensitive information, such as personal names, API keys, organization names, and IDs, and safely replacing them with anonymized placeholders.",
        verbose=True,
        llm=documentation_llm,
        tools=[directory]
    )

    insight_gatherer = Agent(
        role="Insight Gatherer",
        goal="Extract and provide detailed insights into the code, including its structure, dependencies, and imports.",
        backstory="Expert Python code reviewer and software engineer who excels at identifying key components of the codebase, pinpointing dependencies, and analyzing imports.",
        verbose=True,
        llm=documentation_llm
    )

    research_assistant = Agent(
        role="Code Research Assistant",
        goal="Gather additional information about libraries, dependencies, and tools identified in the code to assist the documenter agent in creating comprehensive documentation.",
        backstory="Skilled researcher with access to vast online resources, specializing in understanding programming libraries, frameworks, and tools to enhance project documentation.",
        verbose=True,
        llm=documentation_llm,
        memory=True,
		#tools=[search_tool]
    )

    commenter = Agent(
        role="Code Commenter",
        goal="Enhance the Python code with meaningful and precise comments.",
        backstory="Meticulous software engineer who prioritizes code clarity and maintainability.",
        verbose=True,
        llm=documentation_llm
    )
    
    refactoring_agent = Agent(
        role="Code Refactorer",
        goal="Analyze and improve code structure while maintaining functionality",
        backstory="""Senior software architect specializing in code refactoring and modernization. 
        Expert in identifying code smells, applying design patterns, and improving code quality 
        while ensuring the original functionality remains unchanged.""",
        verbose=True,
        llm=documentation_llm,
)

    documenter = Agent(
        role="Documentation Writer",
        goal="Create comprehensive documentation for the Python code.",
        backstory="Technical writer skilled at explaining complex concepts in a simple way.",
        verbose=True,
        llm=documentation_llm
    )

    optimizer = Agent(
        role="Optimization Advisor",
        goal="Identify potential optimizations in the given Python code.",
        backstory="Veteran developer with deep knowledge of performance and structural improvements.",
        verbose=True,
        llm=documentation_llm
    )

    error_handler = Agent(
        role="Error and Exception Handler Documenter",
        goal="Document error-handling mechanisms in the code, explaining scenarios for possible exceptions.",
        backstory="Debugger with expertise in analyzing and documenting fault-tolerant code.",
        verbose=True,
        llm=llm
    )

    tester = Agent(
        role="Test Case Documenter",
        goal="Suggest and document test cases for the code.",
        backstory="QA engineer who ensures robust and reliable code by creating comprehensive test strategies.",
        verbose=True,
        llm=llm
    )

    usage_guide_creator = Agent(
        role="Usage Guide Creator",
        goal="Develop a practical guide on how to use the provided Python code effectively.",
        backstory="Developer with a passion for creating example-driven guides that simplify usage.",
        verbose=True,
        llm=documentation_llm
    )

    idea_agent = Agent(
        role="Idea Generator",
        goal="Generate creative and relevant ideas for the content based on user inputs.",
        backstory="Expert in brainstorming and ideation, helping to establish a strong foundation for content creation.",
        verbose=True,
        llm=documentation_llm
    )
    
    analyze_code_task = Task(
        description="""Perform a comprehensive analysis of the Python codebase:
        1. If directory_path is provided ({directory_path}):
           - Analyze all the code files in the directory
           - Identify relationships between files
           - Document the project structure
           - Analyze import dependencies between files
           - Identify shared utilities and common patterns
        
        Process multiple/all files simultaneously
        Focus on:
        - Project architecture and structure
        - Inter-file dependencies and relationships
        - Common patterns and shared utilities
        - Main entry points and important modules
        """,
        expected_output="""A detailed analysis report including:
        1. Project Structure Overview
        2. File Relationships and Dependencies
        3. Key Components and Their Roles
        4. Architectural Patterns
        5. Important Code Paths
        """,
        agent=code_analyzer,
        tools = [file_read_tool,file_read_tool,directory],
        memory=True
    )

    clean_entities_task = Task(
        description="""Review and sanitize sensitive information across the codebase:
        Directory: {directory_path} 
         Process multiple/all files simultaneously
        1. Scan all relevant coding files for sensitive information
        2. Maintain consistency in anonymization across files
        3. Preserve functionality while removing sensitive data
        4. Document all replacements made
        """,
        expected_output="Return a sanitized Python file with anonymized sensitive entities.",
        agent=entity_cleaner,
        output_file='clean.py',
        memory=True
        
    )

    gather_insights_task = Task(
        description="""Analyze the Python code to extract insights about its structure, dependencies, imports, and functionality. 
    File path: {directory_path} 
        """,
        expected_output=" A detailed report summarizing the dependencies, key imports,tools,libraries and overall purpose of the code, providing clear insights for documentation purposes.",
        agent=insight_gatherer,
        output_file='insights.md',
        memory=True,
        tools=[directory]
    )

    research_entities_task = Task(
        description="""
        Use the insights from the provided code, such as identified libraries, tools, and techniques, to gather relevant information from the internet **only for libraries, tools, or techniques that are not already known or well-documented**. 
        To avoid rate-limit errors and minimize search requests, follow these strategies:
        
        1. **Check for Known Libraries/Tools First**: 
        - Avoid searching for well-known libraries (like NumPy, Pandas, etc.) if sufficient knowledge is already available.
        - If documentation for a library/tool is commonly available or can be inferred, skip the search and rely on known information.

        2. **Batch and Optimize Search Requests**: 
        - Combine multiple unknown libraries, tools, or techniques into a **single search query** (e.g., "TensorRT, Timm, Albumentations documentation").
        - Extract multiple pieces of information from a single result (official docs, guides, tutorials, etc.).
        
        3. **Rate-Limit Awareness**: 
        - Introduce a small delay between successive search requests if required. 
        - Avoid sending multiple back-to-back queries for different tools or concepts. 
        - If rate limits are encountered, **pause and retry after a short delay** instead of sending repeated requests.

        4. **Comprehensive Report**: 
        - Provide a detailed research report for **each unknown library, tool, or technique**. Each entry should have:
            - **Name of the Library/Tool/Technique**
            - **Short Description**
            - **Link to Official Documentation** (or a high-quality, reputable source)
            - **Additional Resources (Optional, if helpful)**
        """,
        expected_output="""
        A well-structured research report containing clear explanations, descriptions, and relevant documentation links 
        for libraries, tools, or techniques **that were not previously known**. Each entry should include:
        - **Name of the Library/Tool/Technique**
        - **Short Description**
        - **Link to Official Documentation**
        - **Additional Resources (Optional)**
        """,
        agent=research_assistant,
        tools=[search_tool],
        memory=True,
        #context=code_analyzer
    )


    comment_code_task = Task(
        description=""" Process multiple/all files simultaneously. Add detailed and meaningful comments to the Python code to improve readability.
        Focus on:
        1. Function documentation
        2. Class documentation
        3. Complex logic explanation
        4. Important variable descriptions
        If {directory_path} exists comment all the files in the directory
        """,
        expected_output="Each file in the {directory_path} will be updated with comments to improve developer readability.",
        agent=commenter,
        output_file="commented.py ",
        memory=True,  
        tools=[file_read_tool,directory,write]
        #context=[code_analyzer]
    )
    
    refactoring_task = Task(
    description="""Analyze and refactor the code while maintaining its functionality:
    1. Identify code smells and anti-patterns
    2. Suggest and implement design pattern improvements
    3. Optimize code structure and organization
    4. Improve naming conventions and readability
    5. Enhance modularity and reusability
    6. Reduce code duplication
    7. Optimize imports and dependencies
    8. Apply modern coding practices
    
    For each file in {directory_path}, provide:
    - List of identified issues
    - Refactoring suggestions
    - Improved code implementation
    - Explanation of changes made
    
    Focus on:
    - SOLID principles
    - DRY (Don't Repeat Yourself)
    - Clean Code principles
    - Performance optimization
    - Modern language features
    - Best practices for the specific language
    """,
    expected_output="""Each file in the {directory_path} will be updated with refactored code to improve developer readability""",
    agent=refactoring_agent,
    output_file="refactored_code.py",
    memory=True,
    tools=[file_read_tool, directory, write]
)

    generate_documentation_task = Task(
        description="""Create comprehensive project documentation i.e a detailed markdown file documenting the code's overiew, frameworks, purpose, functionality, and usage covering all aspects of a well written markdown file.
        Directory: {directory_path} 
        If multiple files exist it should contain above information for all the files
 
        """,
        expected_output="A well-structured documentation file explaining the overview of the code/framework overview,purpose,how to navigate,structure,multiple files and usage of the code and any additional notes in depth, also add links if required",
        agent=documenter,
        output_file='documentation.md',
        memory=True,
        context=[research_entities_task],
        tools=[file_read_tool,directory]
    )

    crew = Crew(
        agents=[code_analyzer, entity_cleaner, insight_gatherer,research_assistant, commenter,refactoring_agent, documenter],
        tasks=[analyze_code_task, clean_entities_task, gather_insights_task,research_entities_task,comment_code_task,refactoring_task,generate_documentation_task],
        process=Process.sequential,
        verbose=True
    )
    
   # Create output directory for documentation
    output_dir = "documentation_output"
    os.makedirs(output_dir, exist_ok=True)
    
    results = crew.kickoff(inputs={"directory_path" :directory_path, "file_path":file_path})
    return results

    # Handle commented file
    if os.path.exists('commented.py'):
        with open('commented.py', 'r') as f:
            commented_content = f.read()
        if file_path:
            commented_file_path = save_commented_file(file_path, commented_content)
            st.success(f"Commented file saved at: {commented_file_path}")
    
    # Handle documentation
    if os.path.exists('documentation.md'):
        doc_filename = f"documentation_{os.path.basename(file_path or directory_path)}.md"
        doc_path = os.path.join(output_dir, doc_filename)
        shutil.copy('documentation.md', doc_path)
        
        with open(doc_path, 'r') as f:
            documentation_content = f.read()
        return documentation_content
    
    return None


st.sidebar.image("LOGO.png", use_container_width=True)
st.sidebar.title("Code Documentation AI")
st.sidebar.info(
    "This application generates precise code documentation and provides features like commented files, insights, and more. Streamline your development process with AI-powered assistance!"
)
st.markdown("### Choose Input Method")
input_method = st.radio("Select input method:", ["Upload Single File", "Enter Directory Path"])

if input_method == "Upload Single File":
    uploaded_file = st.file_uploader("📂 **Upload Your Python File (.py)**", type=["py"], accept_multiple_files=False)
    
    if uploaded_file:
        with NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(uploaded_file.read())
            file_path = temp_file.name
        st.success(f"Successfully uploaded: **{uploaded_file.name}**")
        
        with open(file_path, 'r') as file:
            file_content = file.read()

        if st.button("📜 **View Python File**"):
            st.subheader("📃 **Your Uploaded Python Code**")
            st.code(file_content, language='python')
            
        if st.button("🌟 **Generate Documentation**"):
            with st.spinner("Processing the file and generating documentation. Please wait..."):
                documentation_content = CodeCrew(file_path=file_path)
                if documentation_content:
                    st.success("Documentation generated successfully!")
                    
                    st.subheader("📖 **Generated Documentation**")
                    st.download_button(
                        "Download Documentation",
                        data=documentation_content,
                        file_name="documentation.md"
                    )
                    
                    with st.expander("Click here to view the documentation", expanded=True):
                        st.markdown(documentation_content)
                else:
                    st.error("Failed to generate documentation!")

else:
    directory_path = st.text_input("📁 **Enter Directory Path**", 
                                 placeholder="e.g., /path/to/your/python/files")
    
    if directory_path and os.path.isdir(directory_path):
        python_files = get_python_files(directory_path)
        if not python_files:
            st.warning("No coding files found in the specified directory.")
        else:
            st.success(f"Found {len(python_files)} Coding files in the directory")
            if st.button("📜 **View Found Files**"):
                st.subheader("📃 ** Files in Directory**")
                for file_path in python_files:
                    st.write(f"- {os.path.basename(file_path)}")
                    
            if st.button("🌟 **Generate Documentation for All Files**"):
                with st.spinner("Processing all files and generating documentation. Please wait..."):
                    for file_path in python_files:
                        st.write(f"Processing: {os.path.basename(file_path)}")
                        results = CodeCrew(directory_path=directory_path, file_path=file_path)
            
                    documentation_path = '/Users/sam22ridhi/Downloads/project/documentation.md'
                    if os.path.exists(documentation_path):
                        with open(documentation_path, 'r') as doc_file:
                            documentation_content = doc_file.read()
                        
                        st.subheader("📖 **Generated Documentation**")
                        st.download_button("Download Documentation", data=documentation_content, file_name="documentation.md")
                        st.markdown("""
                            <style>
                                .markdown-doc-container {
                                    background-color: #ffffff;
                                    border-radius: 10px;
                                    padding: 20px;
                                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                                }
                            </style>
                        """,unsafe_allow_html=True)
                        
                        with st.expander("Click here to view the documentation", expanded=True):
                            st.markdown(f"<div class='markdown-doc-container'>{documentation_content}</div>", unsafe_allow_html=True)
                    else:
                        st.error("Documentation file not found!")
                        
    elif directory_path:
        st.error("Invalid directory path. Please enter a valid directory path.")
