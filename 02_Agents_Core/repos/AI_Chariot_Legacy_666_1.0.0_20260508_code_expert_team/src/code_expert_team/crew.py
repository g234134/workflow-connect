from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
import os

@CrewBase
class CodeExpertTeam():
    # 使用 Qwen 2.5 3B，這對你的 RTX 2060 負擔最輕
    local_llm = LLM(model="ollama/qwen2.5-coder:3b", base_url="http://localhost:11434")

    @agent
    def code_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_reviewer'],
            llm=self.local_llm,
            verbose=True
        )

    @agent
    def refactoring_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['refactoring_expert'],
            llm=self.local_llm,
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
            agent=self.code_reviewer()
        )

    @task
    def optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimization_task'],
            agent=self.refactoring_expert(),
            output_file='code_optimization_report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
