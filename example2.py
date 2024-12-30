import streamlit as st
import os
from crewai.process import Process
from crewai_tools import FileReadTool, SerperDevTool,DirectoryReadTool
from tempfile import NamedTemporaryFile
from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv

load_dotenv()
st.title("Code Documentation Agent")
    
llm = LLM("groq/llama-3.3-70b-versatile")
documentation_llm = LLM(
    model="gemini/gemini-1.5-flash-latest",
    temperature=0.7
)
search_tool=SerperDevTool()
file_read_tool = FileReadTool()
directory = DirectoryReadTool()

def get_python_files(directory_path):
    """Get all Python files from the specified directory."""
    python_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def CodeCrew(directory_path=None):

    code_analyzer = Agent(
        role="Code Analyzer",
        goal="Understand the structure and functionality of the given Python code file.",
        backstory="Experienced software architect with expertise in reading and interpreting code.",
        verbose=True,
        llm=documentation_llm,
        tools = [file_read_tool,directory]
    )

    entity_cleaner = Agent(
        role="Named Entity Cleaner",
        goal="Identify named entities (e.g., personal names, organizations, IDs) in the code and redact or anonymize them to ensure privacy and security.",
        backstory="Security-focused code cleaner specializing in identifying sensitive information, such as personal names, API keys, organization names, and IDs, and safely replacing them with anonymized placeholders.",
        verbose=True,
        llm=llm,
        tools=[directory]
    )

    insight_gatherer = Agent(
        role="Insight Gatherer",
        goal="Extract and provide detailed insights into the code, including its structure, dependencies, and imports.",
        backstory="Expert Python code reviewer and software engineer who excels at identifying key components of the codebase, pinpointing dependencies, and analyzing imports.",
        verbose=True,
        llm=llm
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
        1. If directory_path is provided {directory_path}:
           - Analyze all Python files in the directory
           - Identify relationships between files
           - Document the project structure
           - Analyze import dependencies between files
           - Identify shared utilities and common patterns
           
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
        tools = [file_read_tool,directory],
        memory=True
    )

    clean_entities_task = Task(
        description="""Review and sanitize sensitive information across the codebase:
        Directory: {directory_path if directory_path else 'Single file mode'}
        File: {single_file_path if single_file_path else 'Directory mode'}
        
        1. Scan all relevant Python files for sensitive information
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
    File path: {file_path}
        """,
        expected_output=" A detailed report summarizing the dependencies, key imports,tools,libraries and overall purpose of the code, providing clear insights for documentation purposes.",
        agent=insight_gatherer,
        output_file='insights.md',
        memory=True
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
        context=code_analyzer
    )


    comment_code_task = Task(
        description="""Add meaningful and contextual comments to the Python code to improve readability.
    File path: {directory_path}
        """,
        expected_output=" An updated Python file with clear comments for developers to the {directory_path}",
        agent=commenter,
        output_file='commented.py',
        memory=True,  
        tools=[directory]
        #context=code_analyzer]
    )

    generate_documentation_task = Task(
        description="""Create comprehensive project documentation:
        Directory: {directory_path}
        
        Include:
        1. Project Overview
        2. System Architecture
        3. Component Documentation
        4. Setup Instructions
        5. Configuration Guide
        6. API Documentation (if applicable)
        7. Cross-component Relationships 
        """,
        expected_output="A well-structured documentation file explaining the overview of the code/framework overview,purpose,how to navigate,structure, and usage of the code and any additional notes in depth, also add links if required",
        agent=documenter,
        output_file='documentation.md',
        memory=True,
        context=[research_entities_task],
        tools=[directory]
    )

    optimize_code_task = Task(
        description=""" Identify potential optimizations and provide suggestions to improve performance and structure.
    File path: {file_path}
        """,
        expected_output=" A list of optimization suggestions and justifications.",
        agent=optimizer,
        output_file='optimiser.md',
        memory=True
    )

    error_handling_task = Task(
        description="""Document the error-handling mechanisms present in the Python code and explain the scenarios they address.
            File path: {file_path}""",
        expected_output=" A section in the documentation describing the error-handling strategies.",
        agent=error_handler,
        output_file="error_handling.md"
    )

    test_documentation_task = Task(
        description="""Suggest test cases that ensure robust code functionality.
    File path: {file_path}
        """,
        expected_output="A markdown file or section detailing possible test cases.",
        agent=tester,
        output_file="possible_test_cases.md"
    )


    crew = Crew(
        agents=[code_analyzer, entity_cleaner, insight_gatherer,research_assistant, commenter, documenter, optimizer, error_handler, tester],
        tasks=[analyze_code_task, clean_entities_task, gather_insights_task,research_entities_task,comment_code_task, generate_documentation_task, optimize_code_task, error_handling_task, test_documentation_task],
        process=Process.sequential,
        verbose=True
    )
    
    
    results = crew.kickoff(inputs={"directory_path" :directory_path, "file_path":file_path})
    return results


st.sidebar.image("LOGO.png", use_container_width=True)
st.markdown("### Choose Input Method")
input_method = st.radio("Select input method:", ["Upload Single File", "Enter Directory Path"])

if input_method == "Upload Single File":
    directory_path=None
    uploaded_file = st.file_uploader("📂 **Upload Your Python File (.py)**", type=["py"], 
                                   accept_multiple_files=False)
    
    if uploaded_file:
        with NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(uploaded_file.read())
            file_path = temp_file.name
        st.success(f"Successfully uploaded: **{uploaded_file.name}**")
        
        if st.button("📜 **View Python File**"):
            with open(file_path, 'r') as file:
                st.code(file.read(), language='python')
            
        if st.button("🌟 **Generate Documentation**"):
            with st.spinner("Generating documentation..."):
                results = CodeCrew(file_path=file_path)
                st.success("Documentation generated successfully!")
                
                documentation_path = 'documentation.md'
                if os.path.exists(documentation_path):
                    with open(documentation_path, 'r') as doc_file:
                        documentation_content = doc_file.read()
                    
                    st.download_button("Download Documentation", 
                                     data=documentation_content, 
                                     file_name="documentation.md")
                    
                    with st.expander("View Documentation", expanded=True):
                        st.markdown(documentation_content)
                else:
                    st.error("Documentation file not found!")

else:
    file_path=None
    directory_path = st.text_input("📁 **Enter Directory Path**", 
                                 placeholder="e.g., /path/to/your/python/files")
    
    if directory_path and os.path.isdir(directory_path):
        python_files = get_python_files(directory_path)
        if not python_files:
            st.warning("No Python files found in the specified directory.")
        else:
            st.success(f"Found {len(python_files)} Python files in the directory")
            
            if st.button("📜 **View Found Files**"):
                for file in python_files:
                    st.write(f"- {os.path.basename(file)}")
                    
            if st.button("🌟 **Generate Documentation**"):
                with st.spinner("Generating documentation..."):
                    # Fixed: Only pass directory_path here
                    results = CodeCrew(directory_path=directory_path)
                    st.success("Documentation generated successfully!")
                    
                    documentation_path = 'documentation.md'
                    if os.path.exists(documentation_path):
                        with open(documentation_path, 'r') as doc_file:
                            documentation_content = doc_file.read()
                        
                        st.download_button("Download Documentation", 
                                         data=documentation_content, 
                                         file_name="documentation.md")
                        
                        with st.expander("View Documentation", expanded=True):
                            st.markdown(documentation_content)
                    else:
                        st.error("Documentation file not found!")
    elif directory_path:
        st.error("Invalid directory path. Please enter a valid directory path.")