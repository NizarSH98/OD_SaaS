"""
Unit tests for VisionLabel Pro data storage and annotation system.

This module tests all data storage functionality including:
- Annotation saving and loading operations
- Project data management and persistence
- Export format generation (YOLO, COCO, Pascal VOC)
- JSON file operations and error handling
- Dataset statistics and analytics
- File system operations and cleanup
"""

import pytest
import os
import json
import tempfile
import shutil
import zipfile
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime

from modules.data_storage import LabelStorage


@pytest.mark.unit
class TestLabelStorageInitialization:
    """Test LabelStorage initialization and configuration"""
    
    def test_label_storage_creation(self, app):
        """Test LabelStorage initialization with datasets folder"""
        datasets_folder = app.config['DATASETS_FOLDER']
        storage = LabelStorage(datasets_folder)
        
        assert storage.datasets_folder == datasets_folder
    
    def test_label_storage_with_custom_folder(self):
        """Test LabelStorage initialization with custom datasets folder"""
        custom_folder = '/custom/datasets/path'
        storage = LabelStorage(custom_folder)
        
        assert storage.datasets_folder == custom_folder


@pytest.mark.unit
class TestAnnotationOperations:
    """Test annotation CRUD operations"""
    
    def test_save_annotation_new_project(self, label_storage, sample_annotations):
        """Test saving annotations for a new project"""
        project_id = 'test-project-123'
        frame_index = 0
        frame_path = '/path/to/frame_000.jpg'
        
        result = label_storage.save_annotation(
            project_id, frame_index, frame_path, sample_annotations
        )
        
        assert result is True
        
        # Verify file structure was created
        project_dir = os.path.join(label_storage.datasets_folder, project_id)
        annotations_file = os.path.join(project_dir, 'annotations.json')
        
        assert os.path.exists(project_dir)
        assert os.path.exists(annotations_file)
        
        # Verify annotation content
        with open(annotations_file, 'r') as f:
            data = json.load(f)
        
        assert data['project_id'] == project_id
        assert 'created_at' in data
        assert 'updated_at' in data
        assert '0' in data['frames']
        assert data['frames']['0']['frame_index'] == frame_index
        assert data['frames']['0']['frame_path'] == frame_path
        assert data['frames']['0']['annotations'] == sample_annotations
    
    def test_save_annotation_existing_project(self, label_storage, sample_annotations):
        """Test saving annotations to existing project"""
        project_id = 'existing-project'
        
        # Create initial annotation
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations[:1])
        
        # Add second frame annotation
        new_annotations = sample_annotations[1:]
        result = label_storage.save_annotation(
            project_id, 1, '/frame_1.jpg', new_annotations
        )
        
        assert result is True
        
        # Verify both frames exist
        annotations_file = os.path.join(label_storage.datasets_folder, project_id, 'annotations.json')
        with open(annotations_file, 'r') as f:
            data = json.load(f)
        
        assert '0' in data['frames']
        assert '1' in data['frames']
        assert len(data['frames']['0']['annotations']) == 1
        assert len(data['frames']['1']['annotations']) == 1
    
    def test_save_annotation_update_existing_frame(self, label_storage, sample_annotations):
        """Test updating annotations for existing frame"""
        project_id = 'update-project'
        frame_index = 0
        
        # Create initial annotation
        label_storage.save_annotation(project_id, frame_index, '/frame.jpg', sample_annotations[:1])
        
        # Update with new annotations
        updated_annotations = sample_annotations
        result = label_storage.save_annotation(
            project_id, frame_index, '/frame.jpg', updated_annotations
        )
        
        assert result is True
        
        # Verify updated content
        annotations_file = os.path.join(label_storage.datasets_folder, project_id, 'annotations.json')
        with open(annotations_file, 'r') as f:
            data = json.load(f)
        
        assert len(data['frames']['0']['annotations']) == 2
        assert data['frames']['0']['annotations'] == updated_annotations
    
    def test_save_annotation_error_handling(self, label_storage, sample_annotations):
        """Test error handling during annotation saving"""
        project_id = 'error-project'
        
        # Make datasets folder read-only to simulate error
        original_mode = os.stat(label_storage.datasets_folder).st_mode
        os.chmod(label_storage.datasets_folder, 0o444)
        
        try:
            result = label_storage.save_annotation(
                project_id, 0, '/frame.jpg', sample_annotations
            )
            assert result is False
        finally:
            # Restore permissions
            os.chmod(label_storage.datasets_folder, original_mode)
    
    def test_load_annotations_existing_project(self, label_storage, sample_annotations):
        """Test loading annotations for existing project"""
        project_id = 'load-test-project'
        
        # Create test data
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations[:1])
        label_storage.save_annotation(project_id, 1, '/frame_1.jpg', sample_annotations[1:])
        
        # Load annotations
        annotations = label_storage.load_annotations(project_id)
        
        assert annotations is not None
        assert annotations['project_id'] == project_id
        assert len(annotations['frames']) == 2
        assert '0' in annotations['frames']
        assert '1' in annotations['frames']
    
    def test_load_annotations_nonexistent_project(self, label_storage):
        """Test loading annotations for non-existent project"""
        annotations = label_storage.load_annotations('nonexistent-project')
        
        assert annotations is None
    
    def test_load_annotations_corrupted_file(self, label_storage):
        """Test loading annotations from corrupted file"""
        project_id = 'corrupted-project'
        project_dir = os.path.join(label_storage.datasets_folder, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create corrupted annotations file
        annotations_file = os.path.join(project_dir, 'annotations.json')
        with open(annotations_file, 'w') as f:
            f.write('invalid json content')
        
        annotations = label_storage.load_annotations(project_id)
        
        assert annotations is None
    
    def test_get_frame_annotations_existing(self, label_storage, sample_annotations):
        """Test getting annotations for specific frame"""
        project_id = 'frame-test-project'
        frame_index = 5
        
        # Save test data
        label_storage.save_annotation(project_id, frame_index, '/frame_5.jpg', sample_annotations)
        
        # Get frame annotations
        frame_annotations = label_storage.get_frame_annotations(project_id, frame_index)
        
        assert frame_annotations == sample_annotations
    
    def test_get_frame_annotations_nonexistent(self, label_storage):
        """Test getting annotations for non-existent frame"""
        frame_annotations = label_storage.get_frame_annotations('nonexistent', 0)
        
        assert frame_annotations == []
    
    def test_delete_frame_annotations(self, label_storage, sample_annotations):
        """Test deleting annotations for specific frame"""
        project_id = 'delete-test-project'
        
        # Create test data with multiple frames
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations)
        label_storage.save_annotation(project_id, 1, '/frame_1.jpg', sample_annotations)
        
        # Delete frame 0 annotations
        result = label_storage.delete_frame_annotations(project_id, 0)
        
        assert result is True
        
        # Verify frame 0 is gone but frame 1 remains
        annotations = label_storage.load_annotations(project_id)
        assert '0' not in annotations['frames']
        assert '1' in annotations['frames']
    
    def test_get_project_statistics(self, label_storage, sample_annotations):
        """Test getting project statistics and analytics"""
        project_id = 'stats-project'
        
        # Create test data
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations)
        label_storage.save_annotation(project_id, 1, '/frame_1.jpg', sample_annotations[:1])
        label_storage.save_annotation(project_id, 2, '/frame_2.jpg', [])  # Empty frame
        
        stats = label_storage.get_project_statistics(project_id)
        
        assert stats['total_frames'] == 3
        assert stats['annotated_frames'] == 2  # Frame 2 has no annotations
        assert stats['total_annotations'] == 3  # 2 + 1 + 0
        assert stats['annotations_per_frame'] == 1.0  # 3 annotations / 3 frames
        
        # Class distribution
        expected_classes = {'person': 2, 'car': 1}
        assert stats['class_distribution'] == expected_classes


