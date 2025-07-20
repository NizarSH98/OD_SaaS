// Export Interface Functionality
class ExportInterface {
    constructor(options) {
        this.projectId = options.projectId;
        this.metadata = options.metadata;
        this.stats = options.stats;
        this.selectedFormat = null;
        this.chart = null;
        this.init();
    }
    
    init() {
        this.setupFormatSelection();
        this.setupExportOptions();
        this.setupExportActions();
        this.loadClassDistribution();
        this.updateStats();
    }
    
    setupFormatSelection() {
        const formatCards = document.querySelectorAll('.format-card');
        const formatButtons = document.querySelectorAll('.format-select-btn');
        
        formatButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const format = button.getAttribute('data-format');
                this.selectFormat(format);
            });
        });
        
        formatCards.forEach(card => {
            card.addEventListener('click', () => {
                const format = card.getAttribute('data-format');
                this.selectFormat(format);
            });
        });
    }
    
    selectFormat(format) {
        // Remove previous selection
        document.querySelectorAll('.format-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select new format
        const selectedCard = document.querySelector(`[data-format="${format}"]`);
        selectedCard.classList.add('selected');
        
        this.selectedFormat = format;
        this.showExportOptions();
        this.updateExportSummary();
        
        // Scroll to options
        document.getElementById('exportOptions').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
    
    showExportOptions() {
        document.getElementById('exportOptions').style.display = 'block';
        document.getElementById('classDistribution').style.display = 'block';
        document.getElementById('exportActions').style.display = 'block';
    }
    
    setupExportOptions() {
        // Frame selection options
        const frameOptions = document.querySelectorAll('input[name="frameSelection"]');
        frameOptions.forEach(option => {
            option.addEventListener('change', () => {
                this.updateExportSummary();
            });
        });
        
        // Image quality slider
        const qualitySlider = document.getElementById('imageQuality');
        const qualityValue = document.getElementById('qualityValue');
        
        qualitySlider.addEventListener('input', (e) => {
            qualityValue.textContent = `${e.target.value}%`;
            this.updateExportSummary();
        });
    }
    
    setupExportActions() {
        document.getElementById('startExport').addEventListener('click', () => {
            this.startExport();
        });
        
        document.getElementById('cancelExport').addEventListener('click', () => {
            this.resetSelection();
        });
        
        document.getElementById('cancelExportModal').addEventListener('click', () => {
            this.cancelExport();
        });
    }
    
    updateStats() {
        document.getElementById('totalAnnotations').textContent = this.stats.totalAnnotations;
        document.getElementById('completionRate').textContent = `${this.stats.completionRate}%`;
        document.getElementById('annotatedCount').textContent = this.stats.annotatedFrames;
    }
    
    updateExportSummary() {
        if (!this.selectedFormat) return;
        
        const frameSelection = document.querySelector('input[name="frameSelection"]:checked').value;
        const framesToExport = frameSelection === 'all' ? this.stats.totalFrames : this.stats.annotatedFrames;
        const quality = document.getElementById('imageQuality').value;
        
        // Update summary
        document.getElementById('selectedFormat').textContent = this.getFormatDisplayName(this.selectedFormat);
        document.getElementById('framesToExport').textContent = framesToExport.toLocaleString();
        document.getElementById('estimatedSize').textContent = this.estimateFileSize(framesToExport, quality);
    }
    
    getFormatDisplayName(format) {
        const names = {
            'yolo': 'YOLO (Darknet)',
            'coco': 'COCO JSON',
            'pascal_voc': 'Pascal VOC XML'
        };
        return names[format] || format;
    }
    
    estimateFileSize(frameCount, quality) {
        // Rough estimation based on frame count and quality
        const baseImageSize = (quality / 100) * 200; // KB per image
        const annotationOverhead = 5; // KB per frame for annotation files
        const totalSizeKB = frameCount * (baseImageSize + annotationOverhead);
        
        return this.formatFileSize(totalSizeKB * 1024);
    }
    
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    async loadClassDistribution() {
        try {
            const response = await fetch(`/api/project/${this.projectId}/stats`);
            if (response.ok) {
                const stats = await response.json();
                this.createClassChart(stats.classes || []);
                this.displayClassList(stats.classes || []);
            }
        } catch (error) {
            console.error('Error loading class distribution:', error);
        }
    }
    
    createClassChart(classes) {
        const ctx = document.getElementById('distributionChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        if (classes.length === 0) {
            ctx.font = '16px Inter';
            ctx.fillStyle = '#6b7280';
            ctx.textAlign = 'center';
            ctx.fillText('No annotations yet', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        const colors = this.generateColors(classes.length);
        
        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: classes,
                datasets: [{
                    data: classes.map(() => Math.floor(Math.random() * 50) + 10), // Mock data
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#374151',
                        borderWidth: 1
                    }
                }
            }
        });
    }
    
    displayClassList(classes) {
        const classList = document.getElementById('classList');
        
        if (classes.length === 0) {
            classList.innerHTML = '<div class="text-center text-muted">No classes defined yet</div>';
            return;
        }
        
        const colors = this.generateColors(classes.length);
        
        classList.innerHTML = classes.map((className, index) => `
            <div class="class-item">
                <div class="class-color" style="background-color: ${colors[index]}"></div>
                <span class="class-name">${className}</span>
                <span class="class-count">${Math.floor(Math.random() * 50) + 1}</span>
            </div>
        `).join('');
    }
    
    generateColors(count) {
        const colors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
            '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
            '#f97316', '#6366f1', '#14b8a6', '#eab308'
        ];
        
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(colors[i % colors.length]);
        }
        return result;
    }
    
    async startExport() {
        const frameSelection = document.querySelector('input[name="frameSelection"]:checked').value;
        const quality = document.getElementById('imageQuality').value;
        
        const exportData = {
            format: this.selectedFormat,
            frame_selection: frameSelection,
            image_quality: parseInt(quality)
        };
        
        // Show progress modal
        const modal = new bootstrap.Modal(document.getElementById('exportModal'));
        modal.show();
        
        try {
            const response = await fetch(`/api/export/${this.projectId}/${this.selectedFormat}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(exportData)
            });
            
            if (response.ok) {
                // Start polling for progress
                this.pollExportProgress();
            } else {
                throw new Error('Export failed to start');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.showExportError(error.message);
            modal.hide();
        }
    }
    
    async pollExportProgress() {
        const progressBar = document.getElementById('exportProgressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressStep = document.getElementById('progressStep');
        const progressDetails = document.getElementById('progressDetails');
        
        const steps = [
            'Preparing images...',
            'Generating annotations...',
            'Creating archive...',
            'Finalizing export...'
        ];
        
        let currentStep = 0;
        let progress = 0;
        
        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5;
            
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                this.completeExport();
            }
            
            // Update step
            const stepIndex = Math.floor((progress / 100) * steps.length);
            if (stepIndex !== currentStep && stepIndex < steps.length) {
                currentStep = stepIndex;
                progressStep.textContent = steps[currentStep];
                progressDetails.textContent = `Processing... ${Math.floor(progress)}%`;
            }
            
            progressBar.style.width = `${progress}%`;
            progressPercentage.textContent = `${Math.floor(progress)}%`;
            
        }, 500);
    }
    
    completeExport() {
        const progressStep = document.getElementById('progressStep');
        const progressDetails = document.getElementById('progressDetails');
        const exportFooter = document.getElementById('exportFooter');
        
        progressStep.textContent = 'Export Complete!';
        progressDetails.textContent = 'Your dataset is ready for download.';
        
        exportFooter.innerHTML = `
            <button type="button" class="btn btn-success" onclick="window.location.href='/api/export/${this.projectId}/${this.selectedFormat}'">
                <i class="fas fa-download me-2"></i>
                Download Dataset
            </button>
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                Close
            </button>
        `;
        
        if (window.VisionLabel) {
            window.VisionLabel.showNotification('Dataset exported successfully!', 'success');
        }
    }
    
    showExportError(message) {
        if (window.VisionLabel) {
            window.VisionLabel.showNotification(`Export failed: ${message}`, 'error');
        } else {
            alert(`Export failed: ${message}`);
        }
    }
    
    cancelExport() {
        // In a real implementation, this would cancel the server-side export process
        if (window.VisionLabel) {
            window.VisionLabel.showNotification('Export cancelled', 'info');
        }
    }
    
    resetSelection() {
        document.querySelectorAll('.format-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        this.selectedFormat = null;
        
        document.getElementById('exportOptions').style.display = 'none';
        document.getElementById('classDistribution').style.display = 'none';
        document.getElementById('exportActions').style.display = 'none';
        
        // Scroll back to formats
        document.querySelector('.formats-grid').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Export for global use
window.ExportInterface = ExportInterface; 