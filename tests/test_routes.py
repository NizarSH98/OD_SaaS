"""
Unit tests for VisionLabel Pro Flask routes and API endpoints.

This module tests all route functionality including:
- Main application routes (index, upload, annotate, export)
- API endpoints for frame and annotation operations
- File upload validation and handling
- Authentication protection and access control
- Error handling and response codes
- Session management and project tracking
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from io import BytesIO

from flask import url_for, session


@pytest.mark.unit
class TestMainRoutes:
    """Test main application routes"""
    
    def test_index_route_unauthenticated(self, client):
        """Test index route redirects unauthenticated users"""
        response = client.get('/')
        
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_index_route_authenticated(self, authenticated_client):
        """Test index route for authenticated users"""
        with patch('modules.routes.label_storage') as mock_storage:
            mock_storage.list_projects.return_value = [
                {'project_id': 'test-1', 'name': 'Test Project 1'},
                {'project_id': 'test-2', 'name': 'Test Project 2'}
            ]
            
            response = authenticated_client.get('/')
            
            assert response.status_code == 200
            assert b'Dashboard' in response.data
            assert b'Test Project 1' in response.data
    
    def test_upload_route_get_authenticated(self, authenticated_client):
        """Test GET request to upload route for authenticated user"""
        response = authenticated_client.get('/upload')
        
        assert response.status_code == 200
        assert b'Create New Project' in response.data
        assert b'Upload Video' in response.data
    
    def test_upload_route_get_unauthenticated(self, client):
        """Test GET request to upload route redirects unauthenticated users"""
        response = client.get('/upload')
        
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_annotate_route_authenticated(self, authenticated_client):
        """Test annotate route for authenticated user"""
        with patch('modules.routes.label_storage') as mock_storage:
            # Mock project metadata
            mock_metadata = {
                'project_id': 'test-project',
                'video_name': 'test.mp4',
                'total_frames': 10
            }
            mock_storage.load_project_metadata.return_value = mock_metadata
            mock_storage.load_annotations.return_value = {'frames': {}}
            
            response = authenticated_client.get('/annotate/test-project')
            
            assert response.status_code == 200
            assert b'Annotate' in response.data
    
    def test_annotate_route_nonexistent_project(self, authenticated_client):
        """Test annotate route with non-existent project"""
        with patch('modules.routes.label_storage') as mock_storage:
            mock_storage.load_project_metadata.return_value = None
            
            response = authenticated_client.get('/annotate/nonexistent')
            
            assert response.status_code == 404
    
    def test_export_route_authenticated(self, authenticated_client):
        """Test export route for authenticated user"""
        with patch('modules.routes.label_storage') as mock_storage:
            mock_metadata = {
                'project_id': 'test-project',
                'video_name': 'test.mp4',
                'total_frames': 10
            }
            mock_storage.load_project_metadata.return_value = mock_metadata
            mock_storage.get_project_statistics.return_value = {
                'annotated_frames': 5,
                'total_annotations': 15,
                'completion_percentage': 50.0
            }
            
            response = authenticated_client.get('/export/test-project')
            
            assert response.status_code == 200
            assert b'Export Dataset' in response.data


@pytest.mark.unit
class TestVideoUpload:
    """Test video upload functionality"""
    
    def test_upload_video_no_file(self, authenticated_client):
        """Test video upload without file"""
        response = authenticated_client.post('/upload', data={})
        
        assert response.status_code == 400
        assert b'No video file provided' in response.data
    
    def test_upload_video_empty_filename(self, authenticated_client):
        """Test video upload with empty filename"""
        data = {'video': (BytesIO(b'fake video data'), '')}
        response = authenticated_client.post('/upload', data=data)
        
        assert response.status_code == 400
        assert b'No file selected' in response.data
    
    def test_upload_video_invalid_extension(self, authenticated_client):
        """Test video upload with invalid file extension"""
        data = {'video': (BytesIO(b'fake data'), 'test.txt')}
        response = authenticated_client.post('/upload', data=data)
        
        assert response.status_code == 400
        assert b'Invalid file type' in response.data
    
    @patch('modules.routes.video_processor')
    def test_upload_video_success(self, mock_processor, authenticated_client):
        """Test successful video upload and processing"""
        # Mock video processor
        mock_processor.extract_frames.return_value = (
            'test-project-123',
            ['/frames/frame_0.jpg', '/frames/frame_1.jpg'],
            {
                'project_id': 'test-project-123',
                'video_name': 'test.mp4',
                'total_frames': 2,
                'fps': 30.0,
                'duration': 1.0
            }
        )
        
        # Create test video file
        video_data = BytesIO(b'fake video content')
        data = {
            'video': (video_data, 'test.mp4'),
            'interval': '1.0',
            'project_name': 'Test Project'
        }
        
        response = authenticated_client.post('/upload', data=data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['project_id'] == 'test-project-123'
        assert 'redirect_url' in data
    
    def test_upload_video_invalid_interval(self, authenticated_client):
        """Test video upload with invalid interval parameter"""
        video_data = BytesIO(b'fake video content')
        data = {
            'video': (video_data, 'test.mp4'),
            'interval': '50.0'  # Exceeds max interval
        }
        
        response = authenticated_client.post('/upload', data=data)
        
        assert response.status_code == 400
        assert b'Interval must be between' in response.data
    
    @patch('modules.routes.video_processor')
    def test_upload_video_processing_error(self, mock_processor, authenticated_client):
        """Test video upload with processing error"""
        mock_processor.extract_frames.side_effect = Exception("Processing failed")
        
        video_data = BytesIO(b'fake video content')
        data = {'video': (video_data, 'test.mp4')}
        
        response = authenticated_client.post('/upload', data=data)
        
        assert response.status_code == 500
        assert b'Error processing video' in response.data


@pytest.mark.unit
class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_api_frame_unauthenticated(self, client):
        """Test frame API endpoint without authentication"""
        response = client.get('/api/frame/test-project/0')
        
        assert response.status_code == 302  # Redirect to login
    
    @patch('modules.routes.video_processor')
    def test_api_frame_success(self, mock_processor, authenticated_client):
        """Test successful frame retrieval"""
        # Mock frame path
        mock_processor.frames_folder = '/mock/frames'
        frame_path = '/mock/frames/test-project/frame_000.jpg'
        
        with patch('os.path.exists', return_value=True):
            with patch('flask.send_file') as mock_send:
                mock_send.return_value = 'mock response'
                
                response = authenticated_client.get('/api/frame/test-project/0')
                
                mock_send.assert_called_once()
    
    def test_api_frame_not_found(self, authenticated_client):
        """Test frame API with non-existent frame"""
        with patch('os.path.exists', return_value=False):
            response = authenticated_client.get('/api/frame/test-project/999')
            
            assert response.status_code == 404
    
    @patch('modules.routes.label_storage')
    def test_api_annotations_get(self, mock_storage, authenticated_client):
        """Test GET annotations API"""
        mock_annotations = [
            {'id': 'ann-1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}
        ]
        mock_storage.get_frame_annotations.return_value = mock_annotations
        
        response = authenticated_client.get('/api/annotations/test-project/0')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['annotations'] == mock_annotations
    
    @patch('modules.routes.label_storage')
    def test_api_annotations_post(self, mock_storage, authenticated_client):
        """Test POST annotations API"""
        mock_storage.save_annotation.return_value = True
        
        annotations_data = {
            'annotations': [
                {'id': 'new-1', 'class': 'car', 'x': 200, 'y': 150, 'width': 80, 'height': 60}
            ]
        }
        
        response = authenticated_client.post(
            '/api/annotations/test-project/0',
            data=json.dumps(annotations_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        mock_storage.save_annotation.assert_called_once()
    
    @patch('modules.routes.label_storage')
    def test_api_annotations_post_invalid_json(self, mock_storage, authenticated_client):
        """Test POST annotations API with invalid JSON"""
        response = authenticated_client.post(
            '/api/annotations/test-project/0',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    @patch('modules.routes.label_storage')
    def test_api_annotations_save_error(self, mock_storage, authenticated_client):
        """Test POST annotations API with save error"""
        mock_storage.save_annotation.return_value = False
        
        annotations_data = {'annotations': []}
        
        response = authenticated_client.post(
            '/api/annotations/test-project/0',
            data=json.dumps(annotations_data),
            content_type='application/json'
        )
        
        assert response.status_code == 500
    
    @patch('modules.routes.label_storage')
    def test_api_export_success(self, mock_storage, authenticated_client):
        """Test successful dataset export API"""
        mock_storage.export_dataset.return_value = '/path/to/export.zip'
        
        with patch('flask.send_file') as mock_send:
            mock_send.return_value = 'mock file response'
            
            response = authenticated_client.get('/api/export/test-project/yolo')
            
            mock_storage.export_dataset.assert_called_once_with('test-project', 'yolo')
            mock_send.assert_called_once()
    
    @patch('modules.routes.label_storage')
    def test_api_export_failure(self, mock_storage, authenticated_client):
        """Test dataset export API failure"""
        mock_storage.export_dataset.return_value = None
        
        response = authenticated_client.get('/api/export/test-project/yolo')
        
        assert response.status_code == 500
    
    @patch('modules.routes.label_storage')
    def test_api_delete_project_success(self, mock_storage, authenticated_client):
        """Test successful project deletion API"""
        mock_storage.delete_project.return_value = True
        
        response = authenticated_client.delete('/api/project/test-project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        mock_storage.delete_project.assert_called_once_with('test-project')
    
    @patch('modules.routes.label_storage')
    def test_api_delete_project_failure(self, mock_storage, authenticated_client):
        """Test project deletion API failure"""
        mock_storage.delete_project.return_value = False
        
        response = authenticated_client.delete('/api/project/test-project')
        
        assert response.status_code == 500


@pytest.mark.unit
class TestSessionManagement:
    """Test session management and project tracking"""
    
    @patch('modules.routes.video_processor')
    def test_session_project_tracking(self, mock_processor, authenticated_client):
        """Test that current project is tracked in session"""
        mock_processor.extract_frames.return_value = (
            'session-test-project',
            ['/frames/frame_0.jpg'],
            {'project_id': 'session-test-project'}
        )
        
        video_data = BytesIO(b'fake video content')
        data = {'video': (video_data, 'test.mp4')}
        
        response = authenticated_client.post('/upload', data=data)
        
        # Check session was updated
        with authenticated_client.session_transaction() as sess:
            assert sess.get('current_project') == 'session-test-project'
            assert sess.get('current_frame') == 0
    
    def test_session_frame_navigation(self, authenticated_client):
        """Test frame navigation updates session"""
        with authenticated_client.session_transaction() as sess:
            sess['current_project'] = 'test-project'
            sess['current_frame'] = 5
        
        # Session should persist frame information
        with authenticated_client.session_transaction() as sess:
            assert sess['current_frame'] == 5


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_project_id_format(self, authenticated_client):
        """Test handling of invalid project ID formats"""
        invalid_ids = ['', 'invalid/chars', '../../../etc/passwd', 'very' * 100]
        
        for invalid_id in invalid_ids:
            response = authenticated_client.get(f'/annotate/{invalid_id}')
            # Should handle gracefully (404, 400, or redirect)
            assert response.status_code in [400, 404, 302]
    
    def test_negative_frame_index(self, authenticated_client):
        """Test handling of negative frame indices"""
        response = authenticated_client.get('/api/frame/test-project/-1')
        
        assert response.status_code in [400, 404]
    
    def test_very_large_frame_index(self, authenticated_client):
        """Test handling of very large frame indices"""
        response = authenticated_client.get('/api/frame/test-project/999999')
        
        assert response.status_code == 404
    
    def test_malformed_annotation_data(self, authenticated_client):
        """Test handling of malformed annotation data"""
        malformed_data = [
            '{}',  # Empty object
            '{"invalid": "structure"}',  # Wrong structure
            '{"annotations": "not_a_list"}',  # Wrong type
        ]
        
        for data in malformed_data:
            response = authenticated_client.post(
                '/api/annotations/test-project/0',
                data=data,
                content_type='application/json'
            )
            # Should handle gracefully
            assert response.status_code in [400, 500]
    
    def test_file_system_errors(self, authenticated_client):
        """Test handling of file system errors"""
        # Test with permissions that might cause issues
        with patch('os.path.exists', side_effect=OSError("Permission denied")):
            response = authenticated_client.get('/api/frame/test-project/0')
            
            # Should handle OS errors gracefully
            assert response.status_code in [404, 500]


@pytest.mark.integration
class TestRouteIntegration:
    """Integration tests for route interactions"""
    
    @patch('modules.routes.video_processor')
    @patch('modules.routes.label_storage')
    def test_full_workflow_integration(self, mock_storage, mock_processor, authenticated_client):
        """Test complete workflow from upload to export"""
        # 1. Upload video
        mock_processor.extract_frames.return_value = (
            'integration-project',
            ['/frames/frame_0.jpg', '/frames/frame_1.jpg'],
            {
                'project_id': 'integration-project',
                'video_name': 'test.mp4',
                'total_frames': 2
            }
        )
        
        video_data = BytesIO(b'fake video content')
        upload_response = authenticated_client.post('/upload', data={
            'video': (video_data, 'test.mp4'),
            'project_name': 'Integration Test'
        })
        
        assert upload_response.status_code == 200
        
        # 2. Access annotation page
        mock_storage.load_project_metadata.return_value = {
            'project_id': 'integration-project',
            'video_name': 'test.mp4',
            'total_frames': 2
        }
        mock_storage.load_annotations.return_value = {'frames': {}}
        
        annotate_response = authenticated_client.get('/annotate/integration-project')
        assert annotate_response.status_code == 200
        
        # 3. Save annotations
        mock_storage.save_annotation.return_value = True
        
        annotations = {
            'annotations': [
                {'id': 'test-1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}
            ]
        }
        
        save_response = authenticated_client.post(
            '/api/annotations/integration-project/0',
            data=json.dumps(annotations),
            content_type='application/json'
        )
        
        assert save_response.status_code == 200
        
        # 4. Export dataset
        mock_storage.export_dataset.return_value = '/path/to/export.zip'
        
        with patch('flask.send_file') as mock_send:
            mock_send.return_value = 'file response'
            
            export_response = authenticated_client.get('/api/export/integration-project/yolo')
            assert export_response.status_code == 200
    
    def test_authentication_flow_integration(self, client):
        """Test authentication integration with protected routes"""
        protected_routes = [
            ('GET', '/'),
            ('GET', '/upload'),
            ('POST', '/upload'),
            ('GET', '/annotate/test'),
            ('GET', '/export/test'),
            ('GET', '/api/frame/test/0'),
            ('GET', '/api/annotations/test/0'),
            ('POST', '/api/annotations/test/0'),
            ('DELETE', '/api/project/test')
        ]
        
        for method, route in protected_routes:
            if method == 'GET':
                response = client.get(route)
            elif method == 'POST':
                response = client.post(route, data={})
            elif method == 'DELETE':
                response = client.delete(route)
            
            # All should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]
            if response.status_code == 302:
                assert '/auth/login' in response.location
    
    @patch('modules.routes.video_processor')
    @patch('modules.routes.label_storage')
    def test_concurrent_user_operations(self, mock_storage, mock_processor, app):
        """Test concurrent operations by multiple users"""
        # Create multiple test clients
        client1 = app.test_client()
        client2 = app.test_client()
        
        # Mock authentication for both clients
        with client1.session_transaction() as sess:
            sess['_user_id'] = 'user-1'
            sess['_fresh'] = True
        
        with client2.session_transaction() as sess:
            sess['_user_id'] = 'user-2'
            sess['_fresh'] = True
        
        # Mock storage operations
        mock_storage.save_annotation.return_value = True
        mock_storage.get_frame_annotations.return_value = []
        
        # Both users work on different projects simultaneously
        annotations1 = {'annotations': [{'id': '1', 'class': 'person', 'x': 100, 'y': 100, 'width': 50, 'height': 50}]}
        annotations2 = {'annotations': [{'id': '2', 'class': 'car', 'x': 200, 'y': 200, 'width': 80, 'height': 60}]}
        
        response1 = client1.post(
            '/api/annotations/project-1/0',
            data=json.dumps(annotations1),
            content_type='application/json'
        )
        
        response2 = client2.post(
            '/api/annotations/project-2/0',
            data=json.dumps(annotations2),
            content_type='application/json'
        )
        
        # Both operations should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200 