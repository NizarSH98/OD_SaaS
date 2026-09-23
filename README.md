# Computer-Vision Dataset Tool

A browser-based computer-vision workflow for turning video into labeled object-detection datasets.

The system covers the practical data-preparation loop:

**video upload → frame extraction → bounding-box annotation → dataset export**

It was built to make object-detection dataset creation usable from a web interface rather than requiring a local annotation toolchain.

## What it demonstrates

- Flask backend and route design
- OpenCV video processing and frame extraction
- browser-based bounding-box annotation
- project-level annotation persistence
- dataset export to multiple training formats
- modular separation between routes, processing, and storage
- error handling and generated-data hygiene

## Supported workflow

1. Create a project and upload a video.
2. Extract frames at a configurable interval.
3. Annotate objects with bounding boxes in the browser.
4. Navigate through frames with keyboard controls.
5. Export the dataset for downstream model training.

## Export formats

- **YOLO**
- **COCO**
- **Pascal VOC**

## Architecture

```text
OD_SaaS/
├── app.py
├── config.py
├── requirements.txt
├── modules/
│   ├── video_processor.py
│   ├── data_storage.py
│   └── routes.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── annotate.html
│   ├── export.html
│   └── error.html
├── uploads/
├── frames/
└── datasets/
```

Runtime media and generated datasets are excluded from source control.

## Stack

**Backend:** Python, Flask  
**Computer vision:** OpenCV  
**Frontend:** HTML5 Canvas, Bootstrap, JavaScript / jQuery  
**Data:** JSON-based annotation storage

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5000
```

## Why this project matters

Model quality depends heavily on data quality and annotation workflow. This project focuses on the engineering around the model—ingestion, human labeling, data structure, export compatibility, and usability.

It is part of my broader work across applied AI, computer vision, RAG systems, and AI tooling.

[Portfolio](https://nizarsh98.github.io/portfolio-classic.html)
