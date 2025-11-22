import os
from crewai import Agent, Task, Crew, Process
from langgraph.graph import StateGraph, END
from typing import TypedDict
from protomesh.core.mesh import ProtoMesh
from protomesh.core.governance import AllowListPolicy
from protomesh.adapters.crewai_adapter import ProtoMeshWriteTool
from protomesh.adapters.langgraph_adapter import ProtoMeshNode

# 1. Setup ProtoMesh
mesh = ProtoMesh()
# Allow writing to 'research_topic'
policy = AllowListPolicy(
    name="TopicPolicy", allowed_resources=["research_topic"], allowed_actions=["write"]
)
mesh.governance.register_policy(policy)

# 2. CrewAI Setup
# Agent that decides a topic and writes it to ProtoMesh
writer_tool = ProtoMeshWriteTool(mesh=mesh, agent_id="crewai_researcher")


# 3. LangGraph Setup
# Workflow that reads the topic and processes it
class GraphState(TypedDict):
    topic: str
    summary: str


def read_topic(state: GraphState, mesh: ProtoMesh):
    print("LangGraph: Reading topic from ProtoMesh...")
    entity = mesh.read("research_topic")
    if entity:
        return {"topic": entity.data.get("topic", "Unknown")}
    return {"topic": "No topic found"}


def summarize(state: GraphState, mesh: ProtoMesh):
    print(f"LangGraph: Summarizing topic '{state['topic']}'...")
    return {"summary": f"Summary of {state['topic']}"}


# Wrap nodes
node_read = ProtoMeshNode(mesh, "langgraph_reader")(read_topic)
node_summary = ProtoMeshNode(mesh, "langgraph_summarizer")(summarize)

workflow = StateGraph(GraphState)
workflow.add_node("read", node_read)
workflow.add_node("summarize", node_summary)
workflow.set_entry_point("read")
workflow.add_edge("read", "summarize")
workflow.add_edge("summarize", END)
app = workflow.compile()

# 4. Execution
if __name__ == "__main__":
    print("--- Starting CrewAI ---")
    if os.environ.get("GOOGLE_API_KEY"):
        try:
            researcher = Agent(
                role="Researcher",
                goal="Decide on a research topic and publish it.",
                backstory="Expert researcher.",
                tools=[writer_tool],
                verbose=True,
                allow_delegation=False,
                llm="gemini/gemini-2.5-flash",
            )

            task1 = Task(
                description='Decide on a topic about "AI Agents" and write it to ProtoMesh using the key "research_topic". '
                'The data should be {"topic": "your chosen topic"}.',
                agent=researcher,
                expected_output="Confirmation that topic was written.",
            )

            crew = Crew(
                agents=[researcher],
                tasks=[task1],
                verbose=True,
                process=Process.sequential,
            )

            crew.kickoff()

            # Verify if agent actually wrote to ProtoMesh
            if not mesh.read("research_topic"):
                print(
                    "WARNING: Agent finished but didn't write to ProtoMesh. Falling back to simulation..."
                )
                result = writer_tool._run(
                    '{"key": "research_topic", "data": {"topic": "Agentic Patterns (Simulated)"}}'
                )
                print(f"Tool Output: {result}")

        except Exception as e:
            print(f"WARNING: CrewAI execution failed ({str(e)}).")
    else:
        print("WARNING: GOOGLE_API_KEY not found.")

    print("\n--- Starting LangGraph ---")
    # Initialize with empty state, it will read from Mesh
    result = app.invoke({"topic": "", "summary": ""})
    print("\n--- Final Result ---")
    print(result)
