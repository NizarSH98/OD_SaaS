"""
Integration tests for VisionLabel Pro SaaS platform.

This module tests end-to-end workflows and component interactions including:
- Complete annotation workflows from upload to export
- Multi-user scenarios and concurrent operations
- Real file system operations and data persistence
- Cross-component integration and data flow
- Performance and scalability testing
- Error propagation and recovery scenarios
"""

import pytest
import os
import json
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock

from flask import session
from modules.video_processor import VideoProcessor
from modules.data_storage import LabelStorage
from modules.models import UserManager


@pytest.mark.integration
class TestEndToEndWorkflows:
    """Test complete end-to-end user workflows"""
    
    def test_complete_annotation_workflow(self, app, authenticated_client, mock_video_file):
        """Test complete workflow from video upload to dataset export"""
        with app.app_context():
            # Initialize real components with temp directories
            video_processor = VideoProcessor(app.config['FRAMES_FOLDER'])
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            
            # 1. Upload and process video
            with open(mock_video_file, 'rb') as video_file:
                upload_response = authenticated_client.post('/upload', data={
                    'video': (video_file, 'test_workflow.mp4'),
                    'interval': '1.0',
                    'project_name': 'Workflow Test'
                })
            
            assert upload_response.status_code == 200
            upload_data = json.loads(upload_response.data)
            project_id = upload_data['project_id']
            
            # 2. Verify frames were extracted
            project_folder = os.path.join(app.config['FRAMES_FOLDER'], project_id)
            assert os.path.exists(project_folder)
            frame_files = [f for f in os.listdir(project_folder) if f.endswith('.jpg')]
            assert len(frame_files) > 0
            
            # 3. Access annotation interface
            with patch('modules.routes.label_storage', label_storage):
                with patch('modules.routes.video_processor', video_processor):
                    annotate_response = authenticated_client.get(f'/annotate/{project_id}')
                    assert annotate_response.status_code == 200
            
            # 4. Add annotations for multiple frames
            test_annotations = [
                {
                    'id': 'workflow-ann-1',
                    'class': 'person',
                    'x': 100, 'y': 150,
                    'width': 200, 'height': 300,
                    'confidence': 0.95
                },
                {
                    'id': 'workflow-ann-2',
                    'class': 'car',
                    'x': 400, 'y': 200,
                    'width': 150, 'height': 100,
                    'confidence': 0.87
                }
            ]
            
            # Annotate multiple frames
            for frame_idx in range(min(3, len(frame_files))):
                frame_path = os.path.join(project_folder, frame_files[frame_idx])
                result = label_storage.save_annotation(
                    project_id, frame_idx, frame_path, test_annotations
                )
                assert result is True
            
            # 5. Verify annotations were saved
            annotations = label_storage.load_annotations(project_id)
            assert annotations is not None
            assert len(annotations['frames']) == 3
            
            # 6. Export in multiple formats
            export_formats = ['yolo', 'coco', 'pascal_voc']
            export_files = []
            
            for format_name in export_formats:
                export_path = label_storage.export_dataset(project_id, format_name)
                assert export_path is not None
                assert os.path.exists(export_path)
                export_files.append(export_path)
            
            # 7. Verify export file contents
            import zipfile
            
            # Check YOLO export
            yolo_export = next(f for f in export_files if 'yolo' in f)
            with zipfile.ZipFile(yolo_export, 'r') as zip_file:
                files = zip_file.namelist()
                assert any('labels/' in f for f in files)
                assert 'classes.txt' in files
            
            # 8. Clean up
            for export_file in export_files:
                if os.path.exists(export_file):
                    os.unlink(export_file)
    
    def test_multi_project_workflow(self, app, authenticated_client, mock_video_file):
        """Test managing multiple projects simultaneously"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            
            # Create multiple projects
            project_ids = []
            
            for i in range(3):
                # Create project
                project_data = {
                    'project_id': f'multi-project-{i}',
                    'video_name': f'video_{i}.mp4',
                    'created_at': time.time(),
                    'total_frames': 10
                }
                
                label_storage.save_project_metadata(f'multi-project-{i}', project_data)
                project_ids.append(f'multi-project-{i}')
                
                # Add some annotations
                annotations = [
                    {
                        'id': f'ann-{i}-1',
                        'class': f'class_{i}',
                        'x': 100 + i * 50,
                        'y': 100 + i * 50,
                        'width': 100, 'height': 100
                    }
                ]
                
                label_storage.save_annotation(
                    f'multi-project-{i}', 0, f'/frame_{i}_0.jpg', annotations
                )
            
            # Verify all projects exist and are independent
            projects = label_storage.list_projects()
            project_ids_found = [p['project_id'] for p in projects if p['project_id'].startswith('multi-project-')]
            
            assert len(project_ids_found) >= 3
            
            # Verify project isolation
            for project_id in project_ids:
                annotations = label_storage.load_annotations(project_id)
                assert annotations is not None
                assert annotations['project_id'] == project_id
                
                # Each project should have its unique annotations
                frame_annotations = annotations['frames']['0']['annotations']
                assert len(frame_annotations) == 1
                assert project_id.split('-')[-1] in frame_annotations[0]['class']
    
    def test_error_recovery_workflow(self, app, authenticated_client, mock_video_file):
        """Test error scenarios and recovery mechanisms"""
        with app.app_context():
            video_processor = VideoProcessor(app.config['FRAMES_FOLDER'])
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            
            # 1. Test corrupted video handling
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as corrupted_video:
                corrupted_video.write(b'not a valid video file')
                corrupted_video.flush()
                
                with open(corrupted_video.name, 'rb') as video_file:
                    upload_response = authenticated_client.post('/upload', data={
                        'video': (video_file, 'corrupted.mp4'),
                        'interval': '1.0'
                    })
                
                # Should handle gracefully
                assert upload_response.status_code in [400, 500]
                
                os.unlink(corrupted_video.name)
            
            # 2. Test annotation recovery after partial failure
            project_id = 'recovery-test'
            
            # Save some valid annotations
            valid_annotations = [{'id': 'valid-1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}]
            result = label_storage.save_annotation(project_id, 0, '/frame_0.jpg', valid_annotations)
            assert result is True
            
            # Verify recovery by loading annotations
            loaded_annotations = label_storage.load_annotations(project_id)
            assert loaded_annotations is not None
            assert len(loaded_annotations['frames']) == 1


@pytest.mark.integration
class TestComponentInteraction:
    """Test interaction between different system components"""
    
    def test_video_processor_storage_integration(self, app, mock_video_file):
        """Test integration between VideoProcessor and LabelStorage"""
        with app.app_context():
            video_processor = VideoProcessor(app.config['FRAMES_FOLDER'])
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            
            # Extract frames
            project_id, frame_paths, metadata = video_processor.extract_frames(
                mock_video_file, interval=1.0, project_name='integration_test'
            )
            
            # Save metadata using storage component
            result = label_storage.save_project_metadata(project_id, metadata)
            assert result is True
            
            # Add annotations for extracted frames
            for i, frame_path in enumerate(frame_paths[:3]):  # Limit to first 3 frames
                annotations = [
                    {
                        'id': f'integration-{i}',
                        'class': 'test_object',
                        'x': 100 + i * 10,
                        'y': 100 + i * 10,
                        'width': 50, 'height': 50
                    }
                ]
                
                result = label_storage.save_annotation(project_id, i, frame_path, annotations)
                assert result is True
            
            # Verify data consistency
            loaded_metadata = label_storage.load_project_metadata(project_id)
            assert loaded_metadata['project_id'] == project_id
            assert loaded_metadata['fps'] == metadata['fps']
            
            loaded_annotations = label_storage.load_annotations(project_id)
            assert len(loaded_annotations['frames']) == 3
    
    def test_authentication_route_integration(self, app, client):
        """Test integration between authentication and route protection"""
        with app.app_context():
            user_manager = UserManager(storage_file=tempfile.mktemp(suffix='.json'))
            
            # Create test user
            user = user_manager.create_user('integration@test.com', 'testpass123')
            assert user is not None
            
            # Test protected route access without login
            response = client.get('/')
            assert response.status_code == 302
            assert '/auth/login' in response.location
            
            # Login user
            login_response = client.post('/auth/login', data={
                'email': 'integration@test.com',
                'password': 'testpass123'
            }, follow_redirects=True)
            
            # Should now have access to protected routes
            dashboard_response = client.get('/')
            assert dashboard_response.status_code == 200
    
    def test_session_persistence_integration(self, app, authenticated_client):
        """Test session persistence across different operations"""
        with app.app_context():
            # Set project in session
            with authenticated_client.session_transaction() as sess:
                sess['current_project'] = 'session-test-project'
                sess['current_frame'] = 5
            
            # Verify session persists across requests
            with authenticated_client.session_transaction() as sess:
                assert sess['current_project'] == 'session-test-project'
                assert sess['current_frame'] == 5
            
            # Make a request and verify session is maintained
            response = authenticated_client.get('/upload')
            assert response.status_code == 200
            
            with authenticated_client.session_transaction() as sess:
                assert sess['current_project'] == 'session-test-project'


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency and persistence across operations"""
    
    def test_annotation_data_consistency(self, app):
        """Test annotation data remains consistent across operations"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            project_id = 'consistency-test'
            
            # Create initial annotations
            initial_annotations = [
                {'id': 'ann-1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50},
                {'id': 'ann-2', 'class': 'car', 'x': 200, 'y': 200, 'width': 80, 'height': 60}
            ]
            
            label_storage.save_annotation(project_id, 0, '/frame_0.jpg', initial_annotations)
            
            # Load and verify
            loaded_1 = label_storage.load_annotations(project_id)
            frame_0_annotations_1 = loaded_1['frames']['0']['annotations']
            
            # Update annotations
            updated_annotations = initial_annotations + [
                {'id': 'ann-3', 'class': 'bike', 'x': 300, 'y': 300, 'width': 40, 'height': 70}
            ]
            
            label_storage.save_annotation(project_id, 0, '/frame_0.jpg', updated_annotations)
            
            # Load again and verify consistency
            loaded_2 = label_storage.load_annotations(project_id)
            frame_0_annotations_2 = loaded_2['frames']['0']['annotations']
            
            assert len(frame_0_annotations_2) == 3
            assert len(frame_0_annotations_1) == 2
            
            # Verify original annotations are preserved
            for original_ann in initial_annotations:
                assert original_ann in frame_0_annotations_2
    
    def test_project_metadata_consistency(self, app):
        """Test project metadata consistency across operations"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            project_id = 'metadata-consistency-test'
            
            # Save initial metadata
            initial_metadata = {
                'project_id': project_id,
                'video_name': 'test.mp4',
                'created_at': '2024-01-01T12:00:00',
                'fps': 30.0,
                'total_frames': 100,
                'duration': 3.33
            }
            
            label_storage.save_project_metadata(project_id, initial_metadata)
            
            # Load and verify
            loaded_metadata = label_storage.load_project_metadata(project_id)
            
            for key, value in initial_metadata.items():
                assert loaded_metadata[key] == value
            
            # Add annotations and verify metadata is preserved
            annotations = [{'id': 'test', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}]
            label_storage.save_annotation(project_id, 0, '/frame_0.jpg', annotations)
            
            # Metadata should remain unchanged
            metadata_after_annotation = label_storage.load_project_metadata(project_id)
            
            for key, value in initial_metadata.items():
                assert metadata_after_annotation[key] == value


