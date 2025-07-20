// Enhanced annotation workspace functionality
class AnnotationWorkspace {
    constructor() {
        // Get values from data attributes instead of Jinja2 template syntax
        const container = document.querySelector('.annotation-workspace');
        this.projectId = container.dataset.projectId;
        this.currentFrame = parseInt(container.dataset.currentFrame) || 0;
        this.totalFrames = parseInt(container.dataset.totalFrames) || 0;
        this.annotations = [];
        this.selectedAnnotation = null;
        this.autoSave = true;
        this.isDirty = false;
        
        this.init();
    }
    
    init() {
        this.setupKeyboardShortcuts();
        this.setupProgressIndicator();
        this.setupAnnotationSystem();
        this.loadCurrentFrameAnnotations();
        this.updateFrameNavigation();
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input fields
            if (e.target.matches('input, textarea, select')) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                case 'a':
                case 'A':
                    e.preventDefault();
                    this.previousFrame();
                    break;
                case 'ArrowRight':
                case 'd':
                case 'D':
                    e.preventDefault();
                    this.nextFrame();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToFrame(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToFrame(this.totalFrames - 1);
                    break;
                case ' ':
                    e.preventDefault();
                    this.toggleAnnotationMode();
                    break;
                case 'Delete':
                case 'Backspace':
                    e.preventDefault();
                    this.deleteSelected();
                    break;
                case 'n':
                case 'N':
                    e.preventDefault();
                    this.noObject();
                    break;
                case 'c':
                case 'C':
                    e.preventDefault();
                    this.clearAll();
                    break;
                case '?':
                    e.preventDefault();
                    this.showShortcuts();
                    break;
                case 'Escape':
                    this.cancelCurrentAction();
                    break;
            }
            
            // Ctrl+key combinations
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 's':
                    case 'S':
                        e.preventDefault();
                        this.saveAnnotations();
                        break;
                    case 'z':
                    case 'Z':
                        e.preventDefault();
                        this.undo();
                        break;
                }
            }
        });
    }
    
    setupProgressIndicator() {
        this.updateProgress();
    }
    
    updateProgress() {
        const progressPercent = (this.currentFrame / (this.totalFrames - 1)) * 100;
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill && progressText) {
            progressFill.style.width = progressPercent + '%';
            progressText.textContent = Math.round(progressPercent) + '%';
        }
    }
    
    setupAnnotationSystem() {
        // Initialize Annotorious or custom annotation system
        this.initializeAnnotorious();
    }
    
    initializeAnnotorious() {
        const image = document.getElementById('annotationImage');
        if (!image) return;
        
        this.annotorious = Annotorious.init({
            image: image,
            widgets: [
                'COMMENT',
                { widget: 'TAG', vocabulary: ['person', 'ball', 'player', 'court'] }
            ]
        });
        
        this.annotorious.on('createAnnotation', (annotation) => {
            this.onAnnotationCreated(annotation);
        });
        
        this.annotorious.on('updateAnnotation', (annotation, previous) => {
            this.onAnnotationUpdated(annotation, previous);
        });
        
        this.annotorious.on('deleteAnnotation', (annotation) => {
            this.onAnnotationDeleted(annotation);
        });
        
        this.annotorious.on('selectAnnotation', (annotation) => {
            this.onAnnotationSelected(annotation);
        });
    }
    
    async loadCurrentFrameAnnotations() {
        try {
            const response = await fetch(`/api/annotations/${this.projectId}/${this.currentFrame}`);
            const data = await response.json();
            
            this.annotations = data.annotations || [];
            this.updateAnnotationsList();
            this.updateAnnotationCount();
            
            // Load annotations into Annotorious
            if (this.annotorious) {
                this.annotorious.setAnnotations(this.annotations);
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
        const emptyAnnotations = document.getElementById('emptyAnnotations');
        
        if (!annotationsList) return;
        
        if (this.annotations.length === 0) {
            annotationsList.innerHTML = '';
            if (emptyAnnotations) emptyAnnotations.style.display = 'block';
            return;
        }
        
        if (emptyAnnotations) emptyAnnotations.style.display = 'none';
        
        annotationsList.innerHTML = this.annotations.map((annotation, index) => `
            <div class="annotation-item ${annotation.selected ? 'selected' : ''}" 
                 onclick="workspace.selectAnnotation(${index})">
                <div class="annotation-info">
                    <div class="annotation-label">${annotation.class || 'object'}</div>
                    <div class="annotation-meta">
                        ${Math.round(annotation.width || 0)} × ${Math.round(annotation.height || 0)}px
                    </div>
                </div>
                <button class="delete-annotation" onclick="workspace.deleteAnnotation(${index}); event.stopPropagation();">
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </div>
        `).join('');
    }
    
    updateAnnotationCount() {
        const countElement = document.getElementById('annotationCount');
        if (countElement) {
            countElement.textContent = this.annotations.length;
        }
    }
    
    updateFrameNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const frameInput = document.getElementById('frameInput');
        
        if (prevBtn) prevBtn.disabled = this.currentFrame <= 0;
        if (nextBtn) nextBtn.disabled = this.currentFrame >= this.totalFrames - 1;
        if (frameInput) frameInput.value = this.currentFrame;
        
        this.updateProgress();
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
        // Save current frame if dirty
        if (this.isDirty && this.autoSave) {
            await this.saveAnnotations();
        }
        
        this.currentFrame = frameIndex;
        
        // Update image source
        const image = document.getElementById('annotationImage');
        if (image) {
            image.src = `/api/frame/${this.projectId}/${frameIndex}`;
        }
        
        // Load annotations for new frame
        await this.loadCurrentFrameAnnotations();
        
        // Update navigation
        this.updateFrameNavigation();
        
        // Update URL without reload
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('frame', frameIndex);
        window.history.replaceState({}, '', newUrl);
    }
    
    onAnnotationCreated(annotation) {
        const labelInput = document.getElementById('labelInput');
        if (labelInput) {
            annotation.class = labelInput.value || 'object';
        }
        
        this.annotations.push(annotation);
        this.isDirty = true;
        this.updateAnnotationsList();
        this.updateAnnotationCount();
        
        if (this.autoSave) {
            this.saveAnnotations();
        }
        
        // If single object mode, move to next frame
        const singleObjectMode = document.getElementById('singleObjectMode');
        if (singleObjectMode && singleObjectMode.checked) {
            setTimeout(() => this.nextFrame(), 500);
        }
    }
    
    onAnnotationUpdated(annotation, previous) {
        const index = this.annotations.findIndex(a => a.id === annotation.id);
        if (index !== -1) {
            this.annotations[index] = annotation;
            this.isDirty = true;
            this.updateAnnotationsList();
            
            if (this.autoSave) {
                this.saveAnnotations();
            }
        }
    }
    
    onAnnotationDeleted(annotation) {
        this.annotations = this.annotations.filter(a => a.id !== annotation.id);
        this.isDirty = true;
        this.updateAnnotationsList();
        this.updateAnnotationCount();
        
        if (this.autoSave) {
            this.saveAnnotations();
        }
    }
    
    onAnnotationSelected(annotation) {
        this.selectedAnnotation = annotation;
        this.annotations.forEach(a => a.selected = (a.id === annotation.id));
        this.updateAnnotationsList();
        
        // Enable delete button
        const deleteBtn = document.getElementById('deleteBtn');
        if (deleteBtn) deleteBtn.disabled = false;
    }
    
    selectAnnotation(index) {
        const annotation = this.annotations[index];
        if (this.annotorious && annotation) {
            this.annotorious.selectAnnotation(annotation.id);
        }
    }
    
    deleteAnnotation(index) {
        const annotation = this.annotations[index];
        if (this.annotorious && annotation) {
            this.annotorious.removeAnnotation(annotation);
        }
    }
    
    deleteSelected() {
        if (this.selectedAnnotation && this.annotorious) {
            this.annotorious.removeAnnotation(this.selectedAnnotation);
        }
    }
    
    clearAll() {
        if (this.annotorious) {
            this.annotorious.clearAnnotations();
        }
        this.annotations = [];
        this.isDirty = true;
        this.updateAnnotationsList();
        this.updateAnnotationCount();
        
        if (this.autoSave) {
            this.saveAnnotations();
        }
    }
    
    noObject() {
        // Mark frame as having no objects and move to next
        this.clearAll();
        setTimeout(() => this.nextFrame(), 200);
    }
    
    toggleAnnotationMode() {
        // Toggle between selection and drawing mode
        // Implementation depends on annotation library
    }
    
    undo() {
        // Implement undo functionality
        this.showNotification('Undo functionality coming soon', 'info');
    }
    
    cancelCurrentAction() {
        // Cancel current drawing or selection
        if (this.annotorious) {
            this.annotorious.cancelSelected();
        }
    }
    
    showShortcuts() {
        const modal = document.getElementById('shortcutsModal');
        if (modal) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        }
    }
    
    updateSaveStatus(message) {
        const statusElement = document.getElementById('saveStatus');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    showNotification(message, type = 'info') {
        if (window.VisionLabel) {
            window.VisionLabel.showNotification(message, type);
        } else {
            console.log(`${type}: ${message}`);
        }
    }
}

// Global functions for backward compatibility
let workspace;

function previousFrame() {
    if (workspace) workspace.previousFrame();
}

function nextFrame() {
    if (workspace) workspace.nextFrame();
}

function goToFrame(frameIndex) {
    if (workspace) workspace.goToFrame(frameIndex);
}

function deleteSelected() {
    if (workspace) workspace.deleteSelected();
}

function clearAll() {
    if (workspace) workspace.clearAll();
}

function noObject() {
    if (workspace) workspace.noObject();
}

function setLabel(label) {
    const labelInput = document.getElementById('labelInput');
    if (labelInput) {
        labelInput.value = label;
    }
}

// Initialize workspace when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    workspace = new AnnotationWorkspace();
}); 