import os
from typing import Dict, Any
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from opencommerce_sdk import OpenCommerceAccountToolkit
from dotenv import load_dotenv
from crewai.tools import BaseTool

# Load environment variables
load_dotenv()

class EVMarketResearchCrew:
    def __init__(self):
        # Initialize OpenCommerce SDK
        self.sdk = OpenCommerceAccountToolkit(network="testnet")
        print("✅ SDK initialized successfully")

        self.address = self.sdk.get_account_address()
        print(f"My account address: {self.address}")
        
        # Initialize agents and tasks
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()
        self.crew = self._create_crew()

    def tavily_search(self, query: str) -> Dict[str, Any]:
        """
        Perform advanced search using Tavily.
        """
        search_request = {
            'query': query,
        }
        return self.sdk.use_service('tavily_search', search_request)

    def gpt_research(self, research_query: str) -> Dict[str, Any]:
        """
        Conduct detailed analysis using GPT Researcher.
        """
        return self.sdk.use_service('gpt_researcher', {
            'query': research_query
        })

    def _create_agents(self) -> Dict[str, Agent]:
        """
        Create specialized research agents.
        """
        # Create proper tool instances
        tavily_tool = TavilySearchTool(self.sdk)
        gpt_tool = GPTResearchTool(self.sdk)

        # Market Research Agent
        market_research_agent = Agent(
            role="Market Research Specialist",
            goal="Gather comprehensive market data about the EV industry",
            backstory="""You are an expert in collecting and analyzing market trends, 
            competitive landscapes, and industry developments. You specialize in 
            automotive and technology sectors, with a deep understanding of global 
            markets and consumer behavior. Your analysis is always data-driven and 
            considers multiple market perspectives.""",
            tools=[tavily_tool],
            verbose=True,
            allow_delegation=True
        )

        # Technology Analysis Agent
        tech_analysis_agent = Agent(
            role="Technology Analyst",
            goal="Analyze technological developments and innovations in the EV space",
            backstory="""You are a technical expert focusing on EV battery technology, 
            charging infrastructure, and manufacturing processes. You have a deep 
            understanding of technical specifications, emerging technologies, and 
            their practical implications. You excel at identifying breakthrough 
            technologies and assessing their market impact.""",
            tools=[gpt_tool],
            verbose=True,
            allow_delegation=True
        )

        # Market Strategy Agent
        strategy_agent = Agent(
            role="Strategic Insights Analyst",
            goal="Synthesize research findings into actionable market insights",
            backstory="""You are a strategic advisor specialized in connecting market 
            research with business opportunities. You excel at identifying market gaps, 
            growth opportunities, and potential risks. Your recommendations are always 
            practical and actionable, backed by solid data and analysis.""",
            tools=[gpt_tool],
            verbose=True,
            allow_delegation=True
        )

        return {
            "market_research": market_research_agent,
            "tech_analysis": tech_analysis_agent,
            "strategy": strategy_agent
        }

    def _create_tasks(self) -> Dict[str, Task]:
        """
        Create research tasks with dependencies.
        """
        # Market Research Task
        market_research_task = Task(
            description="""Conduct comprehensive market research on the EV industry:
            1. Current market size and growth projections
            2. Key players and their market share
            3. Regional market dynamics and growth patterns
            4. Consumer adoption trends and barriers
            5. Regulatory environment and government incentives
            6. Price trends and cost analysis
            7. Supply chain analysis
            
            Format your response as a structured report with clear sections and data points.
            Include specific numbers, percentages, and time frames where possible.""",
            expected_output="Detailed market research report with data-driven insights",
            agent=self.agents["market_research"]
        )

        # Technology Analysis Task
        tech_analysis_task = Task(
            description="""Analyze technological trends in the EV industry, building on the market research:
            1. Battery technology advancements and roadmap
            2. Charging infrastructure development and standards
            3. Manufacturing innovations and processes
            4. Upcoming technological breakthroughs
            5. Technical challenges and potential solutions
            6. Performance metrics and improvements
            7. Sustainability and environmental impact
            
            Reference specific technologies, companies, and development timelines.
            Analyze both current state and future projections.""",
            expected_output="Technical analysis report with focus on innovations and challenges",
            agent=self.agents["tech_analysis"],
            context=[market_research_task]
        )

        # Strategic Insights Task
        strategy_task = Task(
            description="""Synthesize market and technical research into strategic insights:
            1. Key market opportunities and entry points
            2. Competitive advantages and differentiators
            3. Potential risks and mitigation strategies
            4. Growth recommendations by region
            5. Investment implications and timelines
            6. Partnership and collaboration opportunities
            7. Success metrics and KPIs
            
            Provide specific, actionable recommendations backed by the research.
            Include short-term and long-term perspectives.""",
            expected_output="Strategic recommendations report with actionable insights",
            agent=self.agents["strategy"],
            context=[market_research_task, tech_analysis_task]
        )

        return {
            "market_research": market_research_task,
            "tech_analysis": tech_analysis_task,
            "strategy": strategy_task
        }

    def _create_crew(self) -> Crew:
        """
        Create and configure the research crew.
        """
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            verbose=True,
            process=Process.sequential  # Tasks will run in sequence
        )

    def run_research(self) -> Dict[str, str]:
        """
        Execute the research process and return results.
        """
        try:
            print("\n🚀 Starting EV Market Research Process...")
            
            # Execute the research process
            results = self.crew.kickoff()
            
            # Create a timestamped results dictionary
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            research_results = {
                "timestamp": timestamp,
                "market_research": self.tasks["market_research"].output.raw,
                "tech_analysis": self.tasks["tech_analysis"].output.raw,
                "strategy": self.tasks["strategy"].output.raw
            }
            
            print("\n✅ Research process completed successfully!")
            return research_results
            
        except Exception as e:
            print(f"\n❌ Error during research process: {str(e)}")
            raise

class TavilySearchTool(BaseTool):
    name: str = "Tavily Search"
    description: str = "Search the internet for information using Tavily"
    sdk: Any = None

    def __init__(self, sdk):
        super().__init__(sdk=sdk)
        self.sdk = sdk

    def _run(self, query: str) -> str:
        try:
            return self.sdk.use_service('tavily_search', {'query': query})
        except Exception as e:
            print(f"Error in Tavily search: {e}")
            return str(e)

class GPTResearchTool(BaseTool):
    name: str = "GPT Research"
    description: str = "Conduct detailed analysis using GPT Researcher"
    sdk: Any = None

    def __init__(self, sdk):
        super().__init__(sdk=sdk)
        self.sdk = sdk

    def _run(self, query: str) -> str:
        try:
            return self.sdk.use_service('gpt_researcher', {'query': query})
        except Exception as e:
            print(f"Error in GPT Research: {e}")
            return str(e)

def main():
    """
    Main execution function.
    """
    try:
        # Create and run the research crew
        ev_research = EVMarketResearchCrew()
        results = ev_research.run_research()
        
        # Print results in a structured format
        print("\n=== EV Market Research Results ===")
        print(f"\nTimestamp: {results['timestamp']}")
        
        print("\n=== Market Research Findings ===")
        print(results["market_research"])
        
        print("\n=== Technology Analysis ===")
        print(results["tech_analysis"])
        
        print("\n=== Strategic Insights ===")
        print(results["strategy"])
        
    except Exception as e:
        print(f"\nError in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()