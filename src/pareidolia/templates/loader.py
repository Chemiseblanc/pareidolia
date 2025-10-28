"""Template file loading for pareidolia."""

from pathlib import Path

from pareidolia.core.exceptions import (
    ActionNotFoundError,
    PersonaNotFoundError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import Action, Example, Persona
from pareidolia.utils.filesystem import find_files, read_file


class TemplateLoader:
    """Loads and caches template files from the file system.

    Attributes:
        root: Root directory containing persona/action/example folders
    """

    def __init__(self, root: Path) -> None:
        """Initialize the template loader.

        Args:
            root: Root directory containing template folders
        """
        self.root = root
        self._persona_cache: dict[str, Persona] = {}
        self._action_cache: dict[str, Action] = {}
        self._example_cache: dict[str, Example] = {}

    def load_persona(self, name: str) -> Persona:
        """Load a persona by name.

        Args:
            name: The persona name (without file extension)

        Returns:
            The loaded persona

        Raises:
            PersonaNotFoundError: If the persona file is not found
        """
        if name in self._persona_cache:
            return self._persona_cache[name]

        persona_dir = self.root / "persona"
        persona_path = persona_dir / f"{name}.md"

        if not persona_path.exists():
            raise PersonaNotFoundError(f"Persona not found: {name}")

        content = read_file(persona_path)
        persona = Persona(name=name, content=content)
        self._persona_cache[name] = persona

        return persona

    def load_action(self, name: str, persona_name: str) -> Action:
        """Load an action template by name.

        Args:
            name: The action name (without file extension)
            persona_name: The name of the associated persona

        Returns:
            The loaded action

        Raises:
            ActionNotFoundError: If the action template is not found
        """
        cache_key = f"{persona_name}:{name}"
        if cache_key in self._action_cache:
            return self._action_cache[cache_key]

        action_dir = self.root / "action"

        # Try different template extensions
        extensions = [".md.j2", ".md.jinja", ".md.jinja2"]
        action_path = None

        for ext in extensions:
            candidate = action_dir / f"{name}{ext}"
            if candidate.exists():
                action_path = candidate
                break

        if action_path is None:
            raise ActionNotFoundError(f"Action template not found: {name}")

        template = read_file(action_path)
        action = Action(name=name, template=template, persona_name=persona_name)
        self._action_cache[cache_key] = action

        return action

    def load_example(self, name: str) -> Example:
        """Load an example by name.

        Args:
            name: The example name (with or without extension)

        Returns:
            The loaded example

        Raises:
            FileNotFoundError: If the example file is not found
        """
        if name in self._example_cache:
            return self._example_cache[name]

        example_dir = self.root / "example"

        # Determine if this is a template or plain markdown
        is_template = False
        example_path = None

        # Try template extensions first
        template_extensions = [".md.j2", ".md.jinja", ".md.jinja2"]
        for ext in template_extensions:
            candidate = example_dir / f"{name}{ext}"
            if candidate.exists():
                example_path = candidate
                is_template = True
                # Remove the template extension from the name
                name_without_ext = name
                break

        # Try plain markdown
        if example_path is None:
            candidate = example_dir / f"{name}.md"
            if candidate.exists():
                example_path = candidate
                name_without_ext = name
            else:
                # Try with .md extension removed if provided
                if name.endswith(".md"):
                    name_without_ext = name[:-3]
                    candidate = example_dir / f"{name_without_ext}.md"
                    if candidate.exists():
                        example_path = candidate

        if example_path is None:
            raise FileNotFoundError(f"Example not found: {name}")

        content = read_file(example_path)
        example = Example(
            name=name_without_ext, content=content, is_template=is_template
        )
        self._example_cache[name_without_ext] = example

        return example

    def list_actions(self) -> list[str]:
        """List all available action names.

        Returns:
            List of action names (without extensions)
        """
        action_dir = self.root / "action"
        if not action_dir.exists():
            return []

        actions = set()

        # Find all template files
        for pattern in ["*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for path in find_files(action_dir, pattern):
                # Remove all template extensions to get the base name
                name = path.stem
                if name.endswith(".md"):
                    name = name[:-3]
                actions.add(name)

        return sorted(actions)

    def list_personas(self) -> list[str]:
        """List all available persona names.

        Returns:
            List of persona names (without extensions)
        """
        persona_dir = self.root / "persona"
        if not persona_dir.exists():
            return []

        personas = []
        for path in find_files(persona_dir, "*.md"):
            personas.append(path.stem)

        return sorted(personas)

    def list_examples(self) -> list[str]:
        """List all available example names.

        Returns:
            List of example names (without extensions)
        """
        example_dir = self.root / "example"
        if not example_dir.exists():
            return []

        examples = set()

        # Find all example files
        for pattern in ["*.md", "*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for path in find_files(example_dir, pattern):
                # Remove all extensions to get the base name
                name = path.stem
                while name.endswith((".md", ".j2", ".jinja", ".jinja2")):
                    if name.endswith(".md"):
                        name = name[:-3]
                    elif name.endswith(".jinja2"):
                        name = name[:-7]
                    elif name.endswith(".jinja"):
                        name = name[:-6]
                    elif name.endswith(".j2"):
                        name = name[:-3]
                examples.add(name)

        return sorted(examples)

    def load_variant_template(self, variant_name: str) -> str:
        """Load a variant template by name.

        Args:
            variant_name: The variant name (without extension)

        Returns:
            The variant template content

        Raises:
            VariantTemplateNotFoundError: If template not found
        """
        variant_dir = self.root / "variant"

        # Try extensions in order
        extensions = [".md.jinja2", ".md.jinja", ".md.j2", ".md"]

        for ext in extensions:
            candidate = variant_dir / f"{variant_name}{ext}"
            if candidate.exists():
                return read_file(candidate)

        raise VariantTemplateNotFoundError(
            f"Variant template not found: {variant_name}"
        )

    def list_variants(self) -> list[str]:
        """List all available variant template names.

        Returns:
            List of variant names (without extensions)
        """
        variant_dir = self.root / "variant"
        if not variant_dir.exists():
            return []

        variants = set()

        # Find all variant template files
        for pattern in ["*.md", "*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for path in find_files(variant_dir, pattern):
                # Remove all extensions to get base name
                name = path.stem
                while name.endswith((".md", ".j2", ".jinja", ".jinja2")):
                    if name.endswith(".md"):
                        name = name[:-3]
                    elif name.endswith(".jinja2"):
                        name = name[:-7]
                    elif name.endswith(".jinja"):
                        name = name[:-6]
                    elif name.endswith(".j2"):
                        name = name[:-3]
                variants.add(name)

        return sorted(variants)
