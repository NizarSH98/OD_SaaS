# Video Labeling Tool

A modern, web-based Flask application for creating labeled datasets from videos. This tool allows you to extract frames from videos and create bounding box annotations for computer vision model training.

## Features

- **Video Upload & Processing**: Upload videos and extract frames at customizable intervals
- **Interactive Annotation**: Click and drag to create bounding boxes on frames
- **Multiple Export Formats**: Export datasets in YOLO, COCO, and Pascal VOC formats
- **Modern UI**: Responsive, user-friendly interface with Bootstrap styling
- **Project Management**: Organize multiple annotation projects
- **Auto-Save**: Automatic saving of annotations with manual override option
- **Keyboard Shortcuts**: Efficient navigation and annotation controls
- **Progress Tracking**: Visual progress indicators and statistics

## Project Structure

```
OD_SaaS/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── modules/
│   ├── __init__.py
│   ├── video_processor.py    # Video processing and frame extraction
│   ├── data_storage.py       # Annotation storage and export
│   └── routes.py             # Flask routes and API endpoints
├── templates/
│   ├── base.html            # Base template with navigation
│   ├── index.html           # Project listing page
│   ├── upload.html          # Video upload interface
│   ├── annotate.html        # Main annotation interface
│   ├── export.html          # Dataset export page
│   └── error.html           # Error handling page
├── uploads/                 # Uploaded video files
├── frames/                  # Extracted frame images
└── datasets/               # Annotation data and exports
```

## Installation & Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### 1. Clone or Download the Project

```bash
# If you have the project files, navigate to the project directory
cd OD_SaaS
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### 1. Upload a Video

1. Navigate to the home page
2. Click "Upload Video" or "New Project"
3. Select your video file (supports MP4, AVI, MOV, MKV, FLV, WMV, WebM)
4. Set the frame extraction interval (0.1 - 10.0 seconds)
5. Optionally provide a project name
6. Click "Start Processing Video"

### 2. Annotate Frames

1. After processing, you'll be redirected to the annotation interface
2. Use the frame navigation controls to move between frames
3. Enter a class/label name (e.g., "person", "car", "dog")
4. Click "Draw Box" to enable drawing mode
5. Click and drag on the image to create bounding boxes
6. Annotations are auto-saved by default

### 3. Navigation Controls

- **Arrow Keys**: Navigate between frames
- **Space**: Toggle draw mode
- **Delete**: Remove selected annotation
- **Ctrl+S**: Manually save annotations
- **Escape**: Cancel current drawing

### 4. Export Dataset

1. Click "Export" in the annotation interface
2. Choose your preferred format:
   - **YOLO**: For YOLO object detection models
   - **COCO**: JSON format for various frameworks
   - **Pascal VOC**: XML format for traditional CV tools
3. Download the generated ZIP file

## Supported Video Formats

- MP4
- AVI
- MOV
- MKV
- FLV
- WMV
- WebM

## Export Formats

### YOLO Format
- `labels/` folder with `.txt` files containing normalized coordinates
- `images/` folder with frame images
- `classes.txt` file with class names

### COCO Format
- `annotations.json` with complete metadata
- Category definitions and image information
- Compatible with many ML frameworks

### Pascal VOC Format
- Individual `.xml` files for each frame
- Detailed annotation metadata
- Compatible with traditional computer vision tools

## Configuration

Edit `config.py` to customize:

- Upload file size limits
- Supported video formats
- Frame extraction settings
- Export formats
- Directory paths

## API Endpoints

- `GET /` - Home page with project listing
- `POST /upload` - Upload and process video
- `GET /annotate/<project_id>` - Annotation interface
- `GET /api/frame/<project_id>/<frame_index>` - Get frame image
- `POST /api/annotations/<project_id>/<frame_index>` - Save annotations
- `GET /api/export/<project_id>/<format>` - Export dataset

## Technologies Used

- **Backend**: Flask, OpenCV, Python
- **Frontend**: Bootstrap 5, jQuery, HTML5 Canvas
- **Storage**: JSON files for annotations
- **Processing**: OpenCV for video frame extraction

## Development Features

- **Modular Architecture**: Separated concerns for easy extension
- **Clean Code**: Well-documented and organized codebase
- **Error Handling**: Comprehensive error handling and user feedback
- **Responsive Design**: Works on desktop and mobile devices
- **Extensible**: Easy to add new export formats or features

## Troubleshooting

### Common Issues

1. **Video won't upload**: Check file size (max 500MB) and format
2. **Frames not displaying**: Ensure video processed successfully
3. **Annotations not saving**: Check auto-save is enabled or save manually
4. **Export failing**: Ensure you have annotated frames to export

### Performance Tips

- Use smaller frame intervals for detailed annotation
- Larger intervals for faster processing
- Clear old projects periodically to save disk space

## Future Enhancements

This modular architecture allows for easy extension:

- Multi-object tracking across frames
- Polygon annotation support
- Collaborative annotation features
- Integration with ML training pipelines
- Cloud storage support
- Advanced export options

## License

This project is designed for educational and development purposes. Feel free to modify and extend as needed.

## Support

For issues or questions, check the error logs in the console or browser developer tools. The application provides detailed error messages to help with troubleshooting. 