@pytest.mark.integration 
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance characteristics of integrated system"""
    
    def test_large_project_performance(self, app):
        """Test system performance with large projects"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            project_id = 'large-project-test'
            
            # Create large dataset
            num_frames = 100
            annotations_per_frame = 10
            
            start_time = time.time()
            
            # Add many annotations
            for frame_idx in range(num_frames):
                frame_annotations = []
                for ann_idx in range(annotations_per_frame):
                    annotation = {
                        'id': f'large-ann-{frame_idx}-{ann_idx}',
                        'class': f'class_{ann_idx % 5}',  # 5 different classes
                        'x': (frame_idx * 10) % 500,
                        'y': (ann_idx * 10) % 400,
                        'width': 50 + (ann_idx % 20),
                        'height': 50 + (frame_idx % 20)
                    }
                    frame_annotations.append(annotation)
                
                result = label_storage.save_annotation(
                    project_id, frame_idx, f'/frame_{frame_idx:03d}.jpg', frame_annotations
                )
                assert result is True
            
            creation_time = time.time() - start_time
            
            # Test loading performance
            start_time = time.time()
            annotations = label_storage.load_annotations(project_id)
            loading_time = time.time() - start_time
            
            # Test statistics calculation performance
            start_time = time.time()
            stats = label_storage.get_project_statistics(project_id)
            stats_time = time.time() - start_time
            
            # Verify correctness
            assert len(annotations['frames']) == num_frames
            assert stats['total_frames'] == num_frames
            assert stats['total_annotations'] == num_frames * annotations_per_frame
            
            # Performance assertions (reasonable thresholds)
            assert creation_time < 30.0  # Should create large dataset in under 30 seconds
            assert loading_time < 5.0    # Should load large dataset in under 5 seconds
            assert stats_time < 2.0      # Should calculate stats in under 2 seconds
    
    def test_concurrent_operations_performance(self, app):
        """Test performance under concurrent operations"""
        import threading
        import queue
        
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            results_queue = queue.Queue()
            
            def worker_function(worker_id):
                """Worker function for concurrent testing"""
                project_id = f'concurrent-project-{worker_id}'
                
                start_time = time.time()
                
                # Perform operations
                annotations = [
                    {
                        'id': f'worker-{worker_id}-ann',
                        'class': f'worker_class_{worker_id}',
                        'x': worker_id * 10,
                        'y': worker_id * 10,
                        'width': 50, 'height': 50
                    }
                ]
                
                # Save annotation
                result = label_storage.save_annotation(project_id, 0, f'/frame_{worker_id}.jpg', annotations)
                
                # Load annotation
                loaded = label_storage.load_annotations(project_id)
                
                end_time = time.time()
                
                results_queue.put({
                    'worker_id': worker_id,
                    'success': result and loaded is not None,
                    'duration': end_time - start_time
                })
            
            # Start multiple workers
            num_workers = 5
            threads = []
            
            start_time = time.time()
            
            for i in range(num_workers):
                thread = threading.Thread(target=worker_function, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all workers to complete
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            # Verify all workers succeeded
            assert len(results) == num_workers
            assert all(r['success'] for r in results)
            
            # Performance verification
            assert total_time < 10.0  # All operations should complete in under 10 seconds
            average_duration = sum(r['duration'] for r in results) / len(results)
            assert average_duration < 3.0  # Average operation should be under 3 seconds


@pytest.mark.integration
class TestSystemResilience:
    """Test system resilience and error recovery"""
    
    def test_partial_data_corruption_recovery(self, app):
        """Test recovery from partial data corruption scenarios"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            project_id = 'corruption-test'
            
            # Create valid project
            annotations = [
                {'id': 'valid-1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}
            ]
            label_storage.save_annotation(project_id, 0, '/frame_0.jpg', annotations)
            
            # Simulate partial corruption by modifying file
            project_dir = os.path.join(label_storage.datasets_folder, project_id)
            annotations_file = os.path.join(project_dir, 'annotations.json')
            
            # Read original data
            with open(annotations_file, 'r') as f:
                original_data = f.read()
            
            # Corrupt file slightly
            corrupted_data = original_data[:-10] + 'invalid}'
            with open(annotations_file, 'w') as f:
                f.write(corrupted_data)
            
            # Try to load - should handle gracefully
            loaded = label_storage.load_annotations(project_id)
            assert loaded is None  # Should fail gracefully
            
            # Restore original data
            with open(annotations_file, 'w') as f:
                f.write(original_data)
            
            # Should work again
            loaded = label_storage.load_annotations(project_id)
            assert loaded is not None
    
    def test_disk_space_handling(self, app):
        """Test handling of disk space limitations"""
        with app.app_context():
            label_storage = LabelStorage(app.config['DATASETS_FOLDER'])
            
            # This is a conceptual test - in practice would need specific setup
            # to simulate disk space issues
            
            # Try to create very large annotation sets
            project_id = 'disk-space-test'
            large_annotations = []
            
            # Create many large annotations
            for i in range(1000):
                annotation = {
                    'id': f'large-{i}',
                    'class': 'test_class',
                    'x': i, 'y': i, 'width': 100, 'height': 100,
                    'metadata': 'x' * 1000  # Large metadata field
                }
                large_annotations.append(annotation)
            
            # Should handle large datasets gracefully
            result = label_storage.save_annotation(project_id, 0, '/frame.jpg', large_annotations)
            
            # Result depends on available disk space, but should not crash
            assert isinstance(result, bool) 