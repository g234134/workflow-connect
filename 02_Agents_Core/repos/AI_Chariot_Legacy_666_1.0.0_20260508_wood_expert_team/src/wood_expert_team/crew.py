from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import TavilySearchTool
from wood_expert_team.tools import ScraperAPITool
import os

@CrewBase
class WoodExpertTeam():
    # ä½¿ç”¨ Qwen 2.5 3B ä½œç‚º?¬åœ°å¤§è…¦
    local_llm = LLM(model="ollama/qwen2.5-coder:3b", base_url="http://localhost:11434")

    @agent
    def researcher(self) -> Agent:
        search_tool = TavilySearchTool(include_domains=["mobile01.com", "100.com.tw", "puloapp.com", "searchome.net"])
        scraper_tool = ScraperAPITool()
        return Agent(
            config=self.agents_config['researcher'],
            llm=self.local_llm,
            tools=[search_tool, scraper_tool],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=self.local_llm,
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        # ?Žç¢º?‡å???researcher è² è²¬
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher()
        )

    @task
    def reporting_task(self) -> Task:
        # ?Žç¢º?‡å???reporting_analyst è² è²¬
        return Task(
            config=self.tasks_config['reporting_task'],
            agent=self.reporting_analyst(),
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
