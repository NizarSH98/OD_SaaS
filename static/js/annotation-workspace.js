// Simplified annotation workspace with bounding box tool
class AnnotationWorkspace {
    constructor() {
        const container = document.querySelector('.annotation-workspace');
        this.projectId = container.dataset.projectId;
        this.currentFrame = parseInt(container.dataset.currentFrame) || 0;
        this.totalFrames = parseInt(container.dataset.totalFrames) || 0;
        this.annotations = [];
        this.selectedAnnotation = null;
        this.autoSave = true;
        this.isDirty = false;
        this.bboxWidth = 100;
        this.bboxHeight = 100;
        this.currentLabel = 'object';
		// Zoom state
		this.zoom = 1;
		this.minZoom = 0.5;
		this.maxZoom = 3.0;
		this.zoomStep = 0.1;
		// Drawing state
		this.bboxModeEnabled = true;
		this.creationMode = 'drag'; // 'click' | 'drag'
		this.isDrawing = false;
		this.dragStart = null; // {x, y} in display coords
		this.tempBoxEl = null;
		// Move state
		this.isMoving = false;
		this.moveTargetId = null;
		this.moveOffset = { x: 0, y: 0 };
		// Hover state
		this.isHoveringBox = false;
		this.hoveredBoxId = null;
		// Click creation suppression to avoid accidental click after drag
		this.suppressClickCreation = false;
		// Drag robustness
		this.minDragThreshold = 4; // pixels
		this.isGlobalDragListenersAttached = false;
		this.saveDebounceMs = 400;
		this._saveTimer = null;
		
		// Bind event handlers once so we can reliably add/remove listeners
		this.handleImageClickBound = this.handleImageClick.bind(this);
		this.onPointerDownBound = this.onPointerDown.bind(this);
		this.onPointerMoveBound = this.onPointerMove.bind(this);
		this.onPointerUpBound = this.onPointerUp.bind(this);
		this.onHoverMoveBound = this.onHoverMove.bind(this);
        
        this.init();
    }
    
    init() {
        this.setupKeyboardShortcuts();
        this.setupSidebarToggle();
        this.setupBoundingBoxSettings();
		this.setupZoomControls();
        this.setupResizeListener();
        this.loadInitialFrame();
        this.loadCurrentFrameAnnotations();
        this.updateFrameNavigation();
    }
    