@pytest.mark.unit
class TestExportFormats:
    """Test dataset export format generation"""
    
    def test_export_yolo_format(self, label_storage, sample_annotations):
        """Test YOLO format export"""
        project_id = 'yolo-export-test'
        
        # Setup test data with normalized coordinates
        yolo_annotations = [
            {
                'id': 'ann-1',
                'class': 'person',
                'x': 0.1,      # Normalized coordinates
                'y': 0.2,
                'width': 0.3,
                'height': 0.4,
                'confidence': 0.95
            }
        ]
        
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', yolo_annotations)
        
        # Export to YOLO format
        export_path = label_storage.export_dataset(project_id, 'yolo')
        
        assert export_path is not None
        assert os.path.exists(export_path)
        assert export_path.endswith('.zip')
        
        # Verify ZIP contents
        with zipfile.ZipFile(export_path, 'r') as zip_file:
            files = zip_file.namelist()
            assert 'labels/frame_0.txt' in files
            assert 'classes.txt' in files
            
            # Verify YOLO label format
            label_content = zip_file.read('labels/frame_0.txt').decode('utf-8')
            assert 'person' in label_content or '0' in label_content  # Class index or name
    
    def test_export_coco_format(self, label_storage, sample_annotations):
        """Test COCO format export"""
        project_id = 'coco-export-test'
        
        # Setup test data
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations)
        
        # Export to COCO format
        export_path = label_storage.export_dataset(project_id, 'coco')
        
        assert export_path is not None
        assert os.path.exists(export_path)
        
        # Verify ZIP contents
        with zipfile.ZipFile(export_path, 'r') as zip_file:
            files = zip_file.namelist()
            assert 'annotations.json' in files
            
            # Verify COCO format structure
            coco_content = json.loads(zip_file.read('annotations.json').decode('utf-8'))
            assert 'images' in coco_content
            assert 'annotations' in coco_content
            assert 'categories' in coco_content
            assert 'info' in coco_content
    
    def test_export_pascal_voc_format(self, label_storage, sample_annotations):
        """Test Pascal VOC format export"""
        project_id = 'voc-export-test'
        
        # Setup test data
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations)
        
        # Export to Pascal VOC format
        export_path = label_storage.export_dataset(project_id, 'pascal_voc')
        
        assert export_path is not None
        assert os.path.exists(export_path)
        
        # Verify ZIP contents
        with zipfile.ZipFile(export_path, 'r') as zip_file:
            files = zip_file.namelist()
            assert any(f.endswith('.xml') for f in files)  # XML annotation files
    
    def test_export_invalid_format(self, label_storage, sample_annotations):
        """Test export with invalid format"""
        project_id = 'invalid-format-test'
        
        # Setup test data
        label_storage.save_annotation(project_id, 0, '/frame_0.jpg', sample_annotations)
        
        # Try to export with invalid format
        export_path = label_storage.export_dataset(project_id, 'invalid_format')
        
        assert export_path is None
    
    def test_export_empty_project(self, label_storage):
        """Test export of project with no annotations"""
        project_id = 'empty-project'
        
        # Create empty project
        project_dir = os.path.join(label_storage.datasets_folder, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Try to export
        export_path = label_storage.export_dataset(project_id, 'yolo')
        
        # Should handle gracefully
        assert export_path is None or os.path.exists(export_path)
    
    def test_export_nonexistent_project(self, label_storage):
        """Test export of non-existent project"""
        export_path = label_storage.export_dataset('nonexistent-project', 'yolo')
        
        assert export_path is None


@pytest.mark.unit
class TestDataValidation:
    """Test data validation and error handling"""
    
    def test_validate_annotation_structure(self, label_storage):
        """Test annotation structure validation"""
        valid_annotation = {
            'id': 'valid-1',
            'class': 'person',
            'x': 100,
            'y': 150,
            'width': 200,
            'height': 300
        }
        
        invalid_annotations = [
            {},  # Empty
            {'class': 'person'},  # Missing coordinates
            {'x': 100, 'y': 150},  # Missing class
            {'class': 'person', 'x': 'invalid', 'y': 150, 'width': 200, 'height': 300},  # Invalid type
        ]
        
        # Valid annotation should work
        result = label_storage.save_annotation('valid-test', 0, '/frame.jpg', [valid_annotation])
        assert result is True
        
        # Invalid annotations should be handled gracefully
        for invalid_ann in invalid_annotations:
            result = label_storage.save_annotation('invalid-test', 0, '/frame.jpg', [invalid_ann])
            # Should not crash, may return True or False depending on validation
            assert isinstance(result, bool)
    
    def test_coordinate_bounds_validation(self, label_storage):
        """Test coordinate bounds validation"""
        # Test with coordinates outside typical bounds
        out_of_bounds_annotation = {
            'id': 'bounds-test',
            'class': 'person',
            'x': -100,  # Negative coordinate
            'y': 5000,  # Very large coordinate
            'width': 200,
            'height': 300
        }
        
        result = label_storage.save_annotation('bounds-test', 0, '/frame.jpg', [out_of_bounds_annotation])
        
        # Should handle gracefully
        assert isinstance(result, bool)
    
    def test_class_name_validation(self, label_storage):
        """Test class name validation"""
        test_classes = [
            'valid_class',
            'valid-class',
            'ValidClass123',
            '',  # Empty class
            'class with spaces',
            'class/with/slashes',
            'class"with"quotes',
            'очень_длинное_имя_класса_с_юникодом_символами_и_специальными_знаками'
        ]
        
        for class_name in test_classes:
            annotation = {
                'id': f'class-test-{len(class_name)}',
                'class': class_name,
                'x': 100, 'y': 100, 'width': 100, 'height': 100
            }
            
            result = label_storage.save_annotation('class-test', 0, '/frame.jpg', [annotation])
            assert isinstance(result, bool)


@pytest.mark.unit
class TestProjectManagement:
    """Test project management functionality"""
    
    def test_list_projects(self, label_storage, sample_annotations):
        """Test listing all projects"""
        # Create multiple projects
        projects = ['project-1', 'project-2', 'project-3']
        for project_id in projects:
            label_storage.save_annotation(project_id, 0, '/frame.jpg', sample_annotations)
        
        project_list = label_storage.list_projects()
        
        assert len(project_list) >= len(projects)
        for project_id in projects:
            assert any(p['project_id'] == project_id for p in project_list)
    
    def test_delete_project(self, label_storage, sample_annotations):
        """Test project deletion"""
        project_id = 'delete-me'
        
        # Create project
        label_storage.save_annotation(project_id, 0, '/frame.jpg', sample_annotations)
        
        # Verify project exists
        assert label_storage.load_annotations(project_id) is not None
        
        # Delete project
        result = label_storage.delete_project(project_id)
        
        assert result is True
        assert label_storage.load_annotations(project_id) is None
    
    def test_delete_nonexistent_project(self, label_storage):
        """Test deletion of non-existent project"""
        result = label_storage.delete_project('nonexistent-project')
        
        # Should handle gracefully
        assert isinstance(result, bool)
    
    def test_project_metadata_management(self, label_storage, sample_project_metadata):
        """Test project metadata saving and loading"""
        project_id = 'metadata-test'
        
        # Save metadata
        result = label_storage.save_project_metadata(project_id, sample_project_metadata)
        assert result is True
        
        # Load metadata
        loaded_metadata = label_storage.load_project_metadata(project_id)
        assert loaded_metadata is not None
        
        # Verify content
        for key, value in sample_project_metadata.items():
            assert loaded_metadata[key] == value


@pytest.mark.integration
class TestDataStorageIntegration:
    """Integration tests for data storage system"""
    
    def test_full_annotation_workflow(self, label_storage, sample_annotations, sample_project_metadata):
        """Test complete annotation workflow from creation to export"""
        project_id = 'workflow-test'
        
        # 1. Save project metadata
        label_storage.save_project_metadata(project_id, sample_project_metadata)
        
        # 2. Add annotations for multiple frames
        for frame_idx in range(3):
            label_storage.save_annotation(
                project_id, frame_idx, f'/frame_{frame_idx}.jpg', sample_annotations
            )
        
        # 3. Load and verify annotations
        annotations = label_storage.load_annotations(project_id)
        assert len(annotations['frames']) == 3
        
        # 4. Get statistics
        stats = label_storage.get_project_statistics(project_id)
        assert stats['total_frames'] == 3
        assert stats['annotated_frames'] == 3
        
        # 5. Export in multiple formats
        for format_name in ['yolo', 'coco', 'pascal_voc']:
            export_path = label_storage.export_dataset(project_id, format_name)
            assert export_path is not None
            assert os.path.exists(export_path)
        
        # 6. Clean up
        result = label_storage.delete_project(project_id)
        assert result is True
    
    def test_concurrent_annotation_operations(self, label_storage, sample_annotations):
        """Test concurrent annotation operations"""
        project_id = 'concurrent-test'
        
        # Simulate concurrent frame annotations
        frame_operations = []
        for i in range(10):
            result = label_storage.save_annotation(
                project_id, i, f'/frame_{i}.jpg', sample_annotations
            )
            frame_operations.append(result)
        
        # All operations should succeed
        assert all(frame_operations)
        
        # Verify all frames were saved
        annotations = label_storage.load_annotations(project_id)
        assert len(annotations['frames']) == 10
    
    def test_large_annotation_dataset(self, label_storage, sample_annotations):
        """Test handling of large annotation datasets"""
        project_id = 'large-dataset-test'
        
        # Create large number of annotations
        large_annotations = sample_annotations * 50  # 100 annotations per frame
        
        # Save annotations for multiple frames
        for frame_idx in range(10):
            result = label_storage.save_annotation(
                project_id, frame_idx, f'/frame_{frame_idx}.jpg', large_annotations
            )
            assert result is True
        
        # Verify data integrity
        annotations = label_storage.load_annotations(project_id)
        assert len(annotations['frames']) == 10
        
        for frame_key in annotations['frames']:
            assert len(annotations['frames'][frame_key]['annotations']) == 100
        
        # Test statistics calculation
        stats = label_storage.get_project_statistics(project_id)
        assert stats['total_annotations'] == 1000  # 10 frames * 100 annotations
    
    @pytest.mark.slow
    def test_export_performance(self, label_storage, sample_annotations):
        """Test export performance with larger datasets"""
        project_id = 'performance-test'
        
        # Create substantial dataset
        for frame_idx in range(50):
            label_storage.save_annotation(
                project_id, frame_idx, f'/frame_{frame_idx:03d}.jpg', sample_annotations
            )
        
        # Test export performance
        import time
        
        start_time = time.time()
        export_path = label_storage.export_dataset(project_id, 'yolo')
        export_time = time.time() - start_time
        
        assert export_path is not None
        assert export_time < 10.0  # Should complete within 10 seconds
        
        # Verify export completeness
        with zipfile.ZipFile(export_path, 'r') as zip_file:
            files = zip_file.namelist()
            label_files = [f for f in files if f.startswith('labels/') and f.endswith('.txt')]
            assert len(label_files) == 50  # One label file per frame 