import cv2
import os
import uuid
from typing import List, Tuple
import json
from datetime import datetime

class VideoProcessor:
    """Class to handle video processing and frame extraction"""
    
    def __init__(self, frames_folder: str):
        self.frames_folder = frames_folder
        
    def extract_frames(self, video_path: str, interval: float = 1.0, 
                      project_name: str = None) -> Tuple[str, List[str], dict]:
        """
        Extract frames from video at specified intervals
        
        Args:
            video_path: Path to the video file
            interval: Time interval between frames in seconds
            project_name: Name for the project/session
            
        Returns:
            Tuple containing (project_id, frame_paths, metadata)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"🎥 Starting video processing: {video_path}")
        print(f"📊 Interval: {interval} seconds")
        
        try:
            # Generate unique project ID
            project_id = project_name or f"project_{uuid.uuid4().hex[:8]}"
            project_folder = os.path.join(self.frames_folder, project_id)
            
            # Ensure project folder exists
            os.makedirs(project_folder, exist_ok=True)
        
        # Open video (ensure release even on failure on Windows)
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                raise ValueError(f"Could not open video file: {video_path}")
        except Exception as e:
            print(f"❌ Error opening video: {e}")
            raise
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📹 Video info: {total_frames} frames, {fps:.2f} FPS, {duration:.2f}s duration")
        print(f"📐 Resolution: {frame_width}x{frame_height}")
        
        # Calculate frame interval with overflow protection
        try:
            frame_interval = int(fps * interval)
            if frame_interval <= 0:
                frame_interval = 1
        except (OverflowError, ValueError):
            frame_interval = 1
            
        print(f"🔄 Extracting every {frame_interval} frames")
        
        extracted_frames = []
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Progress feedback every 100 frames
            if frame_count % 100 == 0:
                print(f"📊 Processed {frame_count}/{total_frames} frames, extracted {extracted_count} frames")
                
            # Extract frame at specified interval
            if frame_count % frame_interval == 0:
                frame_filename = f"frame_{extracted_count:06d}.jpg"
                frame_path = os.path.join(project_folder, frame_filename)
                
                # Save frame
                cv2.imwrite(frame_path, frame)
                extracted_frames.append(frame_path)
                extracted_count += 1
                
            frame_count += 1
        
        cap.release()
        
        print(f"✅ Video processing complete! Extracted {extracted_count} frames from {total_frames} total frames")
        
        # Create metadata (allow zero extracted frames; handle gracefully)
        metadata = {
            'project_id': project_id,
            'video_path': video_path,
            'video_name': os.path.basename(video_path),
            'fps': fps,
            'total_frames': total_frames,
            'duration': duration,
            'frame_interval': interval,  # Store the original interval
            'extracted_frames': extracted_count,
            'frame_paths': extracted_frames,
            'frame_size': [frame_width, frame_height],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
            # Save metadata
            metadata_path = os.path.join(project_folder, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return project_id, extracted_frames, metadata
            
        except Exception as e:
            print(f"❌ Video processing failed: {e}")
            # Clean up on error
            try:
                if 'cap' in locals():
                    cap.release()
            except:
                pass
            raise
    
    def get_project_metadata(self, project_id: str) -> dict:
        """Load project metadata"""
        metadata_path = os.path.join(self.frames_folder, project_id, 'metadata.json')
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Project metadata not found: {project_id}")
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Handle backward compatibility with old metadata format
        if 'extracted_count' in metadata and 'extracted_frames' not in metadata:
            metadata['extracted_frames'] = metadata['extracted_count']
        
        if 'interval' in metadata and 'frame_interval' not in metadata:
            metadata['frame_interval'] = metadata['interval']
        
        # Check actual available frames and update count
        project_folder = os.path.join(self.frames_folder, project_id)
        if os.path.exists(project_folder):
            frame_files = [f for f in os.listdir(project_folder) 
                         if f.startswith('frame_') and f.endswith('.jpg')]
            actual_frame_count = len(frame_files)
            if actual_frame_count > 0:
                metadata['extracted_frames'] = actual_frame_count
        
        # Ensure required fields exist
        if 'frame_size' not in metadata:
            # Try to get frame size from first frame if available
            if metadata.get('frame_paths') and len(metadata['frame_paths']) > 0:
                first_frame_path = metadata['frame_paths'][0]
                if os.path.exists(first_frame_path):
                    try:
                        import cv2
                        frame = cv2.imread(first_frame_path)
                        if frame is not None:
                            height, width = frame.shape[:2]
                            metadata['frame_size'] = [width, height]
                    except:
                        metadata['frame_size'] = [640, 480]  # Default fallback
            else:
                metadata['frame_size'] = [640, 480]  # Default fallback
        
        return metadata
    
    def get_frame_path(self, project_id: str, frame_index: int) -> str:
        """Get path to specific frame"""
        metadata = self.get_project_metadata(project_id)
        
        # First try the expected path from metadata
        if frame_index < len(metadata['frame_paths']):
            expected_path = metadata['frame_paths'][frame_index]
            if os.path.exists(expected_path):
                return expected_path
        
        # If the expected frame doesn't exist, try to find available frames
        project_folder = os.path.join(self.frames_folder, project_id)
        if os.path.exists(project_folder):
            # Get all frame files in the project folder
            frame_files = [f for f in os.listdir(project_folder) 
                         if f.startswith('frame_') and f.endswith('.jpg')]
            frame_files.sort()  # Sort to get them in order
            
            if frame_files:
                # If we have frames, try to map the requested index to available frames
                if frame_index < len(frame_files):
                    return os.path.join(project_folder, frame_files[frame_index])
                else:
                    # If requested index is beyond available frames, return the last frame
                    return os.path.join(project_folder, frame_files[-1])
        
        # If no frames found, raise an error
        raise FileNotFoundError(f"Frame {frame_index} not found for project {project_id}")
    
    def list_projects(self) -> List[dict]:
        """List all available projects"""
        projects = []
        if not os.path.exists(self.frames_folder):
            return projects
            
        for project_dir in os.listdir(self.frames_folder):
            project_path = os.path.join(self.frames_folder, project_dir)
            if os.path.isdir(project_path):
                try:
                    metadata = self.get_project_metadata(project_dir)
                    projects.append({
                        'id': project_dir,
                        'name': metadata.get('video_name', project_dir),
                        'created_at': metadata.get('created_at'),
                        'frame_count': metadata.get('extracted_frames', metadata.get('extracted_count', 0))
                    })
                except Exception as e:
                    print(f"Error loading project {project_dir}: {e}")
                    # Skip invalid projects
                    continue
        
        return sorted(projects, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its frames"""
        import shutil
        
        project_path = os.path.join(self.frames_folder, project_id)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
            return True
        return False 