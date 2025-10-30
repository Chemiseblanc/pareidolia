"""Template file loading for pareidolia."""

from pareidolia.core.exceptions import (
    ActionNotFoundError,
    PersonaNotFoundError,
    VariantTemplateNotFoundError,
)
from pareidolia.core.models import Action, Example, Persona
from pareidolia.utils.filesystem import FileSystem


class TemplateLoader:
    """Loads and caches template files from the file system.

    Attributes:
        filesystem: FileSystem implementation (local or remote)
        root: Root path within the filesystem
    """

    def __init__(self, filesystem: FileSystem, root: str = "") -> None:
        """Initialize the template loader.

        Args:
            filesystem: FileSystem implementation (local or remote)
            root: Root path within the filesystem (e.g., "pareidolia" or "")
        """
        self.filesystem = filesystem
        self.root = root.rstrip("/")  # Normalize trailing slash
        self._persona_cache: dict[str, Persona] = {}
        self._action_cache: dict[str, Action] = {}
        self._example_cache: dict[str, Example] = {}

    def _build_path(self, *parts: str) -> str:
        """Build a path within the filesystem root.

        Args:
            *parts: Path components to join

        Returns:
            Complete path string
        """
        # Join parts with "/"
        path = "/".join(parts)
        # Prepend self.root if not empty
        if self.root:
            return f"{self.root}/{path}"
        return path

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

        persona_path = self._build_path("personas", f"{name}.md")

        if not self.filesystem.exists(persona_path):
            raise PersonaNotFoundError(f"Persona not found: {name}")

        content = self.filesystem.read_file(persona_path)
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

        # Try different template extensions
        extensions = [".md.j2", ".md.jinja", ".md.jinja2"]
        template = None

        for ext in extensions:
            action_path = self._build_path("actions", f"{name}{ext}")
            if self.filesystem.exists(action_path):
                template = self.filesystem.read_file(action_path)
                break

        if template is None:
            raise ActionNotFoundError(f"Action template not found: {name}")

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

        # Determine if this is a template or plain markdown
        is_template = False
        content = None
        name_without_ext = name

        # Try template extensions first
        template_extensions = [".md.j2", ".md.jinja", ".md.jinja2"]
        for ext in template_extensions:
            example_path = self._build_path("examples", f"{name}{ext}")
            if self.filesystem.exists(example_path):
                content = self.filesystem.read_file(example_path)
                is_template = True
                break

        # Try plain markdown
        if content is None:
            example_path = self._build_path("examples", f"{name}.md")
            if self.filesystem.exists(example_path):
                content = self.filesystem.read_file(example_path)
            else:
                # Try with .md extension removed if provided
                if name.endswith(".md"):
                    name_without_ext = name[:-3]
                    example_path = self._build_path(
                        "examples", f"{name_without_ext}.md"
                    )
                    if self.filesystem.exists(example_path):
                        content = self.filesystem.read_file(example_path)

        if content is None:
            raise FileNotFoundError(f"Example not found: {name}")

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
        actions_path = self._build_path("actions")
        if not self.filesystem.exists(actions_path):
            return []

        actions = set()

        # Find all template files
        for pattern in ["*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for file_path in self.filesystem.list_files(actions_path, pattern):
                # Extract filename from path
                filename = file_path.split("/")[-1]
                # Remove all template extensions to get the base name
                name = filename
                if name.endswith(".md.j2"):
                    name = name[:-6]
                elif name.endswith(".md.jinja2"):
                    name = name[:-10]
                elif name.endswith(".md.jinja"):
                    name = name[:-9]
                # Remove .md if still present
                if name.endswith(".md"):
                    name = name[:-3]
                actions.add(name)

        return sorted(actions)

    def list_personas(self) -> list[str]:
        """List all available persona names.

        Returns:
            List of persona names (without extensions)
        """
        personas_path = self._build_path("personas")
        if not self.filesystem.exists(personas_path):
            return []

        personas = []
        for file_path in self.filesystem.list_files(personas_path, "*.md"):
            # Extract filename from path and remove extension
            filename = file_path.split("/")[-1]
            if filename.endswith(".md"):
                personas.append(filename[:-3])

        return sorted(personas)

    def list_examples(self) -> list[str]:
        """List all available example names.

        Returns:
            List of example names (without extensions)
        """
        examples_path = self._build_path("examples")
        if not self.filesystem.exists(examples_path):
            return []

        examples = set()

        # Find all example files
        for pattern in ["*.md", "*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for file_path in self.filesystem.list_files(examples_path, pattern):
                # Extract filename from path
                filename = file_path.split("/")[-1]
                # Remove all extensions to get the base name
                name = filename
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
        # Try extensions in order
        extensions = [".md.jinja2", ".md.jinja", ".md.j2", ".md"]

        for ext in extensions:
            variant_path = self._build_path("variant", f"{variant_name}{ext}")
            if self.filesystem.exists(variant_path):
                return self.filesystem.read_file(variant_path)

        raise VariantTemplateNotFoundError(
            f"Variant template not found: {variant_name}"
        )

    def list_variants(self) -> list[str]:
        """List all available variant template names.

        Returns:
            List of variant names (without extensions)
        """
        variants_path = self._build_path("variant")
        if not self.filesystem.exists(variants_path):
            return []

        variants = set()

        # Find all variant template files
        for pattern in ["*.md", "*.md.j2", "*.md.jinja", "*.md.jinja2"]:
            for file_path in self.filesystem.list_files(variants_path, pattern):
                # Extract filename from path
                filename = file_path.split("/")[-1]
                # Remove all extensions to get base name
                name = filename
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
