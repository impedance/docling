"""Integration tests for the complete document processing pipeline."""

import json
import tempfile
from pathlib import Path

from core.model.config import PipelineConfig
from core.pipeline import DocumentPipeline


class TestDocumentPipelineIntegration:
    """End-to-end tests for the document processing pipeline."""

    def test_pipeline_processes_docx_file(self):
        """Test that the pipeline can process a real DOCX file end-to-end."""
        # Arrange
        input_file = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")
        assert input_file.exists(), "Test DOCX file should exist"
        
        config = PipelineConfig()
        pipeline = DocumentPipeline(config)
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(str(input_file), temp_dir)
            
            # Assert
            assert result.success, f"Pipeline should succeed: {result.error_message}"
            assert len(result.chapter_files) > 0, "Should generate at least one chapter file"
            assert len(result.asset_files) > 0, "Should extract at least one asset"
            
            # Verify files exist
            index_path = Path(result.index_file)
            assert index_path.exists(), "Index file should be created"
            
            manifest_path = Path(result.manifest_file)
            assert manifest_path.exists(), "Manifest file should be created"
            
            # Verify chapter files exist
            for chapter_file in result.chapter_files:
                assert Path(chapter_file).exists(), f"Chapter file should exist: {chapter_file}"
            
            # Verify asset files exist
            for asset_file in result.asset_files:
                assert Path(asset_file).exists(), f"Asset file should exist: {asset_file}"

    def test_pipeline_generates_valid_index_md(self):
        """Test that the generated index.md has valid content."""
        # Arrange
        input_file = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")
        config = PipelineConfig()
        pipeline = DocumentPipeline(config)
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(str(input_file), temp_dir)
            
            # Assert
            assert result.success
            index_path = Path(result.index_file)
            index_content = index_path.read_text(encoding='utf-8')
            
            # Check basic structure
            assert index_content.startswith('#'), "Index should start with a heading"
            assert 'chapters/' in index_content, "Index should link to chapter files"

    def test_pipeline_generates_valid_manifest_json(self):
        """Test that the generated manifest.json is valid JSON with expected structure."""
        # Arrange
        input_file = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")
        config = PipelineConfig()
        pipeline = DocumentPipeline(config)
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(str(input_file), temp_dir)
            
            # Assert
            assert result.success
            manifest_path = Path(result.manifest_file)
            manifest_content = manifest_path.read_text(encoding='utf-8')
            
            # Verify it's valid JSON
            manifest_data = json.loads(manifest_content)
            
            # Check required structure
            assert 'metadata' in manifest_data, "Manifest should contain metadata"
            assert 'chapters' in manifest_data, "Manifest should contain chapters"
            assert 'assets' in manifest_data, "Manifest should contain assets"
            
            # Check metadata structure
            metadata = manifest_data['metadata']
            assert 'title' in metadata, "Metadata should contain title"
            assert 'language' in metadata, "Metadata should contain language"

    def test_pipeline_with_custom_config(self):
        """Test that the pipeline respects custom configuration."""
        # Arrange
        input_file = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")
        config = PipelineConfig(
            split_level=1,
            assets_dir="custom_assets",
            chapter_pattern="{index:03d}-custom-{slug}.md",
            locale="fr"
        )
        pipeline = DocumentPipeline(config)
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(str(input_file), temp_dir)
            
            # Assert
            assert result.success
            
            # Check that custom assets directory is used
            temp_path = Path(temp_dir)
            doc_dir = temp_path / "cu-admin-install"
            custom_assets_dir = doc_dir / "custom_assets"
            assert custom_assets_dir.exists(), "Custom assets directory should be created"
            
            # Check manifest uses custom locale
            manifest_path = Path(result.manifest_file)
            manifest_data = json.loads(manifest_path.read_text())
            assert manifest_data['metadata']['language'] == 'fr', "Should use custom locale"

    def test_pipeline_handles_missing_file_gracefully(self):
        """Test that the pipeline handles missing input files gracefully."""
        # Arrange
        config = PipelineConfig()
        pipeline = DocumentPipeline(config)
        nonexistent_file = "/tmp/nonexistent_file.docx"
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(nonexistent_file, temp_dir)
            
            # Assert
            assert not result.success, "Pipeline should fail for missing file"
            assert result.error_message, "Should provide error message"
            assert len(result.chapter_files) == 0, "Should not generate chapter files"
            assert len(result.asset_files) == 0, "Should not generate asset files"

    def test_pipeline_creates_directory_structure(self):
        """Test that the pipeline creates the expected directory structure."""
        # Arrange
        input_file = Path("/home/spec/work/rosa/docling/docx-s/cu-admin-install.docx")
        config = PipelineConfig()
        pipeline = DocumentPipeline(config)
        
        # Act
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.process(str(input_file), temp_dir)
            
            # Assert
            assert result.success
            
            temp_path = Path(temp_dir)
            doc_dir = temp_path / "cu-admin-install"
            chapters_dir = doc_dir / "chapters"
            assets_dir = doc_dir / "assets"
            
            assert doc_dir.exists(), "Document directory should be created"
            assert chapters_dir.exists(), "Chapters directory should be created"
            assert assets_dir.exists(), "Assets directory should be created"
            
            assert (doc_dir / "index.md").exists(), "Index file should be created"
            assert (doc_dir / "manifest.json").exists(), "Manifest file should be created"