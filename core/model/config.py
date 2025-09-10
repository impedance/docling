"""Configuration models for the document processing pipeline."""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    """Configuration for the document processing pipeline."""
    
    # Splitting configuration
    split_level: int = Field(default=1, description="Heading level at which to split into chapters")
    
    # Output configuration  
    assets_dir: str = Field(default="assets", description="Directory name for assets within output")
    chapter_pattern: str = Field(default="{index:02d}-{slug}.md", description="Filename pattern for chapters")
    
    # Content configuration
    frontmatter_enabled: bool = Field(default=True, description="Whether to include frontmatter in output")
    locale: str = Field(default="en", description="Language/locale for processing")
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "PipelineConfig":
        """Load configuration from a YAML file."""
        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        
        return cls(**config_data)
    
    @classmethod
    def from_dict(cls, config_data: dict) -> "PipelineConfig":
        """Create configuration from a dictionary."""
        return cls(**config_data)
    
    def to_yaml(self, config_path: Path) -> None:
        """Save configuration to a YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.model_dump(), f, default_flow_style=False, sort_keys=True)


def load_config(config_path: Optional[Path] = None) -> PipelineConfig:
    """
    Load pipeline configuration from file or return defaults.
    
    Args:
        config_path: Path to configuration file. If None, looks for config.yaml in current directory.
        
    Returns:
        PipelineConfig instance
    """
    if config_path is None:
        config_path = Path("config.yaml")
    
    return PipelineConfig.from_yaml(config_path)