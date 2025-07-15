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
            
        # Generate unique project ID
        project_id = project_name or f"project_{uuid.uuid4().hex[:8]}"
        project_folder = os.path.join(self.frames_folder, project_id)
        os.makedirs(project_folder, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # Calculate frame interval
        frame_interval = int(fps * interval)
        
        extracted_frames = []
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
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
        
        # Create metadata
        metadata = {
            'project_id': project_id,
            'video_path': video_path,
            'video_name': os.path.basename(video_path),
            'fps': fps,
            'total_frames': total_frames,
            'duration': duration,
            'interval': interval,
            'extracted_count': extracted_count,
            'created_at': datetime.now().isoformat(),
            'frame_paths': extracted_frames
        }
        
        # Save metadata
        metadata_path = os.path.join(project_folder, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return project_id, extracted_frames, metadata
    
    def get_project_metadata(self, project_id: str) -> dict:
        """Load project metadata"""
        metadata_path = os.path.join(self.frames_folder, project_id, 'metadata.json')
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Project metadata not found: {project_id}")
            
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def get_frame_path(self, project_id: str, frame_index: int) -> str:
        """Get path to specific frame"""
        metadata = self.get_project_metadata(project_id)
        if frame_index < 0 or frame_index >= len(metadata['frame_paths']):
            raise IndexError(f"Frame index {frame_index} out of range")
        return metadata['frame_paths'][frame_index]
    
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
                        'frame_count': metadata.get('extracted_count', 0)
                    })
                except:
                    # Skip invalid projects
                    continue
        
        return sorted(projects, key=lambda x: x['created_at'], reverse=True)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its frames"""
        import shutil
        
        project_path = os.path.join(self.frames_folder, project_id)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
            return True
        return False 