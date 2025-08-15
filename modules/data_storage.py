import json
import os
from typing import List, Dict, Any
from datetime import datetime
import uuid

class LabelStorage:
    """Class to handle storage and retrieval of bounding box labels"""
    
    def __init__(self, datasets_folder: str):
        self.datasets_folder = datasets_folder
        
    def save_annotation(self, project_id: str, frame_index: int, frame_path: str, 
                       annotations: List[Dict[str, Any]]) -> bool:
        """
        Save annotations for a specific frame
        
        Args:
            project_id: Project identifier
            frame_index: Index of the frame
            frame_path: Path to the frame image
            annotations: List of bounding box annotations
            
        Returns:
            Success status
        """
        try:
            # Create project annotation directory
            project_dir = os.path.join(self.datasets_folder, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Load existing annotations
            annotations_file = os.path.join(project_dir, 'annotations.json')
            if os.path.exists(annotations_file):
                with open(annotations_file, 'r') as f:
                    all_annotations = json.load(f)
            else:
                all_annotations = {
                    'project_id': project_id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'frames': {}
                }
            
            # Update annotations for this frame
            frame_key = str(frame_index)
            all_annotations['frames'][frame_key] = {
                'frame_index': frame_index,
                'frame_path': frame_path,
                'annotations': annotations,
                'updated_at': datetime.now().isoformat()
            }
            all_annotations['updated_at'] = datetime.now().isoformat()
            
            # Save updated annotations
            with open(annotations_file, 'w') as f:
                json.dump(all_annotations, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error saving annotation: {e}")
            return False
    
    def get_annotations(self, project_id: str, frame_index: int = None) -> Dict[str, Any]:
        """
        Get annotations for a project or specific frame
        
        Args:
            project_id: Project identifier
            frame_index: Optional specific frame index
            
        Returns:
            Annotations data
        """
        annotations_file = os.path.join(self.datasets_folder, project_id, 'annotations.json')
        
        if not os.path.exists(annotations_file):
            return {'frames': {}} if frame_index is None else {'annotations': []}
        
        with open(annotations_file, 'r') as f:
            all_annotations = json.load(f)
        
        if frame_index is not None:
            frame_key = str(frame_index)
            if frame_key in all_annotations.get('frames', {}):
                return all_annotations['frames'][frame_key]
            else:
                return {'annotations': []}
        
        return all_annotations
    
    def delete_annotation(self, project_id: str, frame_index: int, annotation_id: str) -> bool:
        """Delete a specific annotation"""
        try:
            annotations_file = os.path.join(self.datasets_folder, project_id, 'annotations.json')
            
            if not os.path.exists(annotations_file):
                return False
                
            with open(annotations_file, 'r') as f:
                all_annotations = json.load(f)
            
            frame_key = str(frame_index)
            if frame_key in all_annotations.get('frames', {}):
                frame_annotations = all_annotations['frames'][frame_key].get('annotations', [])
                # Remove annotation with matching ID
                frame_annotations = [ann for ann in frame_annotations if ann.get('id') != annotation_id]
                all_annotations['frames'][frame_key]['annotations'] = frame_annotations
                all_annotations['frames'][frame_key]['updated_at'] = datetime.now().isoformat()
                all_annotations['updated_at'] = datetime.now().isoformat()
                
                with open(annotations_file, 'w') as f:
                    json.dump(all_annotations, f, indent=2)
                    
                return True
                
        except Exception as e:
            print(f"Error deleting annotation: {e}")
            return False
    
    def load_annotations(self, project_id: str) -> Dict[str, Any]:
        """
        Load all annotations for a project
        
        Args:
            project_id: Project identifier
            
        Returns:
            All annotations data or None if not found
        """
        try:
            annotations_file = os.path.join(self.datasets_folder, project_id, 'annotations.json')
            
            if not os.path.exists(annotations_file):
                return None
                
            with open(annotations_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return None
    
    def get_frame_annotations(self, project_id: str, frame_index: int) -> List[Dict[str, Any]]:
        """
        Get annotations for a specific frame
        
        Args:
            project_id: Project identifier
            frame_index: Frame index
            
        Returns:
            List of annotations for the frame
        """
        try:
            annotations = self.load_annotations(project_id)
            if not annotations:
                return []
                
            frame_key = str(frame_index)
            frame_data = annotations.get('frames', {}).get(frame_key, {})
            return frame_data.get('annotations', [])
            
        except Exception as e:
            print(f"Error getting frame annotations: {e}")
            return []
    
    def delete_frame_annotations(self, project_id: str, frame_index: int) -> bool:
        """
        Delete all annotations for a specific frame
        
        Args:
            project_id: Project identifier
            frame_index: Frame index
            
        Returns:
            Success status
        """
        try:
            annotations_file = os.path.join(self.datasets_folder, project_id, 'annotations.json')
            
            if not os.path.exists(annotations_file):
                return False
                
            with open(annotations_file, 'r') as f:
                all_annotations = json.load(f)
            
            frame_key = str(frame_index)
            if frame_key in all_annotations.get('frames', {}):
                del all_annotations['frames'][frame_key]
                all_annotations['updated_at'] = datetime.now().isoformat()
                
                with open(annotations_file, 'w') as f:
                    json.dump(all_annotations, f, indent=2)
                    
                return True
                
        except Exception as e:
            print(f"Error deleting frame annotations: {e}")
            return False
    
    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics for a project
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project statistics
        """
        try:
            annotations = self.load_annotations(project_id)
            if not annotations:
                return {
                    'total_frames': 0,
                    'annotated_frames': 0,
                    'total_annotations': 0,
                    'classes': set()
                }
            
            frames = annotations.get('frames', {})
            total_frames = len(frames)
            annotated_frames = 0
            total_annotations = 0
            classes = set()
            
            for frame_data in frames.values():
                frame_annotations = frame_data.get('annotations', [])
                if frame_annotations:
                    annotated_frames += 1
                    total_annotations += len(frame_annotations)
                    for ann in frame_annotations:
                        if 'class' in ann:
                            classes.add(ann['class'])
            
            annotations_per_frame = total_annotations / total_frames if total_frames > 0 else 0
            
            # Calculate class distribution
            class_distribution = {}
            for ann_class in classes:
                class_count = sum(1 for frame_data in frames.values() 
                                for ann in frame_data.get('annotations', [])
                                if ann.get('class') == ann_class)
                class_distribution[ann_class] = class_count
            
            return {
                'total_frames': total_frames,
                'annotated_frames': annotated_frames,
                'total_annotations': total_annotations,
                'annotations_per_frame': annotations_per_frame,
                'classes': list(classes),
                'class_distribution': class_distribution
            }
            
        except Exception as e:
            print(f"Error getting project statistics: {e}")
            return {
                'total_frames': 0,
                'annotated_frames': 0,
                'total_annotations': 0,
                'classes': []
            }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects
        
        Returns:
            List of project dictionaries with metadata
        """
        try:
            if not os.path.exists(self.datasets_folder):
                return []
                
            projects = []
            for item in os.listdir(self.datasets_folder):
                project_dir = os.path.join(self.datasets_folder, item)
                if os.path.isdir(project_dir):
                    annotations_file = os.path.join(project_dir, 'annotations.json')
                    if os.path.exists(annotations_file):
                        # Try to load metadata
                        metadata = self.load_project_metadata(item)
                        project_info = {
                            'project_id': item,
                            'name': metadata.get('video_name', item),
                            'created_at': metadata.get('created_at', ''),
                            'frame_count': metadata.get('extracted_count', 0)
                        }
                        projects.append(project_info)
                        
            return projects
            
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []
    
    def save_project_metadata(self, project_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Save project metadata
        
        Args:
            project_id: Project identifier
            metadata: Metadata to save
            
        Returns:
            Success status
        """
        try:
            project_dir = os.path.join(self.datasets_folder, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            metadata_file = os.path.join(project_dir, 'metadata.json')
            metadata['updated_at'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error saving project metadata: {e}")
            return False
    
    def load_project_metadata(self, project_id: str) -> Dict[str, Any]:
        """Load project metadata"""
        try:
            metadata_file = os.path.join(self.datasets_folder, project_id, 'metadata.json')
            if not os.path.exists(metadata_file):
                return {}
            
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading project metadata: {e}")
            return {}
    
    def export_dataset(self, project_id: str, format_type: str = 'yolo') -> str:
        """
        Export dataset in specified format
        
        Args:
            project_id: Project identifier
            format_type: Export format ('yolo', 'coco', 'pascal_voc')
            
        Returns:
            Path to exported dataset
        """
        annotations_file = os.path.join(self.datasets_folder, project_id, 'annotations.json')
        
        if not os.path.exists(annotations_file):
            return None  # Return None for empty/nonexistent projects
        
        with open(annotations_file, 'r') as f:
            annotations_data = json.load(f)
        
        export_dir = os.path.join(self.datasets_folder, project_id, f'export_{format_type}')
        os.makedirs(export_dir, exist_ok=True)
        
        if format_type == 'yolo':
            return self._export_yolo(annotations_data, export_dir)
        elif format_type == 'coco':
            return self._export_coco(annotations_data, export_dir)
        elif format_type == 'pascal_voc':
            return self._export_pascal_voc(annotations_data, export_dir)
        else:
            return None  # Return None for unsupported formats
    
    def _export_yolo(self, annotations_data: Dict, export_dir: str) -> str:
        """Export in YOLO format"""
        # Create classes file
        classes = set()
        for frame_data in annotations_data.get('frames', {}).values():
            for ann in frame_data.get('annotations', []):
                classes.add(ann.get('class', 'object'))
        
        classes_list = sorted(list(classes))
        with open(os.path.join(export_dir, 'classes.txt'), 'w') as f:
            f.write('\n'.join(classes_list))
        
        # Create label files
        labels_dir = os.path.join(export_dir, 'labels')
        images_dir = os.path.join(export_dir, 'images')
        os.makedirs(labels_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        
        for frame_index_str, frame_data in annotations_data.get('frames', {}).items():
            frame_path = frame_data.get('frame_path', '')
            # Derive deterministic frame name using index if path missing
            if frame_path:
                frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            else:
                try:
                    idx = int(frame_index_str)
                    frame_name = f'frame_{idx:06d}'
                except Exception:
                    frame_name = f'frame_{frame_index_str}'

            # Determine image size. Prefer per-annotation image_width/height; else infer from file.
            image_width = None
            image_height = None
            anns = frame_data.get('annotations', [])
            if anns:
                image_width = anns[0].get('image_width')
                image_height = anns[0].get('image_height')
            if (image_width is None or image_height is None) and os.path.exists(frame_path):
                try:
                    from PIL import Image
                    with Image.open(frame_path) as im:
                        image_width, image_height = im.size
                except Exception:
                    pass
            if image_width is None or image_height is None:
                image_width, image_height = 1, 1  # Prevent division by zero; produces zeros

            # Copy image (create symlink or copy)
            import shutil
            if os.path.exists(frame_path):
                shutil.copy2(frame_path, os.path.join(images_dir, os.path.basename(frame_path)))

            # Create YOLO label file
            label_file = os.path.join(labels_dir, f'{frame_name}.txt')
            with open(label_file, 'w') as f:
                for ann in anns:
                    class_id = classes_list.index(ann.get('class', 'object'))

                    # Support two shapes:
                    # 1) Pixel fields at top-level: x,y,width,height
                    # 2) Dict under 'bbox'
                    if 'bbox' in ann and isinstance(ann['bbox'], dict):
                        bx = float(ann['bbox'].get('x', 0))
                        by = float(ann['bbox'].get('y', 0))
                        bw = float(ann['bbox'].get('width', 0))
                        bh = float(ann['bbox'].get('height', 0))
                    else:
                        bx = float(ann.get('x', 0))
                        by = float(ann.get('y', 0))
                        bw = float(ann.get('width', 0))
                        bh = float(ann.get('height', 0))

                    # If all values are <= 1, assume already normalized (top-left origin).
                    if bx <= 1.0 and by <= 1.0 and bw <= 1.0 and bh <= 1.0:
                        # Convert from normalized top-left + size to normalized center format
                        x_center = bx + bw / 2.0
                        y_center = by + bh / 2.0
                        width = bw
                        height = bh
                    else:
                        # Pixel coordinates: convert to normalized center-based YOLO format
                        x_center = (bx + bw / 2.0) / float(image_width)
                        y_center = (by + bh / 2.0) / float(image_height)
                        width = bw / float(image_width)
                        height = bh / float(image_height)

                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        # Create zip file
        import zipfile
        zip_path = export_dir + '.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _export_coco(self, annotations_data: Dict, export_dir: str) -> str:
        """Export in COCO format"""
        # Implement COCO format export
        coco_data = {
            "info": {
                "description": "VisionLabel Pro Dataset",
                "url": "",
                "version": "1.0",
                "year": 2024,
                "contributor": "",
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # Add categories
        classes = set()
        for frame_data in annotations_data.get('frames', {}).values():
            for ann in frame_data.get('annotations', []):
                classes.add(ann.get('class', 'object'))
        
        for i, class_name in enumerate(sorted(classes)):
            coco_data["categories"].append({
                "id": i,
                "name": class_name,
                "supercategory": "object"
            })
        
        annotation_id = 1
        for frame_data in annotations_data.get('frames', {}).values():
            frame_path = frame_data.get('frame_path', '')
            image_id = frame_data.get('frame_index', 0)
            
            # Add image info
            coco_data["images"].append({
                "id": image_id,
                "file_name": os.path.basename(frame_path),
                "width": frame_data.get('annotations', [{}])[0].get('image_width', 640),
                "height": frame_data.get('annotations', [{}])[0].get('image_height', 480)
            })
            
            # Add annotations
            for ann in frame_data.get('annotations', []):
                bbox = ann.get('bbox', {})
                class_name = ann.get('class', 'object')
                class_id = next(cat['id'] for cat in coco_data['categories'] if cat['name'] == class_name)
                
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": class_id,
                    "bbox": [bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)],
                    "area": bbox.get('width', 0) * bbox.get('height', 0),
                    "iscrowd": 0
                })
                annotation_id += 1
        
        # Save COCO JSON
        with open(os.path.join(export_dir, 'annotations.json'), 'w') as f:
            json.dump(coco_data, f, indent=2)
        
        # Create zip file
        import zipfile
        zip_path = export_dir + '.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _export_pascal_voc(self, annotations_data: Dict, export_dir: str) -> str:
        """Export in Pascal VOC XML format"""
        # Create XML annotations for each frame
        import xml.etree.ElementTree as ET
        
        for frame_data in annotations_data.get('frames', {}).values():
            frame_path = frame_data.get('frame_path', '')
            frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            
            # Create XML structure
            annotation = ET.Element('annotation')
            
            # Add filename
            filename = ET.SubElement(annotation, 'filename')
            filename.text = os.path.basename(frame_path)
            
            # Add size
            size = ET.SubElement(annotation, 'size')
            width = ET.SubElement(size, 'width')
            height = ET.SubElement(size, 'height')
            depth = ET.SubElement(size, 'depth')
            
            if frame_data.get('annotations'):
                first_ann = frame_data['annotations'][0]
                width.text = str(first_ann.get('image_width', 640))
                height.text = str(first_ann.get('image_height', 480))
                depth.text = '3'
            
            # Add objects
            for ann in frame_data.get('annotations', []):
                obj = ET.SubElement(annotation, 'object')
                
                name = ET.SubElement(obj, 'name')
                name.text = ann.get('class', 'object')
                
                bndbox = ET.SubElement(obj, 'bndbox')
                bbox = ann.get('bbox', {})
                
                xmin = ET.SubElement(bndbox, 'xmin')
                ymin = ET.SubElement(bndbox, 'ymin')
                xmax = ET.SubElement(bndbox, 'xmax')
                ymax = ET.SubElement(bndbox, 'ymax')
                
                xmin.text = str(int(bbox.get('x', 0)))
                ymin.text = str(int(bbox.get('y', 0)))
                xmax.text = str(int(bbox.get('x', 0) + bbox.get('width', 0)))
                ymax.text = str(int(bbox.get('y', 0) + bbox.get('height', 0)))
            
            # Save XML file
            tree = ET.ElementTree(annotation)
            xml_file = os.path.join(export_dir, f'{frame_name}.xml')
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        
        # Create zip file
        import zipfile
        zip_path = export_dir + '.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def delete_project(self, project_id: str) -> bool:
        """Delete all annotations for a project"""
        try:
            project_dir = os.path.join(self.datasets_folder, project_id)
            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir)
                return True
            return False
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False 