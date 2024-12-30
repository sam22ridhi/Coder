import streamlit as st
import os
from crewai.process import Process
from crewai_tools import FileReadTool, SerperDevTool, DirectoryReadTool, FileWriterTool
from tempfile import NamedTemporaryFile
from crewai import Agent, Crew, Process, Task, LLM
from dotenv import load_dotenv
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
st.title("Code Documentation AI")

# Initialize LLMs and tools
llm = LLM("groq/llama-3.3-70b-versatile")
documentation_llm = LLM(
    model="gemini/gemini-1.5-flash-latest",
    temperature=0.7
)
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory_tool = DirectoryReadTool()
write_tool = FileWriterTool()

class Agents:
    """Class to manage all agents"""
    
    @staticmethod
    def create_code_analyzer():
        return Agent(
            role="Code Analyzer",
            goal="Understand the structure and functionality of code files comprehensively.",
            backstory="Experienced software architect with expertise in reading and interpreting code across multiple languages and frameworks.",
            verbose=True,
            llm=documentation_llm,
            tools=[directory_tool, file_read_tool]
        )

    @staticmethod
    def create_entity_cleaner():
        return Agent(
            role="Named Entity Cleaner",
            goal="Identify and sanitize sensitive information in code while maintaining functionality.",
            backstory="Security-focused code cleaner specializing in identifying and anonymizing sensitive information.",
            verbose=True,
            llm=documentation_llm,
            tools=[directory_tool, file_read_tool]
        )

    @staticmethod
    def create_insight_gatherer():
        return Agent(
            role="Insight Gatherer",
            goal="Extract detailed insights about code structure, dependencies, and patterns.",
            backstory="Expert code reviewer who excels at identifying key components and patterns.",
            verbose=True,
            llm=documentation_llm,
            tools=[directory_tool, file_read_tool]
        )

    @staticmethod
    def create_research_assistant():
        return Agent(
            role="Code Research Assistant",
            goal="Research and provide context about libraries, frameworks, and tools used.",
            backstory="Skilled researcher specializing in programming technologies and best practices.",
            verbose=True,
            llm=documentation_llm,
            memory=True,
            tools=[search_tool]
        )

    @staticmethod
    def create_commenter():
        return Agent(
            role="Code Commenter",
            goal="Add detailed, context-aware comments to improve code readability.",
            backstory="Expert developer focused on code clarity and documentation.",
            verbose=True,
            llm=documentation_llm,
            tools=[file_read_tool, write_tool]
        )

    @staticmethod
    def create_documenter():
        return Agent(
            role="Documentation Writer",
            goal="Create comprehensive, well-structured documentation for code.",
            backstory="Technical writer skilled at creating clear, thorough documentation.",
            verbose=True,
            llm=documentation_llm,
            tools=[file_read_tool, write_tool]
        )

    @staticmethod
    def create_optimizer():
        return Agent(
            role="Optimization Advisor",
            goal="Identify and suggest code optimizations and improvements.",
            backstory="Performance optimization specialist with extensive refactoring experience.",
            verbose=True,
            llm=documentation_llm
        )

    @staticmethod
    def create_error_handler():
        return Agent(
            role="Error Handler Documenter",
            goal="Document error handling patterns and potential failure points.",
            backstory="Expert in defensive programming and robust error handling.",
            verbose=True,
            llm=llm
        )

    @staticmethod
    def create_tester():
        return Agent(
            role="Test Case Documenter",
            goal="Design and document comprehensive test strategies.",
            backstory="QA engineer specializing in test coverage and quality assurance.",
            verbose=True,
            llm=llm
        )

    @staticmethod
    def create_usage_guide_creator():
        return Agent(
            role="Usage Guide Creator",
            goal="Create practical guides and examples for code usage.",
            backstory="Developer advocate focused on creating user-friendly documentation.",
            verbose=True,
            llm=documentation_llm
        )

