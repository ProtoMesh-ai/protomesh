from crewai.tools import BaseTool
from pydantic import Field
from protomesh.core.mesh import ProtoMesh


class ProtoMeshReadTool(BaseTool):
    name: str = "ProtoMesh Read"
    description: str = "Read shared state from ProtoMesh. Input is the key string."
    mesh: ProtoMesh = Field(exclude=True)

    def _run(self, key: str) -> str:
        entity = self.mesh.read(key)
        if entity:
            return str(entity.data)
        return "Key not found"


class ProtoMeshWriteTool(BaseTool):
    name: str = "ProtoMesh Write"
    description: str = "Write to shared state in ProtoMesh. Input must be a JSON string with 'key' and 'data'."
    mesh: ProtoMesh = Field(exclude=True)
    agent_id: str

    def _run(self, json_input: str) -> str:
        import json

        try:
            payload = json.loads(json_input)
            key = payload.get("key")
            data = payload.get("data")
            version = payload.get("version")  # Optional for optimistic locking

            if not key or data is None:
                return "Error: 'key' and 'data' are required."

            entity = self.mesh.write(key, data, self.agent_id, expected_version=version)
            return f"Success. New version: {entity.version}"
        except Exception as e:
            return f"Error: {str(e)}"
