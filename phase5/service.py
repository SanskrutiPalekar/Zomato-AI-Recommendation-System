"""
Master Service Layer for the Zomato AI Restaurant Recommendation Service.
Orchestrates and integrates all 5 development phases:
  Step 1: Input Zomato user data (MetadataStore)
  Step 2: User Input parsing & validation (InputHandler)
  Step 3: Integration & Candidate Filtering (IntegrationPipeline)
  Step 4: Groq AI Recommendation Engine (Phase4Pipeline)
  Step 5: Display to the User (DisplayAdapter)
"""

from typing import Optional

from phase1.metadata_store import MetadataStore
from phase2.city_matcher import CityMatcher
from phase2.cli_prompt import CLIPrompt
from phase2.config import DEFAULT_KNOWN_LOCALITIES
from phase2.input_handler import InputHandler
from phase2.models import UserQuery
from phase3.integrator import IntegrationPipeline
from phase4.groq_engine import GroqRecommendationEngine
from phase4.models import RecommendationResponse
from phase4.pipeline import Phase4Pipeline
from phase5.display_adapter import CLIDisplayAdapter, DisplayAdapter


class ZomatoAIService:
    """End-to-End Restaurant Recommendation Service integrating all 5 layers."""

    def __init__(
        self,
        metadata_store: MetadataStore,
        input_handler: Optional[InputHandler] = None,
        integration_pipeline: Optional[IntegrationPipeline] = None,
        recommendation_pipeline: Optional[Phase4Pipeline] = None,
        display_adapter: Optional[DisplayAdapter] = None,
    ):
        self.metadata_store = metadata_store
        if input_handler is None:
            store_cities = metadata_store.get_distinct_cities() if metadata_store else []
            store_locations = metadata_store.get_distinct_locations() if metadata_store else []
            merged_localities = list(
                dict.fromkeys(DEFAULT_KNOWN_LOCALITIES + store_cities + store_locations)
            )
            self.input_handler = InputHandler(
                city_matcher=CityMatcher(known_localities=merged_localities)
            )
        else:
            self.input_handler = input_handler
        self.integration_pipeline = integration_pipeline or IntegrationPipeline()
        self.recommendation_pipeline = recommendation_pipeline or Phase4Pipeline()
        self.display_adapter = display_adapter or CLIDisplayAdapter()

    def search(
        self,
        city: str,
        price: str,
        preferences: Optional[str] = None,
        force_mock: bool = False,
        render_output: bool = True,
        top_k: int = 6,
    ) -> RecommendationResponse:
        """
        Executes a complete recommendation request across all 5 layers:
        Step 2 (Input) -> Step 3 (Integrate) -> Step 4 (Recommend) -> Step 5 (Display).
        """
        # Step 2: Validate and standardize user inputs
        query: UserQuery = self.input_handler.process_inputs(
            city_input=city,
            budget_input=price,
            preferences_input=preferences,
        )

        if render_output:
            self.display_adapter.render_query_summary(query)

        # Step 3: Integrate with Step 1 knowledge base to retrieve and rank candidates
        context_payload = self.integration_pipeline.run(
            query=query,
            metadata_store=self.metadata_store,
            max_candidates=max(20, top_k * 2),
        )

        # Step 4: Generate reasoned recommendations using Groq AI model
        response: RecommendationResponse = self.recommendation_pipeline.run(
            payload=context_payload,
            force_mock=force_mock,
            target_count=top_k,
        )

        # Step 5: Render formatted output to user
        if render_output:
            self.display_adapter.render_recommendations(response)

        return response

    def run_interactive_session(self) -> None:
        """
        Runs the interactive CLI application session.
        Prompts user, executes search across all layers, renders rich cards,
        and allows continuous exploratory searches.
        """
        self.display_adapter.render_welcome()
        cli_prompt = CLIPrompt(handler=self.input_handler)

        while True:
            try:
                # Capture and validate user query
                query = cli_prompt.prompt_user()
                self.display_adapter.render_query_summary(query)

                # Integrate and retrieve candidates
                payload = self.integration_pipeline.run(
                    query=query,
                    metadata_store=self.metadata_store,
                    max_candidates=10,
                )

                # Generate recommendations with Groq
                response = self.recommendation_pipeline.run(payload)

                # Display to user
                self.display_adapter.render_recommendations(response)

            except Exception as err:
                self.display_adapter.render_error(str(err))

            # Prompt next action
            print("\n" + "-" * 60)
            choice = input("[?] Would you like to search again? (y/n): ").strip().lower()
            if choice not in ("y", "yes"):
                print("\nThank you for using Zomato AI Concierge! Bon appétit!\n")
                break