class Tasks:
    """Class to manage all tasks"""
    
    @staticmethod
    def create_analysis_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Analyze code file at {file_path}:
            1. Identify overall structure and architecture
            2. Document key components and their relationships
            3. Analyze dependencies and imports
            4. Identify design patterns and architectural decisions
            5. Evaluate code organization and modularity
            """,
            expected_output="""Detailed analysis report including:
            1. Code Structure Overview
            2. Component Analysis
            3. Dependency Map
            4. Design Pattern Identification
            5. Architecture Recommendations
            """,
            agent=agent,
            output_file=f"analysis_{os.path.basename(file_path)}.md"
        )

    @staticmethod
    def create_cleaning_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Review and sanitize {file_path}:
            1. Identify sensitive information (API keys, credentials, etc.)
            2. Detect and anonymize personal data
            3. Remove or mask security-sensitive details
            4. Document all sanitization actions
            """,
            expected_output="Sanitized code file with documentation of changes",
            agent=agent,
            output_file=f"cleaned_{os.path.basename(file_path)}"
        )

    @staticmethod
    def create_insight_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Extract insights from {file_path}:
            1. Identify key functionalities
            2. Document code patterns
            3. Analyze complexity and maintainability
            4. Review error handling approaches
            """,
            expected_output="Comprehensive insights report",
            agent=agent,
            output_file=f"insights_{os.path.basename(file_path)}.md"
        )

    @staticmethod
    def create_research_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Research technologies used in {file_path}:
            1. Identify external dependencies
            2. Research best practices
            3. Find relevant documentation
            4. Gather community insights
            """,
            expected_output="Technology research report",
            agent=agent,
            output_file=f"research_{os.path.basename(file_path)}.md"
        )

    @staticmethod
    def create_commenting_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Add comprehensive comments to {file_path}:
            1. Document function purposes
            2. Explain complex logic
            3. Add context to important sections
            4. Include usage examples
            """,
            expected_output="Well-commented code file",
            agent=agent,
            output_file=f"commented_{os.path.basename(file_path)}"
        )

    @staticmethod
    def create_documentation_task(file_path: str, agent: Agent) -> Task:
        return Task(
            description=f"""Create complete documentation for {file_path}:
            1. Overview and purpose
            2. Installation instructions
            3. Usage examples
            4. API documentation
            5. Configuration options
            """,
            expected_output="Complete markdown documentation",
            agent=agent,
            output_file=f"docs_{os.path.basename(file_path)}.md"
        )

class FileProcessor:
    """Handles the processing of individual files"""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        return {
            'analyzer': Agents.create_code_analyzer(),
            'cleaner': Agents.create_entity_cleaner(),
            'insight_gatherer': Agents.create_insight_gatherer(),
            #'researcher': Agents.create_research_assistant(),
            'commenter': Agents.create_commenter(),
            'documenter': Agents.create_documenter(),
            #'optimizer': Agents.create_optimizer(),
            #'error_handler': Agents.create_error_handler(),
            #'tester': Agents.create_tester(),
            #'usage_guide_creator': Agents.create_usage_guide_creator()
        }

    async def process_file(self, file_path: str) -> Dict:
        """Process a single file through all agents concurrently"""
        tasks = []
        
        # Create tasks for each agent
        tasks.extend([
            Tasks.create_analysis_task(file_path, self.agents['analyzer']),
            Tasks.create_cleaning_task(file_path, self.agents['cleaner']),
            Tasks.create_insight_task(file_path, self.agents['insight_gatherer']),
            #Tasks.create_research_task(file_path, self.agents['researcher']),
            Tasks.create_commenting_task(file_path, self.agents['commenter']),
            Tasks.create_documentation_task(file_path, self.agents['documenter'])
        ])
        
        # Create crew for concurrent processing
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        try:
            results = await asyncio.to_thread(crew.kickoff)
            return results
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None

class DocumentationGenerator:
    """Manages the overall documentation generation process"""
    
    def __init__(self, output_dir: str = "documentation_output"):
        self.output_dir = output_dir
        self.file_processor = FileProcessor()
        os.makedirs(output_dir, exist_ok=True)

    async def process_directory(self, directory_path: str) -> List[Dict]:
        """Process all files in directory with chunking"""
        files = self._get_code_files(directory_path)
        results = []
        
        # Process files in chunks
        chunk_size = 3
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            chunk_results = await asyncio.gather(
                *[self.file_processor.process_file(f) for f in chunk]
            )
            results.extend(chunk_results)
            
            # Update progress
            progress = (i + len(chunk)) / len(files)
            st.progress(progress)
        
        return results

    def _get_code_files(self, directory_path: str) -> List[str]:
        """Get all supported code files from directory"""
        extensions = {".py", ".js", ".html", ".css"}
        files = []
        for root, _, filenames in os.walk(directory_path):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
        return files

    def consolidate_documentation(self, results: List[Dict]) -> str:
        """Combine all documentation into a single comprehensive document"""
        consolidated = []
        
        for result in results:
            if result and isinstance(result, dict):
                for agent_role, content in result.items():
                    if content:
                        consolidated.append(f"## {agent_role}\n\n{content}\n\n")
        
        return "\n".join(consolidated)

def main():
    st.sidebar.image("LOGO.png", use_container_width=True)
    st.sidebar.title("Code Documentation AI")
    st.sidebar.info(
        "Advanced AI-powered code documentation generator with concurrent processing!"
    )

    input_method = st.radio("Select input method:", ["Upload Single File", "Enter Directory Path"])
    
    doc_generator = DocumentationGenerator()

    if input_method == "Upload Single File":
        handle_single_file_upload(doc_generator)
    else:
        handle_directory_input(doc_generator)

def handle_single_file_upload(doc_generator):
    uploaded_file = st.file_uploader("📂 Upload Your Code File", 
                                   type=["py", "js", "html", "css"], 
                                   accept_multiple_files=False)
    
    if uploaded_file and st.button("🌟 Generate Documentation"):
        with st.spinner("Processing file..."):
            with NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())
                results = asyncio.run(doc_generator.file_processor.process_file(temp_file.name))
                display_results(results, doc_generator)

def handle_directory_input(doc_generator):
    directory_path = st.text_input("📁 Enter Directory Path")
    
    if directory_path and os.path.isdir(directory_path) and st.button("🌟 Generate Documentation"):
        with st.spinner("Processing directory..."):
            results = asyncio.run(doc_generator.process_directory(directory_path))
            display_results(results, doc_generator)

def display_results(results: List[Dict], doc_generator: DocumentationGenerator):
    if results:
        st.success("Documentation generated successfully!")
        
        # Consolidate documentation
        consolidated_docs = doc_generator.consolidate_documentation(results)
        
        # Save consolidated documentation
        doc_path = os.path.join(doc_generator.output_dir, "complete_documentation.md")
        with open(doc_path, 'w') as f:
            f.write(consolidated_docs)
        
        # Display and download options
        st.markdown("### 📖 Generated Documentation")
        st.download_button(
            "⬇️ Download Complete Documentation",
            consolidated_docs,
            file_name="complete_documentation.md"
        )
        
        with st.expander("👀 View Documentation", expanded=True):
            st.markdown("documentation.md")
    else:
        st.error("Failed to generate documentation. Please check the logs for details.")

if __name__ == "__main__":
    main()