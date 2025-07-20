from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for, current_app
from flask_login import login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from .video_processor import VideoProcessor
from .data_storage import LabelStorage
from config import Config
import json

main_bp = Blueprint('main', __name__)

# Initialize processors
video_processor = None
label_storage = None

@main_bp.before_app_request
def initialize_processors():
    """Initialize processors with app config"""
    global video_processor, label_storage
    if video_processor is None:
        video_processor = VideoProcessor(current_app.config['FRAMES_FOLDER'])
    if label_storage is None:
        label_storage = LabelStorage(current_app.config['DATASETS_FOLDER'])

@main_bp.route('/')
@login_required
def index():
    """Main page - project selection or create new"""
    projects = video_processor.list_projects()
    return render_template('index.html', projects=projects)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_video():
    """Upload video and extract frames"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not Config.allowed_file(file.filename, current_app.config['ALLOWED_VIDEO_EXTENSIONS']):
        return jsonify({'error': 'Invalid file type. Allowed: ' + ', '.join(current_app.config['ALLOWED_VIDEO_EXTENSIONS'])}), 400
    
    try:
        # Save uploaded video
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(video_path)
        
        # Get processing parameters
        interval = float(request.form.get('interval', current_app.config['DEFAULT_FRAME_INTERVAL']))
        project_name = request.form.get('project_name', '').strip()
        
        # Validate interval
        if interval < current_app.config['MIN_FRAME_INTERVAL'] or interval > current_app.config['MAX_FRAME_INTERVAL']:
            return jsonify({'error': f'Interval must be between {current_app.config["MIN_FRAME_INTERVAL"]} and {current_app.config["MAX_FRAME_INTERVAL"]} seconds'}), 400
        
        # Extract frames
        project_id, frame_paths, metadata = video_processor.extract_frames(
            video_path, interval, project_name
        )
        
        # Store project in session
        session['current_project'] = project_id
        session['current_frame'] = 0
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'frame_count': len(frame_paths),
            'metadata': metadata,
            'redirect': url_for('main.annotate', project_id=project_id)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/project/<project_id>')
def load_project(project_id):
    """Load existing project"""
    try:
        metadata = video_processor.get_project_metadata(project_id)
        session['current_project'] = project_id
        session['current_frame'] = 0
        return redirect(url_for('main.annotate', project_id=project_id))
    except FileNotFoundError:
        return render_template('error.html', error='Project not found'), 404

@main_bp.route('/annotate/<project_id>')
@login_required
def annotate(project_id):
    """Main annotation interface"""
    try:
        metadata = video_processor.get_project_metadata(project_id)
        current_frame = session.get('current_frame', 0)
        
        # Get existing annotations for current frame
        annotations = label_storage.get_annotations(project_id, current_frame)
        
        return render_template('annotate.html', 
                             project_id=project_id,
                             metadata=metadata,
                             current_frame=current_frame,
                             annotations=annotations.get('annotations', []))
    except FileNotFoundError:
        return render_template('error.html', error='Project not found'), 404

@main_bp.route('/api/frame/<project_id>/<int:frame_index>')
def get_frame(project_id, frame_index):
    """Get specific frame image"""
    try:
        frame_path = video_processor.get_frame_path(project_id, frame_index)
        return send_file(frame_path, mimetype='image/jpeg')
    except (FileNotFoundError, IndexError) as e:
        return jsonify({'error': str(e)}), 404

@main_bp.route('/api/annotations/<project_id>/<int:frame_index>', methods=['GET'])
def get_annotations(project_id, frame_index):
    """Get annotations for specific frame"""
    annotations = label_storage.get_annotations(project_id, frame_index)
    return jsonify(annotations)

@main_bp.route('/api/annotations/<project_id>/<int:frame_index>', methods=['POST'])
def save_annotations(project_id, frame_index):
    """Save annotations for specific frame"""
    try:
        data = request.get_json()
        annotations = data.get('annotations', [])
        
        # Add IDs to annotations if not present
        for i, ann in enumerate(annotations):
            if 'id' not in ann:
                ann['id'] = f"{frame_index}_{i}_{uuid.uuid4().hex[:8]}"
        
        # Get frame path for metadata
        frame_path = video_processor.get_frame_path(project_id, frame_index)
        
        success = label_storage.save_annotation(project_id, frame_index, frame_path, annotations)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to save annotations'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/annotations/<project_id>/<int:frame_index>/<annotation_id>', methods=['DELETE'])
def delete_annotation(project_id, frame_index, annotation_id):
    """Delete specific annotation"""
    try:
        success = label_storage.delete_annotation(project_id, frame_index, annotation_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Annotation not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/navigate/<project_id>', methods=['POST'])
def navigate_frame(project_id):
    """Navigate to specific frame"""
    try:
        data = request.get_json()
        frame_index = data.get('frame_index')
        
        metadata = video_processor.get_project_metadata(project_id)
        max_frames = metadata['extracted_count']
        
        if frame_index < 0 or frame_index >= max_frames:
            return jsonify({'error': 'Frame index out of range'}), 400
        
        session['current_frame'] = frame_index
        
        # Get annotations for new frame
        annotations = label_storage.get_annotations(project_id, frame_index)
        
        return jsonify({
            'success': True,
            'frame_index': frame_index,
            'annotations': annotations.get('annotations', []),
            'total_frames': max_frames
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/export/<project_id>')
@login_required
def export_page(project_id):
    """Export page for dataset"""
    try:
        metadata = video_processor.get_project_metadata(project_id)
        annotations = label_storage.get_annotations(project_id)
        
        # Count annotated frames
        annotated_frames = len([f for f in annotations.get('frames', {}).values() 
                               if f.get('annotations')])
        
        return render_template('export.html',
                             project_id=project_id,
                             metadata=metadata,
                             annotated_frames=annotated_frames,
                             export_formats=current_app.config['EXPORT_FORMATS'])
    except FileNotFoundError:
        return render_template('error.html', error='Project not found'), 404

@main_bp.route('/api/export/<project_id>/<format_type>')
@login_required
def export_dataset(project_id, format_type):
    """Export dataset in specified format"""
    try:
        if format_type not in current_app.config['EXPORT_FORMATS']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        export_path = label_storage.export_dataset(project_id, format_type)
        
        # Create ZIP file of export
        import shutil
        zip_path = f"{export_path}.zip"
        shutil.make_archive(export_path, 'zip', export_path)
        
        return send_file(zip_path, 
                        as_attachment=True,
                        download_name=f"{project_id}_{format_type}_dataset.zip",
                        mimetype='application/zip')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/projects', methods=['GET'])
def list_projects():
    """API endpoint to list all projects"""
    projects = video_processor.list_projects()
    return jsonify({'projects': projects})

@main_bp.route('/api/project/<project_id>/stats')
def project_stats(project_id):
    """Get project statistics"""
    try:
        metadata = video_processor.get_project_metadata(project_id)
        annotations = label_storage.get_annotations(project_id)
        
        total_frames = metadata['extracted_count']
        annotated_frames = len([f for f in annotations.get('frames', {}).values() 
                               if f.get('annotations')])
        
        # Count total annotations
        total_annotations = sum(len(f.get('annotations', [])) 
                               for f in annotations.get('frames', {}).values())
        
        # Count classes
        classes = set()
        for frame_data in annotations.get('frames', {}).values():
            for ann in frame_data.get('annotations', []):
                classes.add(ann.get('class', 'object'))
        
        stats = {
            'total_frames': total_frames,
            'annotated_frames': annotated_frames,
            'completion_percentage': (annotated_frames / total_frames * 100) if total_frames > 0 else 0,
            'total_annotations': total_annotations,
            'unique_classes': len(classes),
            'classes': sorted(list(classes))
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project/<project_id>', methods=['DELETE'])
def delete_project_api(project_id):
    """Delete a project and all its data (REST API endpoint)"""
    try:
        # Delete from video processor (frames and project data)
        if hasattr(video_processor, 'delete_project'):
            video_processor.delete_project(project_id)
        
        # Delete from label storage (annotations)
        if hasattr(label_storage, 'delete_project'):
            label_storage.delete_project(project_id)
        
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/delete_project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and all its data (legacy endpoint)"""
    return delete_project_api(project_id)

# Error handlers
@main_bp.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500 