    setupResizeListener() {
        // Update overlay position when window is resized
        window.addEventListener('resize', () => {
            this.updateOverlayPosition();
            this.renderBoundingBoxes();
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.matches('input, textarea, select')) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousFrame();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextFrame();
                    break;
                case 'b':
                case 'B':
                    e.preventDefault();
                    this.toggleBoundingBoxMode();
                    break;
                case 'n':
                case 'N':
                    e.preventDefault();
                    this.nextFrameAfterAnnotation();
                    break;
                case 'Delete':
                case 'Backspace':
                    e.preventDefault();
                    this.deleteSelected();
                    break;
                case 'Escape':
                    this.cancelCurrentAction();
                    break;
            }
        });
    }
    
    setupSidebarToggle() {
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('workspaceSidebar');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
            });
        }
    }
    
    setupBoundingBoxSettings() {
        const bboxWidthInput = document.getElementById('bboxWidth');
        const bboxHeightInput = document.getElementById('bboxHeight');
        const classInput = document.getElementById('classInput');
		const modeClickBtn = document.getElementById('modeClick');
		const modeDragBtn = document.getElementById('modeDrag');
        
        if (bboxWidthInput) {
            bboxWidthInput.addEventListener('change', (e) => {
                this.bboxWidth = parseInt(e.target.value);
            });
        }
        
        if (bboxHeightInput) {
            bboxHeightInput.addEventListener('change', (e) => {
                this.bboxHeight = parseInt(e.target.value);
            });
        }
        
        if (classInput) {
            classInput.addEventListener('change', (e) => {
                this.currentLabel = e.target.value;
            });
        }
        
        // Set up class suggestions
        const classSuggestions = document.querySelectorAll('.class-suggestion');
        classSuggestions.forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                if (classInput) {
                    classInput.value = suggestion.textContent;
                    this.currentLabel = suggestion.textContent;
                }
            });
        });

		// Creation mode buttons
		if (modeClickBtn && modeDragBtn) {
			modeClickBtn.addEventListener('click', () => {
				modeClickBtn.classList.add('active');
				modeDragBtn.classList.remove('active');
				this.creationMode = 'click';
			});
			modeDragBtn.addEventListener('click', () => {
				modeDragBtn.classList.add('active');
				modeClickBtn.classList.remove('active');
				this.creationMode = 'drag';
			});
		}
    }
    
    loadInitialFrame() {
        const image = document.getElementById('annotationImage');
        const loadingContainer = document.getElementById('loadingContainer');
        
        if (!image) return;
        
        if (loadingContainer) {
            loadingContainer.style.display = 'flex';
        }
        image.style.display = 'none';
        
        image.onload = () => {
            console.log('Frame loaded successfully');
            if (loadingContainer) {
                loadingContainer.style.display = 'none';
            }
            image.style.display = 'block';
            this.imageReady = true;
            this.setupBoundingBoxTool();
            // Ensure annotations render after image metrics are available
            this.renderBoundingBoxes();
        };
        
        image.onerror = () => {
            console.error('Failed to load frame');
            if (loadingContainer) {
                loadingContainer.style.display = 'none';
            }
            this.imageReady = false;
            this.showNotification('Failed to load frame', 'error');
        };
        
        console.log(`Loading frame: /api/frame/${this.projectId}/${this.currentFrame}`);
        image.src = `/api/frame/${this.projectId}/${this.currentFrame}`;
    }
    
    setupBoundingBoxTool() {
        const image = document.getElementById('annotationImage');
        const overlay = document.getElementById('imageOverlay');
        
        if (!image) return;
        
		// Remove any prior listeners
		image.removeEventListener('mousedown', this.onPointerDownBound);
		image.removeEventListener('mousemove', this.onPointerMoveBound);
		image.removeEventListener('mouseup', this.onPointerUpBound);
		image.removeEventListener('click', this.handleImageClickBound);
		if (overlay) {
			overlay.removeEventListener('mousedown', this.onPointerDownBound);
			overlay.removeEventListener('mousemove', this.onPointerMoveBound);
			overlay.removeEventListener('mouseup', this.onPointerUpBound);
			overlay.removeEventListener('click', this.handleImageClickBound);
		}
		
		// Use pointer events for drawing on overlay (preferred)
		if (overlay) {
			overlay.addEventListener('mousedown', this.onPointerDownBound);
			overlay.addEventListener('mousemove', this.onPointerMoveBound, { passive: true });
			overlay.addEventListener('mouseup', this.onPointerUpBound);
			// Track hover for edit intent
			overlay.addEventListener('mousemove', this.onHoverMoveBound, { passive: true });
			// Click placement for click mode
			overlay.addEventListener('click', this.handleImageClickBound);
		} else {
			// Fallback to image if overlay missing
			image.addEventListener('mousedown', this.onPointerDownBound);
			image.addEventListener('mousemove', this.onPointerMoveBound, { passive: true });
			image.addEventListener('mouseup', this.onPointerUpBound);
			image.addEventListener('mousemove', this.onHoverMoveBound, { passive: true });
			image.addEventListener('click', this.handleImageClickBound);
		}
        
        // Update overlay positioning to match image (only when image metrics are valid)
        this.updateOverlayPosition();
        
        console.log('Bounding box tool activated');
    }

	setupZoomControls() {
		const zoomInBtn = document.getElementById('zoomIn');
		const zoomOutBtn = document.getElementById('zoomOut');
		const zoomResetBtn = document.getElementById('zoomReset');
		
		if (zoomInBtn) zoomInBtn.addEventListener('click', () => this.setZoom(this.zoom + this.zoomStep));
		if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => this.setZoom(this.zoom - this.zoomStep));
		if (zoomResetBtn) zoomResetBtn.addEventListener('click', () => this.setZoom(1));
	}

	setZoom(newZoom) {
		this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, newZoom));
		const image = document.getElementById('annotationImage');
		const overlay = document.getElementById('imageOverlay');
		if (image) {
			image.style.transformOrigin = 'top left';
			image.style.transform = `scale(${this.zoom})`;
		}
		if (overlay) {
			overlay.style.transformOrigin = 'top left';
			overlay.style.transform = `scale(${this.zoom})`;
		}
		// Reposition overlay to align after scaling
		this.updateOverlayPosition();
	}
    
    updateOverlayPosition() {
        const image = document.getElementById('annotationImage');
        const overlay = document.getElementById('imageOverlay');
        
        if (!image || !overlay) return;
        
        const imageRect = image.getBoundingClientRect();
        const containerRect = image.parentElement.getBoundingClientRect();
        
        // Calculate the offset between image and container
        const imageOffsetX = imageRect.left - containerRect.left;
        const imageOffsetY = imageRect.top - containerRect.top;
        
        // Position the overlay to match the image exactly
        overlay.style.left = `${imageOffsetX}px`;
        overlay.style.top = `${imageOffsetY}px`;
        overlay.style.width = `${imageRect.width}px`;
        overlay.style.height = `${imageRect.height}px`;
        
        console.log('Updated overlay position:', { imageOffsetX, imageOffsetY, width: imageRect.width, height: imageRect.height });
    }
    
    handleImageClick(event) {
        // If we just dragged (move/resize/draw), suppress click creation
        if (this.suppressClickCreation) {
            this.suppressClickCreation = false;
            return;
        }
        // If hovering a box, interpret click as selection/edit, not creation
        if (this.isHoveringBox) return;
        if (this.creationMode !== 'click') return; // Only in click mode
        console.log('Image click detected', event);
        
        // Get the image element
        const image = document.getElementById('annotationImage');
        if (!image) {
            console.error('Image element not found');
            return;
        }
        
        const imageRect = image.getBoundingClientRect();
        
        // Calculate click position relative to the image element
        const clickX = event.clientX - imageRect.left;
        const clickY = event.clientY - imageRect.top;
        
        // Check if click is within image element bounds
        if (clickX < 0 || clickX > imageRect.width || clickY < 0 || clickY > imageRect.height) {
            console.log('Click outside image element bounds');
            return;
        }
        
        // Convert click position directly to image coordinates
        const scaleX = image.naturalWidth / imageRect.width;
        const scaleY = image.naturalHeight / imageRect.height;
        
        const imageX = clickX * scaleX;
        const imageY = clickY * scaleY;
        
        console.log('Click position:', { clickX, clickY });
        console.log('Image coordinates:', { imageX, imageY });
        console.log('Image natural size:', { width: image.naturalWidth, height: image.naturalHeight });
        console.log('Image display size:', { width: imageRect.width, height: imageRect.height });
        
        // Create bounding box centered on click position
        let bboxX = imageX - (this.bboxWidth / 2);  // Center horizontally
        let bboxY = imageY - (this.bboxHeight / 2);  // Center vertically
        
        // Ensure bounding box stays within image boundaries
        const originalBboxX = bboxX;
        const originalBboxY = bboxY;
        
        bboxX = Math.max(0, Math.min(bboxX, image.naturalWidth - this.bboxWidth));
        bboxY = Math.max(0, Math.min(bboxY, image.naturalHeight - this.bboxHeight));
        
        // If the bounding box was adjusted, show a notification
        if (originalBboxX !== bboxX || originalBboxY !== bboxY) {
            this.showNotification('Bounding box adjusted to stay within image boundaries', 'info');
        }
        
        const bbox = {
            id: `bbox_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'bbox',
            x: bboxX,
            y: bboxY,
            width: this.bboxWidth,
            height: this.bboxHeight,
            class: this.currentLabel,
            created_at: new Date().toISOString(),
            image_width: image.naturalWidth,
            image_height: image.naturalHeight,
            bbox: { x: bboxX, y: bboxY, width: this.bboxWidth, height: this.bboxHeight }
        };
        
        console.log('Creating bounding box:', bbox);
        console.log('Bounding box will be centered at:', { 
            centerX: bboxX + (this.bboxWidth / 2), 
            centerY: bboxY + (this.bboxHeight / 2) 
        });
        console.log('Click position (display coordinates):', { clickX, clickY });
        console.log('Expected bounding box position (display coordinates):', { 
            x: bboxX * (imageRect.width / image.naturalWidth), 
            y: bboxY * (imageRect.height / image.naturalHeight) 
        });
        
        // Show visual feedback for click position
        this.showClickIndicator(clickX, clickY);
        
        this.addBoundingBox(bbox);
        this.showNotification(`Added ${this.currentLabel} bounding box`, 'success');
    }
    
    addBoundingBox(bbox) {
        this.annotations.push(bbox);
        this.isDirty = true;
        this.updateAnnotationsList();
        this.updateAnnotationCount();
        this.renderBoundingBoxes();
        
        if (this.autoSave) {
            this.saveAnnotations();
        }
    }

	// Pointer-based drawing for bounding boxes
    onPointerDown(event) {
        if (!this.bboxModeEnabled) return;
		const image = document.getElementById('annotationImage');
		const overlay = document.getElementById('imageOverlay');
		if (!image || !overlay) return;
		const rect = image.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;
		if (x < 0 || y < 0 || x > rect.width || y > rect.height) return;

        // If the target is an existing bbox or its handle, start move/resize, not draw
        const targetEl = event.target;
        const bboxEl = targetEl && targetEl.closest ? targetEl.closest('.bbox-overlay') : null;
        if (bboxEl) {
            const id = bboxEl.dataset.id;
            this.selectBoundingBox(id);
            // Determine if resizing
            if (targetEl.classList && targetEl.classList.contains('resize-handle')) {
                this.isResizing = true;
                this.resizeHandle = Array.from(targetEl.classList).find(c => c.startsWith('handle-'));
                // Record starting geometry for stability
                const ann = this.annotations.find(a => a.id === id);
                if (ann) {
                    this.resizeStart = { x: ann.x, y: ann.y, w: ann.width, h: ann.height };
                }
            } else {
                this.isMoving = true;
                this.moveTargetId = id;
                this.moveStart = { x, y };
            }
            return;
        }

        // If hovering a box, we are editing, not drawing
        if (this.isHoveringBox) return;
        if (this.creationMode !== 'drag') return; // Only draw in drag mode

        this.isDrawing = true;
        this.dragStart = { x, y };
        // Temp visual
        this.tempBoxEl = document.createElement('div');
        this.tempBoxEl.className = 'bbox-overlay';
        this.tempBoxEl.style.left = `${x}px`;
        this.tempBoxEl.style.top = `${y}px`;
        this.tempBoxEl.style.width = '0px';
        this.tempBoxEl.style.height = '0px';
        overlay.appendChild(this.tempBoxEl);
	}

    onPointerMove(event) {
        const image = document.getElementById('annotationImage');
        const rect = image.getBoundingClientRect();
        let x = event.clientX - rect.left;
        let y = event.clientY - rect.top;
        x = Math.max(0, Math.min(x, rect.width));
        y = Math.max(0, Math.min(y, rect.height));

        // Update hover flag
        this.updateHoverFlag(event);

        // Move existing bbox
        if (this.isMoving && this.moveTargetId) {
            const dx = x - this.moveStart.x;
            const dy = y - this.moveStart.y;
            this.moveStart = { x, y };
            const ann = this.annotations.find(a => a.id === this.moveTargetId);
            if (ann) {
                const scaleX = image.naturalWidth / rect.width;
                const scaleY = image.naturalHeight / rect.height;
                const newX = Math.max(0, Math.min(ann.x + dx * scaleX, image.naturalWidth - ann.width));
                const newY = Math.max(0, Math.min(ann.y + dy * scaleY, image.naturalHeight - ann.height));
                if (newX !== ann.x || newY !== ann.y) {
                    ann.x = newX;
                    ann.y = newY;
                    if (ann.bbox) { ann.bbox.x = ann.x; ann.bbox.y = ann.y; }
                    this.isDirty = true;
                    this.renderBoundingBoxes();
                }
            }
            // mark that a drag occurred to suppress subsequent click-create
            this.suppressClickCreation = true;
            return;
        }

        // Resize existing bbox
        if (this.isResizing && this.selectedAnnotation && this.resizeHandle) {
            const ann = this.selectedAnnotation;
            const scaleX = image.naturalWidth / rect.width;
            const scaleY = image.naturalHeight / rect.height;
            const leftDisplay = ann.x / scaleX;
            const topDisplay = ann.y / scaleY;
            const rightDisplay = (ann.x + ann.width) / scaleX;
            const bottomDisplay = (ann.y + ann.height) / scaleY;

            let newLeft = leftDisplay, newTop = topDisplay, newRight = rightDisplay, newBottom = bottomDisplay;
            if (this.resizeHandle.includes('nw')) { newLeft = x; newTop = y; }
            if (this.resizeHandle.includes('ne')) { newRight = x; newTop = y; }
            if (this.resizeHandle.includes('sw')) { newLeft = x; newBottom = y; }
            if (this.resizeHandle.includes('se')) { newRight = x; newBottom = y; }
            // Normalize
            const l = Math.max(0, Math.min(newLeft, newRight));
            const t = Math.max(0, Math.min(newTop, newBottom));
            const r = Math.min(rect.width, Math.max(newLeft, newRight));
            const b = Math.min(rect.height, Math.max(newTop, newBottom));
            const newX2 = l * scaleX;
            const newY2 = t * scaleY;
            const newW2 = Math.max(1, (r - l) * scaleX);
            const newH2 = Math.max(1, (b - t) * scaleY);
            if (newX2 !== ann.x || newY2 !== ann.y || newW2 !== ann.width || newH2 !== ann.height) {
                ann.x = newX2;
                ann.y = newY2;
                ann.width = newW2;
                ann.height = newH2;
                if (ann.bbox) { ann.bbox.x = ann.x; ann.bbox.y = ann.y; ann.bbox.width = ann.width; ann.bbox.height = ann.height; }
                this.isDirty = true;
                this.renderBoundingBoxes();
            }
            // mark that a drag occurred to suppress subsequent click-create
            this.suppressClickCreation = true;
            return;
        }

        if (!this.isDrawing || !this.dragStart) return;
		const startX = this.dragStart.x;
		const startY = this.dragStart.y;
		const left = Math.min(startX, x);
		const top = Math.min(startY, y);
		const width = Math.abs(x - startX);
		const height = Math.abs(y - startY);
		if (this.tempBoxEl) {
			this.tempBoxEl.style.left = `${left}px`;
			this.tempBoxEl.style.top = `${top}px`;
			this.tempBoxEl.style.width = `${width}px`;
			this.tempBoxEl.style.height = `${height}px`;
		}
	}

    onPointerUp(event) {
        // End move/resize
        if (this.isMoving || this.isResizing) {
            this.isMoving = false;
            this.isResizing = false;
            this.moveTargetId = null;
            this.resizeHandle = null;
            if (this.autoSave) {
                if (this._saveTimer) clearTimeout(this._saveTimer);
                this._saveTimer = setTimeout(() => this.saveAnnotations(), this.saveDebounceMs);
            }
            return;
        }
        if (!this.isDrawing) return;
        const image = document.getElementById('annotationImage');
        const rect = image.getBoundingClientRect();
        let x = event.clientX - rect.left;
        let y = event.clientY - rect.top;
        x = Math.max(0, Math.min(x, rect.width));
        y = Math.max(0, Math.min(y, rect.height));
		const startX = this.dragStart.x;
		const startY = this.dragStart.y;
		const left = Math.min(startX, x);
		const top = Math.min(startY, y);
		const widthDisplay = Math.abs(x - startX);
		const heightDisplay = Math.abs(y - startY);
        // Ignore tiny drags; do not create on release (click handler handles creation immediately)
        if (widthDisplay < 3 || heightDisplay < 3) {
            this.isDrawing = false;
            this.dragStart = null;
            if (this.tempBoxEl) { this.tempBoxEl.remove(); this.tempBoxEl = null; }
            return;
        }
		// Convert to image coords
		const scaleX = image.naturalWidth / rect.width;
		const scaleY = image.naturalHeight / rect.height;
		const bbox = {
			id: `bbox_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
			type: 'bbox',
			x: left * scaleX,
			y: top * scaleY,
			width: widthDisplay * scaleX,
			height: heightDisplay * scaleY,
			class: this.currentLabel,
			created_at: new Date().toISOString(),
			image_width: image.naturalWidth,
			image_height: image.naturalHeight,
			bbox: { x: left * scaleX, y: top * scaleY, width: widthDisplay * scaleX, height: heightDisplay * scaleY }
		};
		this.isDrawing = false;
		this.dragStart = null;
		if (this.tempBoxEl) { this.tempBoxEl.remove(); this.tempBoxEl = null; }
        this.addBoundingBox(bbox);
        // mark drag to prevent following click-create
        this.suppressClickCreation = true;
		this.showNotification(`Added ${this.currentLabel} bounding box`, 'success');
	}
    
    renderBoundingBoxes() {
        const image = document.getElementById('annotationImage');
        const overlay = document.getElementById('imageOverlay');
        
        if (!image || !overlay) return;
        
        // Clear existing overlays
        overlay.innerHTML = '';
        
        // Update overlay positioning to match image
        this.updateOverlayPosition();
        
        // Get the image rect for proper positioning
        const imageRect = image.getBoundingClientRect();
        
        // Guard against zero or missing natural sizes to avoid NaN scaling
        const naturalW = image.naturalWidth || 1;
        const naturalH = image.naturalHeight || 1;
        const scaleX = imageRect.width / naturalW;
        const scaleY = imageRect.height / naturalH;
        
        console.log('Rendering bounding boxes with scale:', { scaleX, scaleY });
        
        this.annotations.forEach(bbox => {
            const bboxElement = document.createElement('div');
            bboxElement.className = 'bbox-overlay';
            bboxElement.dataset.id = bbox.id;
            
            // Position and size the bounding box (convert from image coordinates to display coordinates)
            const displayX = bbox.x * scaleX;
            const displayY = bbox.y * scaleY;
            const displayWidth = bbox.width * scaleX;
            const displayHeight = bbox.height * scaleY;
            
            bboxElement.style.left = `${displayX}px`;
            bboxElement.style.top = `${displayY}px`;
            bboxElement.style.width = `${displayWidth}px`;
            bboxElement.style.height = `${displayHeight}px`;
            
            console.log(`Rendering bbox ${bbox.id}:`, {
                original: { x: bbox.x, y: bbox.y, width: bbox.width, height: bbox.height },
                display: { x: displayX, y: displayY, width: displayWidth, height: displayHeight }
            });
            
            // Add label
            const label = document.createElement('div');
            label.className = 'bbox-label';
            label.textContent = bbox.class;
            bboxElement.appendChild(label);
            
            // Add resize handles
            const handles = ['nw', 'ne', 'sw', 'se'];
            handles.forEach(h => {
                const handle = document.createElement('div');
                handle.className = `resize-handle handle-${h}`;
                handle.addEventListener('mousedown', (e) => {
                    // Begin resize immediately on handle press
                    e.stopPropagation();
                    this.selectBoundingBox(bbox.id);
                    this.isResizing = true;
                    this.resizeHandle = `handle-${h}`;
                    const ann = this.annotations.find(a => a.id === bbox.id);
                    if (ann) {
                        this.resizeStart = { x: ann.x, y: ann.y, w: ann.width, h: ann.height };
                    }
                });
                bboxElement.appendChild(handle);
            });

            // Hover state updates: set flag to indicate editing intent
            bboxElement.addEventListener('mouseenter', () => {
                this.isHoveringBox = true;
                this.hoveredBoxId = bbox.id;
            });
            bboxElement.addEventListener('mouseleave', () => {
                this.isHoveringBox = false;
                this.hoveredBoxId = null;
            });

            // Mouse down selects and prepares for move in pointer handlers
            bboxElement.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.selectBoundingBox(bbox.id);
                const img = document.getElementById('annotationImage');
                if (img) {
                    const rect = img.getBoundingClientRect();
                    this.isMoving = true;
                    this.moveTargetId = bbox.id;
                    this.moveStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
                }
            });
            
            overlay.appendChild(bboxElement);
        });
    }

    onHoverMove(event) {
        this.updateHoverFlag(event);
    }

    updateHoverFlag(event) {
        const targetEl = event.target;
        const bboxEl = targetEl && targetEl.closest ? targetEl.closest('.bbox-overlay') : null;
        if (bboxEl) {
            this.isHoveringBox = true;
            this.hoveredBoxId = bboxEl.dataset.id;
        } else {
            this.isHoveringBox = false;
            this.hoveredBoxId = null;
        }
    }
    
    selectBoundingBox(bboxId) {
        // Remove previous selection
        document.querySelectorAll('.bbox-overlay').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Add selection to clicked box
        const selectedElement = document.querySelector(`[data-id="${bboxId}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }
        
        this.selectedAnnotation = this.annotations.find(a => a.id === bboxId);
    }
    
    deleteSelected() {
        if (this.selectedAnnotation) {
            this.annotations = this.annotations.filter(a => a.id !== this.selectedAnnotation.id);
            this.selectedAnnotation = null;
            this.isDirty = true;
            this.updateAnnotationsList();
            this.updateAnnotationCount();
            this.renderBoundingBoxes();
            
            if (this.autoSave) {
                this.saveAnnotations();
            }
        }
    }
    
    nextFrameAfterAnnotation() {
        // Move to next frame after creating an annotation
        setTimeout(() => this.nextFrame(), 300);
    }
    
    toggleBoundingBoxMode() {
        const bboxTool = document.getElementById('bboxTool');
        if (bboxTool) {
			bboxTool.classList.toggle('active');
			this.bboxModeEnabled = bboxTool.classList.contains('active');
        }
    }
    
    cancelCurrentAction() {
        // Clear selection
        document.querySelectorAll('.bbox-overlay').forEach(el => {
            el.classList.remove('selected');
        });
        this.selectedAnnotation = null;
    }
    
    async loadCurrentFrameAnnotations() {
        try {
            const response = await fetch(`/api/annotations/${this.projectId}/${this.currentFrame}`);
            const data = await response.json();
            
            this.annotations = data.annotations || [];
            this.updateAnnotationsList();
            this.updateAnnotationCount();
            // Defer render until image is ready to get correct natural sizes
            if (this.imageReady) {
                this.renderBoundingBoxes();
            } else {
                // Poll once shortly after for slower image load
                setTimeout(() => this.renderBoundingBoxes(), 30);
            }
        } catch (error) {
            console.error('Failed to load annotations:', error);
            this.showNotification('Failed to load annotations', 'error');
        }
    }
    
    async saveAnnotations() {
        if (!this.isDirty) return;
        
        try {
            const response = await fetch(`/api/annotations/${this.projectId}/${this.currentFrame}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    annotations: this.annotations
                })
            });
            
            if (response.ok) {
                this.isDirty = false;
                this.updateSaveStatus('All changes saved');
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Failed to save annotations:', error);
            this.showNotification('Failed to save annotations', 'error');
        }
    }
    
    updateAnnotationsList() {
        const annotationsList = document.getElementById('annotationsList');
        
        if (!annotationsList) return;
        
        if (this.annotations.length === 0) {
            annotationsList.innerHTML = '<div class="text-muted">No annotations yet</div>';
            return;
        }
        
        annotationsList.innerHTML = this.annotations.map((annotation, index) => `
            <div class="annotation-item ${annotation.selected ? 'selected' : ''}" 
                 onclick="window.workspace.selectBoundingBox('${annotation.id}')">
                <div class="annotation-info">
                    <div class="annotation-label">${annotation.class}</div>
                    <div class="annotation-meta">
                        ${Math.round(annotation.width)} × ${Math.round(annotation.height)}px
                    </div>
                </div>
                <button class="delete-annotation" onclick="window.workspace.deleteAnnotation('${annotation.id}'); event.stopPropagation();">
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </div>
        `).join('');
    }
    
    deleteAnnotation(annotationId) {
        this.annotations = this.annotations.filter(a => a.id !== annotationId);
        this.isDirty = true;
        this.updateAnnotationsList();
        this.updateAnnotationCount();
        this.renderBoundingBoxes();
        
        if (this.autoSave) {
            this.saveAnnotations();
        }
    }
    
    updateAnnotationCount() {
        const countElement = document.getElementById('annotationCount');
        if (countElement) {
            countElement.textContent = this.annotations.length;
        }
    }
    
    updateFrameNavigation() {
        const prevBtn = document.getElementById('prevFrame');
        const nextBtn = document.getElementById('nextFrame');
        const frameSlider = document.getElementById('frameSlider');
        const currentFrameDisplay = document.getElementById('currentFrame');
        
        if (prevBtn) prevBtn.disabled = this.currentFrame <= 0;
        if (nextBtn) nextBtn.disabled = this.currentFrame >= this.totalFrames - 1;
        if (frameSlider) frameSlider.value = this.currentFrame;
        if (currentFrameDisplay) currentFrameDisplay.textContent = this.currentFrame + 1;
    }
    
    previousFrame() {
        if (this.currentFrame > 0) {
            this.navigateToFrame(this.currentFrame - 1);
        }
    }
    
    nextFrame() {
        if (this.currentFrame < this.totalFrames - 1) {
            this.navigateToFrame(this.currentFrame + 1);
        }
    }
    
    goToFrame(frameIndex) {
        const frame = parseInt(frameIndex);
        if (frame >= 0 && frame < this.totalFrames) {
            this.navigateToFrame(frame);
        }
    }
    
    async navigateToFrame(frameIndex) {
        if (this.isDirty && this.autoSave) {
            await this.saveAnnotations();
        }
        
        this.currentFrame = frameIndex;
        
        const image = document.getElementById('annotationImage');
        const loadingContainer = document.getElementById('loadingContainer');
        
        if (image) {
            if (loadingContainer) {
                loadingContainer.style.display = 'flex';
            }
            image.style.display = 'none';
            
            image.onload = () => {
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                image.style.display = 'block';
                this.imageReady = true;
                this.setupBoundingBoxTool();
                this.renderBoundingBoxes();
            };
            
            image.onerror = () => {
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                this.imageReady = false;
                this.showNotification('Failed to load frame', 'error');
            };
            
            image.src = `/api/frame/${this.projectId}/${frameIndex}`;
        }
        
        await this.loadCurrentFrameAnnotations();
        this.updateFrameNavigation();
        
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('frame', frameIndex);
        window.history.replaceState({}, '', newUrl);
    }
    
    updateSaveStatus(message) {
        console.log(message);
    }
    
    showClickIndicator(clickX, clickY) {
        // Create a temporary visual indicator at click position
        const indicator = document.createElement('div');
        indicator.style.position = 'absolute';
        indicator.style.left = `${clickX}px`;
        indicator.style.top = `${clickY}px`;
        indicator.style.width = '8px';
        indicator.style.height = '8px';
        indicator.style.backgroundColor = '#ff4444';
        indicator.style.borderRadius = '50%';
        indicator.style.border = '2px solid white';
        indicator.style.pointerEvents = 'none';
        indicator.style.zIndex = '1000';
        indicator.style.transform = 'translate(-50%, -50%)';
        
        // Add to the image overlay for consistent positioning
        const overlay = document.getElementById('imageOverlay');
        if (overlay) {
            overlay.appendChild(indicator);
            
            // Remove indicator after animation
            setTimeout(() => {
                indicator.style.transition = 'opacity 0.3s ease';
                indicator.style.opacity = '0';
                setTimeout(() => indicator.remove(), 300);
            }, 200);
        }
    }
    
    showNotification(message, type = 'info') {
        console.log(`${type}: ${message}`);
        
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}-circle me-2"></i>
                ${message}
            </div>
        `;
        
        // Add to container
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Show and auto-remove
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialization is handled from the template to avoid double-instantiation