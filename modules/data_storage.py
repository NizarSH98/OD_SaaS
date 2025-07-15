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
                frame_data = all_annotations['frames'][frame_key]
                frame_data['annotations'] = [
                    ann for ann in frame_data['annotations'] 
                    if ann.get('id') != annotation_id
                ]
                frame_data['updated_at'] = datetime.now().isoformat()
                all_annotations['updated_at'] = datetime.now().isoformat()
                
                with open(annotations_file, 'w') as f:
                    json.dump(all_annotations, f, indent=2)
                    
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting annotation: {e}")
            return False
    
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
            raise FileNotFoundError(f"No annotations found for project {project_id}")
        
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
            raise ValueError(f"Unsupported export format: {format_type}")
    
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
        
        for frame_data in annotations_data.get('frames', {}).values():
            frame_path = frame_data.get('frame_path', '')
            frame_name = os.path.splitext(os.path.basename(frame_path))[0]
            
            # Copy image (create symlink or copy)
            import shutil
            if os.path.exists(frame_path):
                shutil.copy2(frame_path, os.path.join(images_dir, os.path.basename(frame_path)))
            
            # Create YOLO label file
            label_file = os.path.join(labels_dir, f'{frame_name}.txt')
            with open(label_file, 'w') as f:
                for ann in frame_data.get('annotations', []):
                    class_id = classes_list.index(ann.get('class', 'object'))
                    
                    # Convert bounding box to YOLO format (normalized)
                    bbox = ann.get('bbox', {})
                    x_center = (bbox.get('x', 0) + bbox.get('width', 0) / 2) / ann.get('image_width', 1)
                    y_center = (bbox.get('y', 0) + bbox.get('height', 0) / 2) / ann.get('image_height', 1)
                    width = bbox.get('width', 0) / ann.get('image_width', 1)
                    height = bbox.get('height', 0) / ann.get('image_height', 1)
                    
                    f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
        
        return export_dir
    
    def _export_coco(self, annotations_data: Dict, export_dir: str) -> str:
        """Export in COCO format"""
        # Implement COCO format export
        coco_data = {
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
        
        return export_dir
    
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
        
        return export_dir
    
    def delete_project(self, project_id: str) -> bool:
        """Delete all annotations for a project"""
        annotations_file = os.path.join(self.datasets_folder, f"{project_id}_annotations.json")
        if os.path.exists(annotations_file):
            os.remove(annotations_file)
            return True
        return False 