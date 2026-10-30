"""Azure AI Foundry "Grounding with Bing" provider (intentional stub).

The classic Bing Search API was retired on 11 Aug 2025. Microsoft's
supported replacement for Bing-grounded agents is the "Grounding with
Bing" tool attached to an Azure AI Foundry Agent Service agent.

Wiring it up requires (per Microsoft docs):
  1. An Azure AI Foundry project with a supported chat model deployed.
  2. A "Grounding with Bing" resource in the same subscription.
  3. The Bing resource connected to the Foundry project as a connection.
  4. An agent configured with the bing_grounding tool. The agent model
     processes the search results - there is no direct Bing result access.

This stub keeps the provider contract honest: the pipeline can reference
it, and it fails with a clear message instead of pretending to work.
"""

import os

from .base import SearchProvider, SearchResult


class FoundryGroundingProvider(SearchProvider):
    """Bing-grounded web search via Azure AI Foundry Agent Service."""

    name = "foundry_bing_grounding"

    def __init__(self, project_endpoint: str = "", model: str = "gpt-4o"):
        self.project_endpoint = project_endpoint or os.environ.get(
            "AZURE_AI_FOUNDRY_ENDPOINT", ""
        )
        self.model = model
        if not self.project_endpoint:
            raise RuntimeError(
                "FoundryGroundingProvider needs AZURE_AI_FOUNDRY_ENDPOINT (see .env.example). "
                "Create an Azure AI Foundry project, connect a 'Grounding with Bing' resource, "
                "and deploy an agent - until then run the pipeline in demo mode "
                "(LocalCorpusProvider), which needs no credentials."
            )

    def search(self, query: str, top_k: int = 5) -> list:
        # TODO(banga19): implement with the azure-ai-projects SDK:
        #   1. agent = project.agents.create_agent(model=self.model,
        #          tools=[ToolUtility.create_bing_grounding_tool(conn_id)])
        #   2. create thread + run with the user query
        #   3. walk run_steps, collect cited URLs + snippets from citations
        #   4. map each citation into SearchResult(title, url, snippet, rank, self.name)
        raise NotImplementedError(
            "Wire this to the azure-ai-projects SDK once the Foundry project exists. "
            "See docs/architecture.md, section 'Roadmap', for the checklist."
        )
