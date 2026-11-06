"""
Presentation layer and Display Adapters for Phase 5: Display to the User.
Provides decoupled display implementations (Rich CLI & JSON) conforming to
the Display Adapter Pattern outlined in Architecture.md.
"""

from abc import ABC, abstractmethod
import sys
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from phase2.models import UserQuery
from phase4.models import RecommendationResponse, RecommendedRestaurant


class DisplayAdapter(ABC):
    """Abstract interface defining the presentation contract for recommendation outputs."""

    @abstractmethod
    def render_welcome(self) -> None:
        """Displays welcome banner or onboarding header."""
        pass

    @abstractmethod
    def render_query_summary(self, query: UserQuery) -> None:
        """Displays search constraints and recognized parameters."""
        pass

    @abstractmethod
    def render_recommendations(self, response: RecommendationResponse) -> None:
        """Renders final AI recommendation cards and rationale."""
        pass

    @abstractmethod
    def render_error(self, message: str) -> None:
        """Renders error or warning messages."""
        pass


class CLIDisplayAdapter(DisplayAdapter):
    """Rich terminal display adapter rendering visual cards, badges, and tables."""

    def __init__(self, console: Optional[Console] = None):
        # Configure safe UTF-8 output on Windows
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except Exception:
                pass
        self.console = console or Console()

    def render_welcome(self) -> None:
        title = Text("ZOMATO AI RESTAURANT RECOMMENDATION SERVICE", style="bold white on red")
        subtitle = "AI-Powered Dining Recommendations with Groq LLM Reasoning"
        panel = Panel(
            f"[bold yellow]{subtitle}[/bold yellow]\n[dim]Find the best dining spots tailored strictly to your City and Budget.[/dim]",
            title=title,
            border_style="red",
            expand=False,
            padding=(1, 2),
        )
        self.console.print(panel)

    def render_query_summary(self, query: UserQuery) -> None:
        table = Table(title="Search Parameters", show_header=True, header_style="bold cyan", border_style="dim")
        table.add_column("Parameter", style="bold")
        table.add_column("Applied Value", style="green")

        table.add_row("Target Location", query.city)
        budget_text = f"Rs. {int(query.max_budget)} (Base: Rs. {int(query.metadata.get('base_max_budget', query.max_budget))})"
        if query.min_budget > 0:
            budget_text = f"Rs. {int(query.min_budget)} - " + budget_text
        table.add_row("Budget Ceiling", budget_text)
        if query.preferences:
            table.add_row("Preferences", query.preferences)

        self.console.print(table)

    def render_recommendations(self, response: RecommendationResponse) -> None:
        if not response.recommendations:
            self.console.print(
                Panel("[bold red]No matching restaurants found within your budget and criteria.[/bold red]", border_style="red")
            )
            return

        # Overall summary panel
        mode_badge = "[dim](Mock Mode)[/dim]" if response.is_mock else f"[bold green]Groq {response.model_name}[/bold green]"
        summary_panel = Panel(
            f"[italic white]{response.overall_ai_summary}[/italic white]\n\n"
            f"[dim]Engine: {mode_badge} | Latency: {response.latency_seconds}s[/dim]",
            title="[bold yellow]AI Concierge Summary[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        self.console.print(summary_panel)

        self.console.print(f"\n[bold green]Top {len(response.recommendations)} Curated Dining Picks:[/bold green]\n")

        for idx, rec in enumerate(response.recommendations, 1):
            self._render_single_restaurant_card(idx, rec)

    def _render_single_restaurant_card(self, rank: int, rec: RecommendedRestaurant) -> None:
        # Header with rating and budget badge
        rating_color = "green" if rec.rating >= 4.0 else "yellow"
        rating_str = f"[{rating_color}]★ {rec.rating:.1f} / 5.0[/{rating_color}]"

        card_content = []
        card_content.append(f"[bold cyan]Locality:[/bold cyan] {rec.location}")
        card_content.append(f"[bold cyan]Cost for Two:[/bold cyan] [bold white]Rs. {rec.cost_for_two}[/bold white] [bold green]({rec.budget_verdict})[/bold green]")
        if rec.cuisines:
            card_content.append(f"[bold cyan]Cuisines:[/bold cyan] {rec.cuisines}")

        # AI Rationale block
        card_content.append(f"\n[bold yellow]AI Rationale:[/bold yellow]\n[italic]{rec.ai_rationale}[/italic]")

        # Must try dishes
        if rec.must_try_dishes:
            dishes_str = ", ".join(f"[bold underline]{d}[/bold underline]" for d in rec.must_try_dishes)
            card_content.append(f"\n[bold magenta]Must-Try Dishes:[/bold magenta] {dishes_str}")

        # Services badge
        services = []
        if rec.online_order == "Yes":
            services.append("[green]✓ Online Delivery[/green]")
        if rec.book_table == "Yes":
            services.append("[blue]✓ Table Booking[/blue]")
        if services:
            card_content.append(f"[dim]Services: {' | '.join(services)}[/dim]")

        panel = Panel(
            "\n".join(card_content),
            title=f"[bold white on blue] #{rank} [/bold white on blue] [bold]{rec.restaurant_name}[/bold] — {rating_str}",
            border_style="blue",
            padding=(1, 2),
        )
        self.console.print(panel)

    def render_error(self, message: str) -> None:
        self.console.print(f"[bold red][!] Error:[/bold red] {message}")


class JSONDisplayAdapter(DisplayAdapter):
    """Machine-readable display adapter for testing, APIs, and WebUI serialization."""

    def __init__(self):
        self.last_response: Optional[Dict[str, Any]] = None
        self.last_query: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

    def render_welcome(self) -> None:
        pass

    def render_query_summary(self, query: UserQuery) -> None:
        self.last_query = query.model_dump()

    def render_recommendations(self, response: RecommendationResponse) -> None:
        self.last_response = response.model_dump()

    def render_error(self, message: str) -> None:
        self.last_error = message

