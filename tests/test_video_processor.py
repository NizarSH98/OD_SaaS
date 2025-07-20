"""
Unit tests for VisionLabel Pro video processing system.

This module tests all video processing functionality including:
- Video file validation and processing
- Frame extraction with various intervals
- Metadata generation and accuracy
- Error handling for invalid videos
- File system operations and cleanup
- OpenCV integration and mocking
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call, mock_open
import cv2
import numpy as np

from modules.video_processor import VideoProcessor


@pytest.mark.unit
class TestVideoProcessorInitialization:
    """Test VideoProcessor initialization and configuration"""
    
    def test_video_processor_creation(self, app):
        """Test VideoProcessor initialization with frames folder"""
        frames_folder = app.config['FRAMES_FOLDER']
        processor = VideoProcessor(frames_folder)
        
        assert processor.frames_folder == frames_folder
    
    def test_video_processor_with_custom_folder(self):
        """Test VideoProcessor initialization with custom frames folder"""
        custom_folder = '/custom/frames/path'
        processor = VideoProcessor(custom_folder)
        
        assert processor.frames_folder == custom_folder


@pytest.mark.unit
class TestVideoFrameExtraction:
    """Test video frame extraction functionality"""
    
    def test_extract_frames_file_not_found(self, video_processor):
        """Test frame extraction with non-existent video file"""
        with pytest.raises(FileNotFoundError) as exc_info:
            video_processor.extract_frames('/nonexistent/video.mp4')
        
        assert 'Video file not found' in str(exc_info.value)
    
    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_extract_frames_invalid_video(self, mock_exists, mock_capture, video_processor):
        """Test frame extraction with corrupted/invalid video file"""
        mock_exists.return_value = True
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_capture.return_value = mock_cap
        
        with pytest.raises(ValueError) as exc_info:
            video_processor.extract_frames('/path/to/invalid.mp4')
        
        assert 'Could not open video file' in str(exc_info.value)
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_frames_successful(self, mock_file_open, mock_makedirs, mock_exists, mock_imwrite,
                                     mock_capture, video_processor):
        """Test successful frame extraction with default parameters"""
        # Setup mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 90  # 3 seconds at 30fps
        }.get(prop, 0)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Create finite sequence of frames that ends with False to prevent infinite loop
        read_responses = [(True, frame)] * 90 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=1.0
        )
        
        # Verify results
        assert project_id.startswith('project_')
        assert len(frame_paths) == 3
        assert metadata['fps'] == 30.0
        assert metadata['total_frames'] == 90
        assert metadata['duration'] == 3.0
        assert metadata['interval'] == 1.0
        assert metadata['extracted_count'] == 3
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_frames_with_custom_interval(self, mock_file_open, mock_makedirs, mock_exists,
                                               mock_imwrite, mock_capture, video_processor):
        """Test frame extraction with custom time interval"""
        # Setup mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 150  # 5 seconds at 30fps
        }.get(prop, 0)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Create finite sequence of frames that ends with False to prevent infinite loop
        read_responses = [(True, frame)] * 150 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        
        mock_capture.return_value = mock_cap
        
        # Execute with 2.5 second interval
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=2.5
        )
        
        # Verify interval calculation
        assert metadata['interval'] == 2.5
        assert metadata['duration'] == 5.0
        # With 2.5 second interval and 30fps, should extract frames every 75 frames
        # At 150 total frames, should extract frames at positions 0 and 75 (2 frames total)
        assert metadata['extracted_count'] == 2
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_frames_with_project_name(self, mock_file_open, mock_makedirs, mock_exists,
                                            mock_imwrite, mock_capture, video_processor):
        """Test frame extraction with custom project name"""
        # Setup mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 30
        }.get(prop, 0)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Create finite sequence of frames that ends with False to prevent infinite loop
        read_responses = [(True, frame)] * 30 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute with custom project name
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=1.0, project_name='custom_project'
        )
        
        # Verify custom project name is used
        assert project_id == 'custom_project'
        assert metadata['project_id'] == 'custom_project'
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_frames_high_fps_video(self, mock_file_open, mock_makedirs, mock_exists,
                                         mock_imwrite, mock_capture, video_processor):
        """Test frame extraction from high FPS video"""
        # Setup mocks for 60fps video
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 60.0,
            cv2.CAP_PROP_FRAME_COUNT: 600  # 10 seconds
        }.get(prop, 0)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        read_responses = [(True, frame)] * 600 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=1.0
        )
        
        # Verify metadata
        assert metadata['fps'] == 60.0
        assert metadata['duration'] == 10.0
        # Should extract frames at 60-frame intervals (1 second at 60fps)
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_frames_write_failure(self, mock_file_open, mock_makedirs, mock_exists,
                                        mock_imwrite, mock_capture, video_processor):
        """Test handling of frame write failures"""
        # Setup mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = False  # Simulate write failure
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 30
        }.get(prop, 0)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Create finite sequence of frames that ends with False to prevent infinite loop
        read_responses = [(True, frame)] * 30 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute - should handle write failure gracefully
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=1.0
        )
        
        # Should still return results even if some writes failed
        assert project_id is not None
        assert isinstance(frame_paths, list)
        assert isinstance(metadata, dict)


@pytest.mark.unit
class TestVideoProcessorMetadata:
    """Test metadata generation and accuracy"""
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_metadata_generation_complete(self, mock_file_open, mock_makedirs, mock_exists,
                                        mock_imwrite, mock_capture, video_processor):
        """Test complete metadata generation"""
        # Setup mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 24.0,
            cv2.CAP_PROP_FRAME_COUNT: 240,
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080
        }.get(prop, 0)
        
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        read_responses = [(True, frame)] * 5 + [(False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/test_video.mp4', interval=2.0, project_name='test_project'
        )
        
        # Verify complete metadata
        expected_metadata = {
            'project_id': 'test_project',
            'video_name': 'test_video.mp4',
            'video_path': '/path/to/test_video.mp4',
            'fps': 24.0,
            'total_frames': 240,
            'duration': 10.0,  # 240 frames / 24 fps
            'frame_interval': 2.0,
            'extracted_frames': 5,
            'frame_size': [1920, 1080]
        }
        
        for key, value in expected_metadata.items():
            assert metadata[key] == value
        
        # Verify timestamp fields exist
        assert 'created_at' in metadata
        assert 'updated_at' in metadata
    
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_metadata_edge_cases(self, mock_makedirs, mock_exists,
                                mock_imwrite, mock_capture, video_processor):
        """Test metadata generation with edge cases"""
        # Setup mocks for edge case video (very short, odd FPS)
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 23.976,  # Odd FPS
            cv2.CAP_PROP_FRAME_COUNT: 2,  # Very short video
            cv2.CAP_PROP_FRAME_WIDTH: 854,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)
        
        frame = np.zeros((480, 854, 3), dtype=np.uint8)
        read_responses = [(True, frame), (False, None)]
        mock_cap.read.side_effect = read_responses
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Execute with small interval
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/short.mp4', interval=0.1
        )
        
        # Verify edge case handling
        assert metadata['fps'] == 23.976
        assert metadata['total_frames'] == 2
        assert abs(metadata['duration'] - (2 / 23.976)) < 0.01
        assert metadata['frame_size'] == [854, 480]


@pytest.mark.unit
class TestVideoProcessorErrorHandling:
    """Test error handling and edge cases"""
    
    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    def test_opencv_exception_handling(self, mock_exists, mock_capture, video_processor):
        """Test handling of OpenCV exceptions"""
        mock_exists.return_value = True
        mock_capture.side_effect = cv2.error("OpenCV Error")
        
        with pytest.raises(cv2.error):
            video_processor.extract_frames('/path/to/video.mp4')
    
    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_frame_read_error(self, mock_makedirs, mock_exists, mock_capture, video_processor):
        """Test handling of frame reading errors"""
        mock_exists.return_value = True
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 30
        }.get(prop, 0)
        
        # All frame reads fail
        mock_cap.read.return_value = (False, None)
        mock_cap.set.return_value = True
        mock_capture.return_value = mock_cap
        
        # Should handle gracefully
        project_id, frame_paths, metadata = video_processor.extract_frames(
            '/path/to/video.mp4', interval=1.0
        )
        
        assert len(frame_paths) == 0
        assert metadata['extracted_frames'] == 0
    
    @patch('cv2.VideoCapture')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_directory_creation_failure(self, mock_makedirs, mock_exists, 
                                      mock_capture, video_processor):
        """Test handling of directory creation failures"""
        mock_exists.return_value = True
        mock_makedirs.side_effect = OSError("Permission denied")
        
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_capture.return_value = mock_cap
        
        with pytest.raises(OSError):
            video_processor.extract_frames('/path/to/video.mp4')
    
    def test_invalid_interval_values(self, video_processor):
        """Test handling of invalid interval values"""
        # These should not raise exceptions but handle gracefully
        test_intervals = [0, -1, float('inf'), float('nan')]
        
        for interval in test_intervals:
            with patch('os.path.exists', return_value=True):
                with patch('cv2.VideoCapture') as mock_capture:
                    mock_cap = MagicMock()
                    mock_cap.isOpened.return_value = True
                    mock_cap.get.side_effect = lambda prop: {
                        cv2.CAP_PROP_FPS: 30.0,
                        cv2.CAP_PROP_FRAME_COUNT: 30
                    }.get(prop, 0)
                    mock_cap.read.return_value = (False, None)
                    mock_capture.return_value = mock_cap
                    
                    try:
                        video_processor.extract_frames('/path/to/video.mp4', interval=interval)
                    except (ValueError, ZeroDivisionError):
                        # These are acceptable exceptions for invalid intervals
                        pass


@pytest.mark.integration
class TestVideoProcessorIntegration:
    """Integration tests using real video files"""
    
    def test_extract_frames_with_real_video(self, video_processor, mock_video_file):
        """Test frame extraction with a real video file"""
        # Use the mock video file fixture (creates actual video)
        project_id, frame_paths, metadata = video_processor.extract_frames(
            mock_video_file, interval=1.0, project_name='integration_test'
        )
        
        # Verify results
        assert project_id == 'integration_test'
        assert len(frame_paths) > 0
        assert metadata['video_name'] == os.path.basename(mock_video_file)
        assert metadata['fps'] == 30.0
        assert metadata['total_frames'] == 90
        assert metadata['duration'] == 3.0
        
        # Verify frame files were actually created
        for frame_path in frame_paths:
            assert os.path.exists(frame_path)
            # Verify file size is reasonable (not empty)
            assert os.path.getsize(frame_path) > 1000  # At least 1KB
    
    def test_multiple_extractions_same_processor(self, video_processor, mock_video_file):
        """Test multiple frame extractions with the same processor instance"""
        # First extraction
        project_id1, frame_paths1, metadata1 = video_processor.extract_frames(
            mock_video_file, interval=1.0, project_name='test1'
        )
        
        # Second extraction with different parameters
        project_id2, frame_paths2, metadata2 = video_processor.extract_frames(
            mock_video_file, interval=0.5, project_name='test2'
        )
        
        # Verify both extractions worked
        assert project_id1 == 'test1'
        assert project_id2 == 'test2'
        assert len(frame_paths2) > len(frame_paths1)  # More frames with smaller interval
        
        # Verify projects are isolated
        assert metadata1['project_id'] != metadata2['project_id']
    
    def test_frame_quality_and_content(self, video_processor, mock_video_file):
        """Test quality and content of extracted frames"""
        project_id, frame_paths, metadata = video_processor.extract_frames(
            mock_video_file, interval=1.0
        )
        
        # Load and verify first frame
        if frame_paths:
            frame = cv2.imread(frame_paths[0])
            
            assert frame is not None
            assert frame.shape == (480, 640, 3)  # Expected dimensions
            assert frame.dtype == np.uint8
            
            # Verify frame is not completely black or white
            mean_intensity = np.mean(frame)
            assert 0 < mean_intensity < 255
    
    @pytest.mark.slow
    def test_large_interval_extraction(self, video_processor, mock_video_file):
        """Test extraction with very large intervals"""
        project_id, frame_paths, metadata = video_processor.extract_frames(
            mock_video_file, interval=10.0  # Larger than video duration
        )
        
        # Should extract only one frame (at start)
        assert len(frame_paths) == 1
        assert metadata['extracted_frames'] == 1
    
    @pytest.mark.slow
    def test_small_interval_extraction(self, video_processor, mock_video_file):
        """Test extraction with very small intervals"""
        project_id, frame_paths, metadata = video_processor.extract_frames(
            mock_video_file, interval=0.1  # 10 FPS extraction
        )
        
        # Should extract many frames
        expected_frames = int(metadata['duration'] / 0.1)
        assert len(frame_paths) >= expected_frames - 1  # Allow for rounding
        assert metadata['extracted_frames'] >= expected_frames - 1 