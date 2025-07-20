// Upload Wizard Functionality
class UploadWizard {
    constructor() {
        this.currentStep = 1;
        this.selectedFile = null;
        this.init();
    }
    
    init() {
        this.setupFileUpload();
        this.setupStepNavigation();
        this.setupFormValidation();
        this.setupProjectCreation();
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('videoFile');
        const fileInfo = document.getElementById('fileInfo');
        const changeFileBtn = document.getElementById('changeFile');
        
        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelection(files[0]);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelection(e.target.files[0]);
            }
        });
        
        // Change file button
        changeFileBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    handleFileSelection(file) {
        // Validate file type
        const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
        if (!allowedTypes.includes(file.type) && !this.isValidVideoFile(file.name)) {
            this.showError('Please select a valid video file (MP4, AVI, MOV, MKV, WebM)');
            return;
        }
        
        // Validate file size (500MB max)
        const maxSize = 500 * 1024 * 1024; // 500MB
        if (file.size > maxSize) {
            this.showError('File size must be less than 500MB');
            return;
        }
        
        this.selectedFile = file;
        this.displayFileInfo(file);
        this.enableNextStep(1);
        this.updateEstimates();
    }
    
    isValidVideoFile(filename) {
        const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'];
        return validExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }
    
    displayFileInfo(file) {
        const uploadArea = document.getElementById('uploadArea');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
        
        uploadArea.style.display = 'none';
        fileInfo.classList.remove('hidden');
    }
    
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    setupStepNavigation() {
        // Next buttons
        document.getElementById('nextStep1').addEventListener('click', () => {
            this.goToStep(2);
        });
        
        document.getElementById('nextStep2').addEventListener('click', () => {
            this.goToStep(3);
            this.updateSummary();
        });
        
        // Previous buttons
        document.getElementById('prevStep2').addEventListener('click', () => {
            this.goToStep(1);
        });
        
        document.getElementById('prevStep3').addEventListener('click', () => {
            this.goToStep(2);
        });
    }
    
    goToStep(step) {
        // Hide current step
        document.querySelector('.wizard-step.active').classList.remove('active');
        document.querySelector('.step.active').classList.remove('active');
        
        // Show new step
        document.getElementById(`step-${step}`).classList.add('active');
        document.querySelector(`[data-step="${step}"]`).classList.add('active');
        
        // Mark completed steps
        for (let i = 1; i < step; i++) {
            document.querySelector(`[data-step="${i}"]`).classList.add('completed');
        }
        
        this.currentStep = step;
    }
    
    setupFormValidation() {
        const projectNameInput = document.getElementById('projectName');
        const frameIntervalInput = document.getElementById('frameInterval');
        
        // Auto-generate project name from file
        projectNameInput.addEventListener('blur', () => {
            if (!projectNameInput.value && this.selectedFile) {
                const baseName = this.selectedFile.name.replace(/\.[^/.]+$/, "");
                projectNameInput.value = baseName;
                this.updateEstimates();
            }
        });
        
        // Update estimates when interval changes
        frameIntervalInput.addEventListener('input', () => {
            this.updateEstimates();
        });
        
        // Auto-fill project name when file is selected
        this.originalHandleFileSelection = this.handleFileSelection;
        this.handleFileSelection = (file) => {
            this.originalHandleFileSelection(file);
            if (!projectNameInput.value) {
                const baseName = file.name.replace(/\.[^/.]+$/, "");
                projectNameInput.value = baseName;
            }
        };
    }
    
    updateEstimates() {
        if (!this.selectedFile) return;
        
        const frameInterval = parseFloat(document.getElementById('frameInterval').value) || 1.0;
        
        // Estimate video duration (rough calculation)
        // We'll use file size as a proxy since we can't get actual duration without loading the video
        const estimatedDuration = Math.max(10, this.selectedFile.size / (1024 * 1024) * 2); // Very rough estimate
        const estimatedFrames = Math.floor(estimatedDuration / frameInterval);
        const estimatedStorage = estimatedFrames * 0.1; // Estimate 100KB per frame
        
        document.getElementById('estimatedFrames').textContent = estimatedFrames.toLocaleString();
        document.getElementById('estimatedStorage').textContent = this.formatFileSize(estimatedStorage * 1024 * 1024);
    }
    
    updateSummary() {
        const projectName = document.getElementById('projectName').value || 'Untitled Project';
        const frameInterval = document.getElementById('frameInterval').value;
        const estimatedFrames = document.getElementById('estimatedFrames').textContent;
        
        document.getElementById('summaryFileName').textContent = this.selectedFile.name;
        document.getElementById('summaryProjectName').textContent = projectName;
        document.getElementById('summaryInterval').textContent = `${frameInterval} seconds`;
        document.getElementById('summaryFrames').textContent = estimatedFrames;
    }
    
    setupProjectCreation() {
        document.getElementById('createProject').addEventListener('click', () => {
            this.createProject();
        });
    }
    
    async createProject() {
        const projectName = document.getElementById('projectName').value || 'Untitled Project';
        const frameInterval = parseFloat(document.getElementById('frameInterval').value) || 1.0;
        
        if (!this.selectedFile) {
            this.showError('Please select a video file');
            return;
        }
        
        // Show processing state
        document.getElementById('createProject').style.display = 'none';
        document.getElementById('prevStep3').style.display = 'none';
        document.getElementById('processingStatus').classList.remove('hidden');
        
        try {
            const formData = new FormData();
            formData.append('video', this.selectedFile);
            formData.append('project_name', projectName);
            formData.append('frame_interval', frameInterval);
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSuccess(result);
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showError(error.message || 'Failed to create project. Please try again.');
            this.resetCreateButton();
        }
    }
    
    showSuccess(result) {
        document.getElementById('processingStatus').classList.add('hidden');
        document.getElementById('successState').classList.remove('hidden');
        
        // Show annotation link
        const startBtn = document.getElementById('startAnnotating');
        startBtn.href = `/annotate/${result.project_id}`;
        startBtn.classList.remove('hidden');
        
        // Update step indicator
        document.querySelector('[data-step="3"]').classList.add('completed');
        
        if (window.VisionLabel) {
            window.VisionLabel.showNotification('Project created successfully!', 'success');
        }
    }
    
    showError(message) {
        if (window.VisionLabel) {
            window.VisionLabel.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }
    
    resetCreateButton() {
        document.getElementById('createProject').style.display = 'inline-flex';
        document.getElementById('prevStep3').style.display = 'inline-flex';
        document.getElementById('processingStatus').classList.add('hidden');
    }
    
    enableNextStep(step) {
        const nextBtn = document.getElementById(`nextStep${step}`);
        if (nextBtn) {
            nextBtn.disabled = false;
        }
    }
}

// Export for global use
window.UploadWizard = UploadWizard; 